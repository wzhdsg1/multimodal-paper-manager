# config.py

import os

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 数据存储路径
PAPERS_DIR = os.path.join(DATA_DIR, "papers")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chroma_db")

# 模型配置
TEXT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CLIP_MODEL_NAME = "ViT-B/32"

# [新增] 自动分类配置
CLASSIFICATION_MODEL = "facebook/bart-large-mnli"
TOPICS = [
    "Computer Vision",
    "Natural Language Processing",
    "Machine Learning",
    "Reinforcement Learning",
    "Data Mining",
    "Artificial Intelligence",
    "Robotics",
    "Neuroscience"
]
UNCATEGORIZED_FOLDER = "Uncategorized" # 分类失败时的默认文件夹

# 确保目录存在
os.makedirs(PAPERS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_DIR, exist_ok=True)
os.makedirs(os.path.join(PAPERS_DIR, UNCATEGORIZED_FOLDER), exist_ok=True)