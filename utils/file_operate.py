# utils/file_operate.py

import os
import shutil
from pathlib import Path
from typing import Optional  # <--- 添加这一行
from config import PAPERS_DIR, UNCATEGORIZED_FOLDER


# 修改函数定义
def move_to_topic_folder(paper_path: str, topic: Optional[str]) -> str:
    """
    根据主题自动创建文件夹并移动论文。
    如果topic为None，则移动到未分类文件夹。
    """
    if topic is None:
        target_dir = os.path.join(PAPERS_DIR, UNCATEGORIZED_FOLDER)
    else:
        safe_topic_name = topic.replace(" ", "_")
        target_dir = os.path.join(PAPERS_DIR, safe_topic_name)

    os.makedirs(target_dir, exist_ok=True)

    filename = os.path.basename(paper_path)
    target_path = os.path.join(target_dir, filename)

    counter = 1
    original_target_path = target_path
    while os.path.exists(target_path):
        name, ext = os.path.splitext(filename)
        target_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
        counter += 1

    try:
        shutil.move(paper_path, target_path)
        print(f"论文已移动至: {target_path}")
        return target_path
    except Exception as e:
        print(f"移动文件失败: {e}")
        return paper_path