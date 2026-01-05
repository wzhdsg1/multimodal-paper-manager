# app.py
import streamlit as st
import os
import argparse
import io
from contextlib import redirect_stdout
from pathlib import Path

# 导入所有核心功能函数
from main import (
    add_paper, organize_papers,
    search_paper_file, search_paper,
    add_image, search_image
)
from config import PAPERS_DIR, IMAGES_DIR  # 导入配置，确保路径正确

# 页面基础配置（优化样式）
st.set_page_config(
    page_title="本地多模态AI文献管理助手",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"  # 默认展开侧边栏
)

# 自定义样式（优化按钮、输入框外观）
st.markdown("""
    <style>
    /* 按钮样式优化 */
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
    }
    div.stButton > button:hover {
        background-color: #45a049;
    }
    /* 输入框/文本域样式 */
    input, textarea, div[data-testid="stNumberInput"] {
        border-radius: 4px;
    }
    /* 侧边栏标题样式 */
    .sidebar-header {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid #eee;
    }
    /* 主区域标题 */
    .main-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)


# 自定义：捕获print输出的函数
def capture_print_output(func, args):
    """执行函数并捕获所有print输出，返回输出文本"""
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            func(args)
        except Exception as e:
            st.error(f"执行出错：{str(e)}")
            return f"执行出错：{str(e)}\n"
    return f.getvalue()


# ========== 左侧侧边栏：功能导航 ==========
with st.sidebar:
    st.markdown('<div class="sidebar-header">📚 功能导航</div>', unsafe_allow_html=True)

    # 功能选择（单选）
    selected_func = st.radio(
        "选择要执行的操作",
        [
            "添加单篇论文",
            "批量整理论文",
            "搜索论文文件（整篇）",
            "搜索论文片段（精准）",
            "添加单张图片",
            "以文搜图"
        ],
        key="func_selector",
        index=0  # 默认选中第一个功能
    )

    # 侧边栏底部提示
    st.divider()
    st.caption("💡 所有数据均保存在本地\n路径参考 config.py 配置")

# ========== 主区域：根据选择显示对应功能 ==========
st.markdown(f'<div class="main-title">{selected_func}</div>', unsafe_allow_html=True)
st.divider()

# 1. 添加单篇论文
if selected_func == "添加单篇论文":
    col1, col2 = st.columns([3, 1])
    with col1:
        paper_file = st.file_uploader(
            "选择PDF论文文件（最大200MB）",
            type=["pdf"],
            key="paper_upload",
            help="支持拖拽或点击上传PDF文件"
        )
    with col2:
        st.write("")  # 占位对齐
        st.write("")
        submit_btn = st.button("添加并索引论文", use_container_width=True)

    # 执行逻辑
    if submit_btn:
        if paper_file:
            # 临时保存上传的文件
            temp_paper_path = os.path.join(PAPERS_DIR, paper_file.name)
            with open(temp_paper_path, "wb") as f:
                f.write(paper_file.getbuffer())

            with st.spinner("正在处理：分类 → 移动 → 生成嵌入 → 索引..."):
                args = argparse.Namespace(path=temp_paper_path)
                output = capture_print_output(add_paper, args)

                # 显示处理日志
                st.subheader("处理日志")
                st.text_area("", output, height=300, key="paper_log")
                st.success("✅ 论文添加并索引完成！")
        else:
            st.warning("⚠️ 请先选择要上传的PDF文件！")

# 2. 批量整理论文
elif selected_func == "批量整理论文":
    # 文件夹路径选择
    dir_path = st.text_input(
        "论文文件夹路径",
        placeholder="例如：D:\\test_papers 或 /home/user/papers",
        help="输入包含PDF论文的文件夹路径"
    )

    # 辅助：弹窗选择文件夹（兼容Windows）
    if st.button("📂 选择文件夹"):
        st.info("提示：Windows可直接粘贴路径（如 D:\\test_papers），mac/Linux粘贴绝对路径")

    # 执行按钮
    col1, col2 = st.columns([4, 1])
    with col2:
        submit_btn = st.button("开始批量整理", use_container_width=True)

    if submit_btn:
        if dir_path and os.path.isdir(dir_path):
            with st.spinner("正在批量处理所有PDF论文..."):
                args = argparse.Namespace(dir=dir_path)
                output = capture_print_output(organize_papers, args)

                st.subheader("批量处理日志")
                st.text_area("", output, height=300, key="organize_log")
                st.success("✅ 批量整理论文完成！")
        else:
            st.error("❌ 文件夹路径无效，请检查路径是否正确！")

# 3. 搜索论文文件（整篇）
elif selected_func == "搜索论文文件（整篇）":
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "搜索关键词/句子",
            placeholder="例如：NLP in management research",
            help="输入你想搜索的论文主题/关键词"
        )
    with col2:
        top_k = st.number_input(
            "返回结果数",
            min_value=1, max_value=10, value=3,
            key="top_k_file",
            help="最多返回10条结果"
        )

    if st.button("🔍 搜索论文文件"):
        if search_query:
            with st.spinner("正在语义搜索相关论文..."):
                args = argparse.Namespace(query=search_query, top_k=top_k)
                output = capture_print_output(search_paper_file, args)

                st.subheader("搜索结果")
                st.text_area("", output, height=300, key="file_search_log")
        else:
            st.warning("⚠️ 请输入搜索关键词！")

# 4. 搜索论文片段（精准）
elif selected_func == "搜索论文片段（精准）":
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "搜索关键词/句子（精准）",
            placeholder="例如：transformer在NLP中的应用",
            help="输入更精准的关键词，返回论文内具体片段"
        )
    with col2:
        top_k = st.number_input(
            "返回片段数",
            min_value=1, max_value=10, value=3,
            key="top_k_frag",
            help="最多返回10个片段"
        )

    if st.button("🔍 搜索论文片段"):
        if search_query:
            with st.spinner("正在搜索论文内精准片段..."):
                args = argparse.Namespace(query=search_query, top_k=top_k)
                output = capture_print_output(search_paper, args)

                st.subheader("精准片段结果")
                st.text_area("", output, height=300, key="frag_search_log")
        else:
            st.warning("⚠️ 请输入搜索关键词！")

# 5. 添加单张图片
elif selected_func == "添加单张图片":
    col1, col2 = st.columns([3, 1])
    with col1:
        image_file = st.file_uploader(
            "选择图片文件",
            type=["jpg", "jpeg", "png", "bmp"],
            key="image_upload",
            help="支持JPG/PNG/BMP格式，拖拽或点击上传"
        )
    with col2:
        st.write("")
        st.write("")
        submit_btn = st.button("添加并索引图片", use_container_width=True)

    if submit_btn:
        if image_file:
            # 临时保存图片
            temp_image_path = os.path.join(IMAGES_DIR, image_file.name)
            with open(temp_image_path, "wb") as f:
                f.write(image_file.getbuffer())

            with st.spinner("正在生成图片嵌入 → 索引..."):
                args = argparse.Namespace(path=temp_image_path)
                output = capture_print_output(add_image, args)

                st.subheader("图片处理日志")
                st.text_area("", output, height=300, key="image_log")
                st.success("✅ 图片添加并索引完成！")
        else:
            st.warning("⚠️ 请先选择要上传的图片文件！")

# 6. 以文搜图
elif selected_func == "以文搜图":
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "图片描述关键词/句子",
            placeholder="例如：海边日落、猫咪趴在沙发上",
            help="输入图片的描述，系统会匹配最相似的图片"
        )
    with col2:
        top_k = st.number_input(
            "返回图片数",
            min_value=1, max_value=10, value=3,
            key="top_k_img",
            help="最多返回10张图片"
        )

    if st.button("🔍 搜索相关图片"):
        if search_query:
            with st.spinner("正在根据描述搜索图片..."):
                args = argparse.Namespace(query=search_query, top_k=top_k)
                output = capture_print_output(search_image, args)

                st.subheader("图片搜索结果")
                st.text_area("", output, height=300, key="img_search_log")
        else:
            st.warning("⚠️ 请输入图片描述关键词！")