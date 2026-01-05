import torch
import open_clip  # 更换为 open_clip
from PIL import Image
from pathlib import Path
import config  # 确保能导入配置文件


class ImageProcessor:
    """图像处理和嵌入生成器（基于 open_clip_torch）"""

    def __init__(self):
        # 从配置文件加载模型名称
        model_name = config.CLIP_MODEL_NAME.replace('/', '_')  # open_clip 使用 '_' 作为分隔符

        print(f"正在加载CLIP模型: {model_name}...")
        # 使用 open_clip 创建模型和预处理工具
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained='laion2b_s34b_b79k'  # 使用一个常用的预训练权重
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.tokenizer = open_clip.get_tokenizer(model_name)  # 获取文本tokenizer
        print("CLIP模型加载完成！")

    def load_and_preprocess_image(self, image_path):
        """加载图像并进行预处理"""
        try:
            img = Image.open(image_path).convert("RGB")
            return self.preprocess(img).unsqueeze(0).to(self.device)
        except Exception as e:
            print(f"加载或预处理图像失败 {image_path}：{str(e)}")
            return None

    def embed_image(self, image_tensor):
        """为单个预处理后的图像生成嵌入向量"""
        with torch.no_grad():
            embedding = self.model.encode_image(image_tensor)
            embedding /= embedding.norm(dim=-1, keepdim=True)  # 归一化
            return embedding.cpu().numpy().tolist()[0]

    def embed_text(self, text):
        """为文本查询生成嵌入向量（用于以文搜图）"""
        with torch.no_grad():
            text_tokens = self.tokenizer([text]).to(self.device)
            embedding = self.model.encode_text(text_tokens)
            embedding /= embedding.norm(dim=-1, keepdim=True)  # 归一化
            return embedding.cpu().numpy().tolist()[0]


# --- 以下是原有的文件操作函数，保持不变 ---

def copy_image_to_data(image_path):
    """将图像复制到统一的images目录"""
    try:
        src = Path(image_path)
        dest = Path(config.IMAGES_DIR) / src.name
        if not dest.exists():
            import shutil
            shutil.copy2(src, dest)
            return str(dest)
        return str(dest)
    except Exception as e:
        print(f"复制图像失败：{str(e)}")
        return image_path