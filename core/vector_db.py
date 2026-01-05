# core/vector_db.py

import chromadb
# 关键修改：从 chromadb 导入 PersistentClient
from chromadb import PersistentClient
from chromadb.config import Settings
from config import CHROMA_DB_DIR
import uuid
from collections import defaultdict
import os

class VectorDB:
    """向量数据库操作封装（支持论文和图像两个集合）- 适配新版 ChromaDB"""
    def __init__(self):
        # 关键修改：使用 PersistentClient 替代 Client
        # 它会自动将数据保存到 persist_directory 指定的路径
        self.client = PersistentClient(
            path=CHROMA_DB_DIR,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        # 创建/获取论文集合（存储文本片段）
        self.paper_collection = self.client.get_or_create_collection(
            name="papers",
            metadata={"hnsw:space": "cosine"}  # 余弦相似度
        )
        # 创建/获取图像集合
        self.image_collection = self.client.get_or_create_collection(
            name="images",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"VectorDB initialized with PersistentClient. Data will be saved to: {CHROMA_DB_DIR}")

    # 论文相关操作
    def add_paper_fragments(self, fragments, embeddings, page_nums, paper_path):
        """添加论文文本片段到数据库"""
        ids = [f"paper_{uuid.uuid4()}" for _ in fragments]
        metadatas = [
            {"paper_path": paper_path, "page": page, "type": "paper"}
            for page in page_nums
        ]
        self.paper_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=fragments,
            metadatas=metadatas
        )
        # 不再需要任何 persist() 调用
        print(f"Added {len(fragments)} fragments to 'papers' collection. Persistence is automatic.")

    def search_paper_files(self, query_embedding, top_k=3):
        """
        搜索并返回最相关的论文文件列表（而非具体片段）。
        """
        num_candidates = top_k * 5
        results = self.paper_collection.query(
            query_embeddings=[query_embedding],
            n_results=num_candidates,
            include=["metadatas", "distances"]
        )

        if not results or not results["metadatas"][0]:
            return []

        paper_scores = defaultdict(lambda: [0.0, 0])

        for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
            paper_path = metadata.get("paper_path")
            if not paper_path:
                continue

            similarity = 1 - distance
            paper_scores[paper_path][0] += similarity
            paper_scores[paper_path][1] += 1

        ranked_papers = []
        for path, (total_score, count) in paper_scores.items():
            avg_score = total_score / count
            filename = os.path.basename(path)
            ranked_papers.append({
                "paper_path": path,
                "filename": filename,
                "average_similarity_score": avg_score
            })

        ranked_papers.sort(key=lambda x: x["average_similarity_score"], reverse=True)

        return ranked_papers[:top_k]

    def search_papers(self, query_embedding, top_k=3):
        """搜索相关论文片段"""
        results = self.paper_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        formatted = []
        if results and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                formatted.append({
                    "fragment": results["documents"][0][i],
                    "paper_path": results["metadatas"][0][i]["paper_path"],
                    "page": results["metadatas"][0][i]["page"],
                    "similarity_score": 1 - results["distances"][0][i]
                })
        return formatted

    # 图像相关操作
    def add_images(self, image_paths, embeddings):
        """添加图像到数据库"""
        ids = [f"img_{uuid.uuid4()}" for _ in image_paths]
        metadatas = [{"image_path": path, "type": "image"} for path in image_paths]
        self.image_collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas
        )
        # 不再需要任何 persist() 调用
        print(f"Added {len(image_paths)} images to 'images' collection. Persistence is automatic.")

    def search_images(self, query_embedding, top_k=3):
        """以文搜图（输入文本嵌入）"""
        results = self.image_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances"]
        )
        formatted = []
        if results and results["metadatas"][0]:
            for i in range(len(results["metadatas"][0])):
                formatted.append({
                    "image_path": results["metadatas"][0][i]["image_path"],
                    "similarity_score": 1 - results["distances"][0][i]
                })
        return formatted