"""
文件名: app/utils/skill_synonyms.py
创建时间: 2026-06-29
作者: TalentSense Team
功能描述: 技能领域同义词映射，用于 required_skills 硬过滤前的语义扩展
入参: required_skills 列表
出参: 扩展后的 required_skills 列表

设计原理:
    - 领域词（nlp/cv/ai/ml/dl/frontend/backend/devops 等）代表一个技术领域，
      候选人可能写了领域下的具体技术（BERT/FastText/Transformer）但没写领域名本身。
      需要扩展为该领域下的所有具体技术，避免误过滤。
    - 具体技术（html/java/python/react 等）不扩展，保持严格匹配。
    - 扩展发生在 _enrich_candidates 硬过滤之前，与 strategy_selector 的同义词扩展
      （用于向量检索召回）互补：前者保证不误杀，后者保证能召回。
"""
from app.core.logger import logger


# 领域词 → 该领域下的具体技术/技能列表（全部小写，匹配时统一小写）
# 仅收录"领域/方向"级别的词，具体技术词（html/java/python/react/vue 等）不在此扩展
DOMAIN_SYNONYMS: dict[str, list[str]] = {
    # NLP / 自然语言处理
    "nlp": [
        "nlp", "自然语言处理", "bert", "fasttext", "transformer", "roberta",
        "albert", "lstm", "gru", "rnn", "seq2seq", "word2vec", "jieba",
        "tf-idf", "文本分类", "意图识别", "命名实体识别", "ner", "情感分析",
        "文本生成", "机器翻译", "问答系统", "reranker", "rerank",
    ],
    # 计算机视觉
    "cv": [
        "cv", "计算机视觉", "opencv", "yolo", "cnn", "resnet", "vgg",
        "图像分类", "目标检测", "语义分割", "实例分割", "ocr", "人脸识别",
    ],
    # AI / 人工智能（最泛的领域词）
    "ai": [
        "ai", "人工智能", "llm", "大模型", "大语言模型", "gpt", "claude",
        "deepseek", "qwen", "chatglm", "rag", "agent", "function call",
        "mcp", "a2a", "coze", "dify", "langchain",
    ],
    # 机器学习
    "ml": [
        "ml", "机器学习", "sklearn", "scikit-learn", "xgboost", "gbdt",
        "lightgbm", "random forest", "随机森林", "逻辑回归", "svm",
        "特征工程", "模型调优",
    ],
    # 深度学习
    "dl": [
        "dl", "深度学习", "pytorch", "tensorflow", "keras", "cuda",
        "gpu", "神经网络", "cnn", "rnn", "transformer",
    ],
    # 前端
    "frontend": [
        "前端", "frontend", "html", "html5", "css", "css3", "javascript",
        "js", "vue", "react", "angular", "typescript", "ts", "webpack",
        "vite", "element-ui", "element plus", "antd", "bootstrap",
    ],
    # 后端
    "backend": [
        "后端", "backend", "spring", "springboot", "spring boot", "django",
        "flask", "fastapi", "express", "nodejs", "node.js", "gin",
        "middleware", "微服务", "microservice",
    ],
    # DevOps / 运维
    "devops": [
        "devops", "运维", "docker", "kubernetes", "k8s", "ci/cd", "jenkins",
        "gitlab ci", "ansible", "terraform", "prometheus", "grafana",
        "linux", "shell", "nginx",
    ],
    # 数据分析
    "数据分析": [
        "数据分析", "data analysis", "pandas", "numpy", "matplotlib",
        "seaborn", "tableau", "power bi", "excel", "sql", "数据可视化",
        "数据挖掘", "data mining",
    ],
}

# 反向索引：具体技术 → 所属领域（用于判断一个 skill 是否是领域词）
_DOMAIN_TERMS_SET: set[str] = set(DOMAIN_SYNONYMS.keys())


def is_domain_term(skill: str) -> bool:
    """判断一个技能词是否是领域/方向词（需要扩展）

    入参:
        skill: 技能词（小写）
    出参:
        True 表示是领域词，需要扩展；False 表示是具体技术，保持严格匹配
    """
    return skill.lower() in _DOMAIN_TERMS_SET


def expand_required_skills(required_skills: list[str]) -> list[str]:
    """扩展 required_skills：领域词展开为该领域下的所有具体技术

    入参:
        required_skills: 原始提取的技能列表（如 ["nlp"] 或 ["html"]）
    出参:
        扩展后的技能列表（如 ["nlp", "bert", "fasttext", ...]）
        具体技术词不扩展，原样返回

    示例:
        ["nlp"] → ["nlp", "bert", "fasttext", "transformer", ...]
        ["html"] → ["html"]（不扩展，保持严格匹配）
        ["nlp", "html"] → ["nlp", "bert", "fasttext", ..., "html"]（nlp扩展，html不扩展）
    """
    if not required_skills:
        return required_skills

    expanded: set[str] = set()
    expanded_count = 0
    for skill in required_skills:
        if not isinstance(skill, str):
            continue
        skill_lower = skill.strip().lower()
        if not skill_lower:
            continue
        if skill_lower in DOMAIN_SYNONYMS:
            # 领域词：展开为该领域下所有技术
            for syn in DOMAIN_SYNONYMS[skill_lower]:
                expanded.add(syn.lower())
            expanded_count += 1
        else:
            # 具体技术：保持原样
            expanded.add(skill_lower)

    result = list(expanded)
    if expanded_count > 0:
        logger.info(
            f"required_skills 领域扩展: {required_skills} → {result} "
            f"(扩展了 {expanded_count} 个领域词)"
        )
    return result
