"""
文件名: app/core/ocr.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: RapidOCR 封装（复用 EduRAG），延迟加载
入参: 图片字节
出参: 提取的文本
"""
import io

# 顶层占位符，使 patch("app.core.ocr.RapidOCR") 可生效；实际加载在 property 内进行
RapidOCR = None

from app.core.logger import logger


class OCREngine:
    """RapidOCR 单引擎封装"""

    def __init__(self):
        self._engine = None

    @property
    def engine(self):
        """延迟加载 RapidOCR 实例

        通过 `global RapidOCR` 引用模块级符号，
        这样测试中 `patch("app.core.ocr.RapidOCR")` 可拦截构造调用。
        """
        if self._engine is None:
            global RapidOCR
            if RapidOCR is None:  # pragma: no cover - 实际运行时分支
                from rapidocr_onnxruntime import RapidOCR as _RapidOCR  # type: ignore
                RapidOCR = _RapidOCR
            self._engine = RapidOCR()
            logger.info("RapidOCR 引擎已加载")
        return self._engine

    @engine.setter
    def engine(self, value):
        """测试注入用"""
        self._engine = value

    def extract_text(self, image_bytes: bytes) -> str:
        """从图片字节提取文本

        RapidOCR 返回 (lines, elapse)；
        lines 元素可能为 (box, text, score) 或 (text, score)，
        本实现统一兼容，提取其中文本部分。
        """
        result = self.engine(io.BytesIO(image_bytes))
        if not result:
            return ""
        lines = result[0] if isinstance(result, (list, tuple)) and len(result) >= 1 else []
        texts: list[str] = []
        for item in lines:
            if isinstance(item, (list, tuple)):
                # 末位为分数 → 文本在倒数第二位；否则末位为文本
                if len(item) >= 2 and isinstance(item[-1], (int, float)):
                    texts.append(str(item[-2]))
                else:
                    texts.append(str(item[-1]))
            else:
                texts.append(str(item))
        return "\n".join(texts)


ocr_engine = OCREngine()
