# check_db.py

import chromadb
from chromadb.config import Settings
from config import CHROMA_DB_DIR  # 确保你的 config.py 中有 CHROMA_DB_DIR


def check_papers_collection():
    """
    直接连接到数据库，检查 'papers' 集合中的文档数量。
    """
    print(f"正在连接到数据库，路径: {CHROMA_DB_DIR}")

    # 使用与 VectorDB 类相同的方式初始化客户端
    client = chromadb.Client(Settings(
        persist_directory=CHROMA_DB_DIR,
        anonymized_telemetry=False
    ))

    # 获取 'papers' 集合
    collection = client.get_or_create_collection(name="papers")

    # 查询集合中的文档总数
    count = collection.count()

    print(f"\n--- 数据库诊断结果 ---")
    print(f"'papers' 集合中的文档总数: {count}")

    if count > 0:
        print("✅ 数据已成功写入数据库！")
    else:
        print("❌ 数据库中没有任何文档！索引过程失败了！")


if __name__ == "__main__":
    check_papers_collection()