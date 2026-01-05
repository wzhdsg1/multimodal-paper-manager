# main.py

import argparse
import os
from pathlib import Path
from typing import Optional, Tuple

# 导入核心模块
from core.pdf_processor import extract_text_with_pages, extract_title_and_abstract
from core.embedding import TextEmbedding, ImageEmbedding
from core.vector_db import VectorDB
from core.classifier import PaperClassifier
from utils.file_operate import move_to_topic_folder
from config import PAPERS_DIR, IMAGES_DIR

# --- 全局模型初始化 ---
# 为了避免每次运行命令都重新加载模型，我们在程序启动时就初始化它们
print("正在初始化模型...")
try:
    text_embedder = TextEmbedding()
    image_embedder = ImageEmbedding()
    classifier = PaperClassifier()
    vdb = VectorDB()
    print("所有模型初始化完成！\n")
except Exception as e:
    print(f"模型初始化失败: {e}")
    exit()


# --- 核心功能函数 ---

def process_and_index_paper(pdf_path: str):
    """
    通用函数：处理单个PDF，包括提取文本、生成嵌入、存入数据库。
    """
    print(f"正在为 '{os.path.basename(pdf_path)}' 提取文本...")
    text_with_pages = extract_text_with_pages(pdf_path)

    if not text_with_pages:
        print(f"未提取到有效文本，跳过索引: {pdf_path}")
        return

    # 使用列表推导式安全地解包数据
    texts = [item[0] for item in text_with_pages]
    page_nums = [item[1] for item in text_with_pages]

    print(f"成功提取 {len(texts)} 个文本片段。")

    print("正在生成文本嵌入...")
    embeddings = text_embedder.embed(texts)

    if len(embeddings) != len(texts):
        print(f"错误：生成的嵌入数量 ({len(embeddings)}) 与文本片段数量 ({len(texts)}) 不匹配！")
        return

    print("正在将数据存入数据库...")
    vdb.add_paper_fragments(texts, embeddings, page_nums, pdf_path)
    print(f"成功索引 {len(texts)} 个片段。")


def add_paper(args):
    """添加单个论文，自动分类并索引。"""
    pdf_path = args.path

    if not os.path.exists(pdf_path):
        print(f"错误：文件 '{pdf_path}' 不存在。")
        return

    print(f"\n开始处理文件: {os.path.basename(pdf_path)}")

    # 1. 提取标题和摘要用于分类
    title, abstract = extract_title_and_abstract(pdf_path)
    if not title:
        title = os.path.basename(pdf_path)
    text_to_classify = f"Title: {title}\nAbstract: {abstract}"

    # 2. 自动分类
    topic = classifier.classify(text_to_classify)

    # 3. 自动移动文件到相应主题文件夹
    final_paper_path = move_to_topic_folder(pdf_path, topic)

    # 4. 处理并索引论文
    process_and_index_paper(final_paper_path)

    # --- 关键：添加自检步骤 ---
    print("\n--- [Self-Check] Verifying data in the same process ---")
    # 等待一小段时间，给数据库一个喘息的机会
    import time
    time.sleep(2)

    # 直接在当前进程中查询数据库
    current_count = vdb.paper_collection.count()
    print(f"Current count of documents in 'papers' collection: {current_count}")

    if current_count > 0:
        print("✅ Self-check PASSED: Data is present in the database within the same process.")
    else:
        print("❌ Self-check FAILED: Data is NOT present in the database, even in the same process!")
    print("----------------------------------------------------\n")


def organize_papers(args):
    """批量整理一个文件夹内的所有PDF论文。"""
    source_dir = args.dir
    if not os.path.isdir(source_dir):
        print(f"错误：目录 '{source_dir}' 不存在或不是一个文件夹。")
        return

    print(f"\n开始整理目录: {source_dir}")
    pdf_files = list(Path(source_dir).glob("*.pdf"))

    if not pdf_files:
        print("在该目录下未找到任何PDF文件。")
        return

    print(f"找到 {len(pdf_files)} 个PDF文件，开始逐个处理...")
    for pdf_path in pdf_files:
        print("\n" + "=" * 40)
        # 使用 argparse.Namespace 来复用 add_paper 的逻辑
        add_paper(argparse.Namespace(path=str(pdf_path)))
    print("\n" + "=" * 40)
    print("批量整理完成！")


def search_paper_file(args):
    """语义搜索，返回相关的论文文件列表。"""
    query = args.query
    print(f"\n--- 正在搜索与 '{query}' 相关的论文文件 (Top {args.top_k}) ---")

    query_embedding = text_embedder.embed([query])[0]
    results = vdb.search_paper_files(query_embedding, top_k=args.top_k)

    if not results:
        print("未找到相关的论文文件。")
        return

    # --- 新增：低置信度提示逻辑 ---
    # 定义一个平均相似度的阈值，例如 0.5
    CONFIDENCE_THRESHOLD = 0.5
    highest_score = results[0]['average_similarity_score']
    show_warning = highest_score < CONFIDENCE_THRESHOLD

    for i, res in enumerate(results, 1):
        print(f"\n结果 {i} (平均相似度: {res['average_similarity_score']:.4f})")
        print(f"文件名: {res['filename']}")
        print(f"路径: {res['paper_path']}")

    if show_warning:
        print("\n 提示：返回结果的平均相似度较低。")
        print("   这可能意味着：")
        print("   1. 您的查询过于宽泛或模糊。")
        print("   2. 数据库中没有与您的查询高度相关的论文。")
        print("   建议尝试使用更具体的关键词或句子进行搜索。")


def search_paper(args):
    """语义搜索，返回相关的论文片段。"""
    query = args.query
    print(f"\n--- 正在搜索与 '{query}' 相关的论文片段 (Top {args.top_k}) ---")

    query_embedding = text_embedder.embed([query])[0]
    results = vdb.search_papers(query_embedding, top_k=args.top_k)

    if not results:
        print("未找到相关内容。")
        return

    # --- 新增：低置信度提示逻辑 ---
    # 定义一个相似度的阈值，例如 0.4
    CONFIDENCE_THRESHOLD = 0.4
    min_score = min(res['similarity_score'] for res in results)
    show_warning = min_score < CONFIDENCE_THRESHOLD

    for i, res in enumerate(results, 1):
        print(f"\n结果 {i} (相似度: {res['similarity_score']:.4f})")
        print(f"来源: {os.path.basename(res['paper_path'])} (页码: {res['page']})")
        print(f"片段: {res['fragment']}")

    if show_warning:
        print("\n提示：部分或全部返回结果的相似度较低。")
        print("   这可能意味着：")
        print("   1. 您的查询过于宽泛或模糊。")
        print("   2. 数据库中没有与您的查询高度相关的文本片段。")
        print("   建议尝试使用更具体的关键词或句子进行搜索。")


def add_image(args):
    """添加单个图片并索引。"""
    image_path = args.path
    if not os.path.exists(image_path):
        print(f"错误：文件 '{image_path}' 不存在。")
        return

    from PIL import Image
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"无法打开或处理图片: {e}")
        return

    print(f"\n正在为 '{os.path.basename(image_path)}' 生成嵌入...")
    embedding = image_embedder.embed([img])[0]

    import shutil
    dest_dir = IMAGES_DIR
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(image_path))
    shutil.copy2(image_path, dest_path)

    vdb.add_images([dest_path], [embedding])
    print(f"图片已复制到 '{dest_path}' 并成功索引。")


def search_image(args):
    """以文搜图，返回相关的图片。"""
    query = args.query
    print(f"\n--- 正在搜索与 '{query}' 描述相关的图片 (Top {args.top_k}) ---")

    query_embedding = image_embedder.embed_text(query)
    results = vdb.search_images(query_embedding, top_k=args.top_k)

    if not results:
        print("未找到相关图片。")
        return

    # --- 新增：低置信度提示逻辑 ---
    # 定义一个相似度的阈值，例如 0.3 (图片的相似度分数通常较低)
    CONFIDENCE_THRESHOLD = 0.3
    min_score = min(res['similarity_score'] for res in results)
    show_warning = min_score < CONFIDENCE_THRESHOLD

    for i, res in enumerate(results, 1):
        print(f"\n结果 {i} (相似度: {res['similarity_score']:.4f})")
        print(f"路径: {res['image_path']}")

    if show_warning:
        print("\n提示：部分或全部返回结果的相似度较低。")
        print("   这可能意味着：")
        print("   1. 您的描述过于抽象或不常见。")
        print("   2. 数据库中没有与您的描述高度相关的图片。")
        print("   建议尝试使用更具体、更常见的词语来描述图片。")


# --- 命令行参数解析 ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="本地多模态AI文献管理助手 (带自动分类和语义搜索)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="可用命令")

    # 添加单篇论文
    add_p = subparsers.add_parser("add_paper", help="添加、自动分类并索引单个论文")
    add_p.add_argument("path", help="PDF论文的路径")
    add_p.set_defaults(func=add_paper)

    # 批量整理论文
    org_p = subparsers.add_parser("organize_papers", help="批量整理一个文件夹内的所有PDF论文")
    org_p.add_argument("dir", help="包含PDF文件的源文件夹路径")
    org_p.set_defaults(func=organize_papers)

    # 搜索论文文件
    search_file_p = subparsers.add_parser("search_paper_file", help="语义搜索，返回相关的论文文件列表")
    search_file_p.add_argument("query", help="搜索关键词或句子")
    search_file_p.add_argument("--top_k", type=int, default=3, help="返回结果数量 (默认: 3)")
    search_file_p.set_defaults(func=search_paper_file)

    # 搜索论文片段
    search_p = subparsers.add_parser("search_paper", help="语义搜索，返回相关的论文片段和页码")
    search_p.add_argument("query", help="搜索关键词或句子")
    search_p.add_argument("--top_k", type=int, default=3, help="返回结果数量 (默认: 3)")
    search_p.set_defaults(func=search_paper)

    # 添加图片
    add_img = subparsers.add_parser("add_image", help="添加单个图片并索引")
    add_img.add_argument("path", help="图片文件的路径")
    add_img.set_defaults(func=add_image)

    # 以文搜图
    search_img = subparsers.add_parser("search_image", help="以文搜图，返回相关的图片")
    search_img.add_argument("query", help="描述图片的关键词或句子")
    search_img.add_argument("--top_k", type=int, default=3, help="返回结果数量 (默认: 3)")
    search_img.set_defaults(func=search_image)

    args = parser.parse_args()
    args.func(args)