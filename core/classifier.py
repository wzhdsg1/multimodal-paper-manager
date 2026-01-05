# core/classifier.py

from transformers import pipeline
from config import CLASSIFICATION_MODEL, TOPICS


class PaperClassifier:
    """
    使用零样本分类模型对论文进行主题分类。
    """

    def __init__(self):
        print(f"正在加载分类模型 '{CLASSIFICATION_MODEL}'... 这可能需要一些时间。")
        self.classifier = pipeline(
            "zero-shot-classification",
            model=CLASSIFICATION_MODEL,
            device=-1  # 使用CPU。如果有GPU且已配置好PyTorch，可以改为0
        )
        print("分类模型加载完成！")

    def classify(self, text_to_classify: str) -> str:
        """
        对给定的文本（标题+摘要）进行分类，返回最可能的主题。
        """
        if not text_to_classify or len(text_to_classify.strip()) < 50:
            return None  # 如果文本太短，无法有效分类

        try:
            result = self.classifier(text_to_classify, TOPICS, multi_label=False)
            best_topic = result['labels'][0]
            score = result['scores'][0]

            print(f"分类结果: '{best_topic}' (置信度: {score:.2f})")

            # 可以设置一个置信度阈值，如果太低则归为未分类
            if score < 0.3:  # 阈值可以根据效果调整
                print("置信度太低，归为未分类。")
                return None

            return best_topic
        except Exception as e:
            print(f"分类时发生错误: {e}")
            return None