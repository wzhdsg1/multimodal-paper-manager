# core/embedding.py

from sentence_transformers import SentenceTransformer
import open_clip
import torch
from config import TEXT_EMBEDDING_MODEL, CLIP_MODEL_NAME


class TextEmbedding:
    """文本嵌入生成器"""

    def __init__(self):
        self.model = SentenceTransformer(TEXT_EMBEDDING_MODEL)

    def embed(self, texts):
        """生成文本列表的嵌入向量"""
        return self.model.encode(texts).tolist()


class ImageEmbedding:
    """图像嵌入生成器（基于 open_clip_torch）"""

    def __init__(self):
        # 关键修改：将 '/' 替换为 '-'
        model_name = CLIP_MODEL_NAME.replace('/', '-')

        print(f"正在加载CLIP模型: {model_name}...")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained='laion2b_s34b_b79k'
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.tokenizer = open_clip.get_tokenizer(model_name)
        print("CLIP模型加载完成！")

    def embed(self, images):
        """生成图像列表的嵌入向量（输入为PIL图像对象列表）"""
        processed_images = [self.preprocess(img).unsqueeze(0).to(self.device) for img in images if img is not None]
        if not processed_images:
            return []

        with torch.no_grad():
            inputs = torch.cat(processed_images)
            embeddings = self.model.encode_image(inputs)
            embeddings /= embeddings.norm(dim=-1, keepdim=True)
            return embeddings.cpu().numpy().tolist()

    def embed_text(self, text):
        """生成文本查询的嵌入（用于以文搜图）"""
        with torch.no_grad():
            text_tokens = self.tokenizer([text]).to(self.device)
            embedding = self.model.encode_text(text_tokens)
            embedding /= embedding.norm(dim=-1, keepdim=True)
            return embedding.cpu().numpy().tolist()[0]