# core/pdf_processor.py

import PyPDF2
from pathlib import Path
from typing import Optional, Tuple
import config


def extract_text_with_pages(pdf_path):
    """提取PDF文本并保留页码信息"""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text_with_pages = []
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    text_with_pages.append((text.strip(), page_num))
            return text_with_pages
    except Exception as e:
        print(f"提取PDF文本失败：{str(e)}")
        return []


# [新增]
def extract_title_and_abstract(pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    启发式地从PDF的前几页提取标题和摘要。
    """
    title, abstract = None, None
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            # 通常标题和摘要在前2-3页
            for i in range(min(3, len(reader.pages))):
                page = reader.pages[i]
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')

                # 1. 寻找标题 (通常是第一行或第二行，且较长)
                if not title:
                    for line in lines:
                        stripped_line = line.strip()
                        if len(stripped_line) > 10 and not stripped_line.isdigit():
                            title = stripped_line
                            break

                # 2. 寻找摘要
                if not abstract:
                    abstract_start_idx = -1
                    for j, line in enumerate(lines):
                        if "abstract" in line.lower():
                            abstract_start_idx = j + 1  # 从下一行开始
                            break

                    if abstract_start_idx != -1:
                        abstract_lines = []
                        for j in range(abstract_start_idx, len(lines)):
                            # 假设摘要在引言(Introduction)之前结束
                            if "introduction" in lines[j].lower():
                                break
                            abstract_lines.append(lines[j].strip())
                        abstract = " ".join(abstract_lines)
                        break  # 找到摘要后就退出循环

    except Exception as e:
        print(f"提取标题和摘要时出错: {e}")

    return title, abstract


def copy_paper_to_data(pdf_path):
    """将论文复制到统一的papers目录（备用方法）"""
    try:
        src = Path(pdf_path)
        dest = Path(config.PAPERS_DIR) / src.name
        if not dest.exists():
            import shutil
            shutil.copy2(src, dest)
            return str(dest)
        return str(dest)
    except Exception as e:
        print(f"复制论文失败：{str(e)}")
        return pdf_path