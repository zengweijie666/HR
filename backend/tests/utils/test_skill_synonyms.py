"""
文件名: tests/utils/test_skill_synonyms.py
创建时间: 2026-06-29
作者: TalentSense Team
功能描述: 技能领域同义词扩展单元测试
"""
from app.utils.skill_synonyms import (
    DOMAIN_SYNONYMS,
    is_domain_term,
    expand_required_skills,
)


def test_is_domain_term_recognizes_nlp():
    """nlp 是领域词"""
    assert is_domain_term("nlp") is True
    assert is_domain_term("NLP") is True  # 大小写不敏感
    assert is_domain_term("cv") is True
    assert is_domain_term("ai") is True
    assert is_domain_term("frontend") is True


def test_is_domain_term_rejects_specific_technology():
    """具体技术不是领域词"""
    assert is_domain_term("html") is False
    assert is_domain_term("java") is False
    assert is_domain_term("python") is False
    assert is_domain_term("react") is False
    assert is_domain_term("vue") is False


def test_expand_nlp_returns_all_related_technologies():
    """nlp 扩展应包含 BERT/FastText/Transformer 等相关技术"""
    result = expand_required_skills(["nlp"])
    result_lower = [s.lower() for s in result]
    # 必须包含 NLP 本身
    assert "nlp" in result_lower
    # 必须包含 NLP 领域下的具体技术
    assert "bert" in result_lower
    assert "fasttext" in result_lower
    assert "transformer" in result_lower
    assert "jieba" in result_lower
    assert "文本分类" in result_lower


def test_expand_html_keeps_strict():
    """html 是具体技术，不扩展"""
    result = expand_required_skills(["html"])
    assert len(result) == 1
    assert result[0].lower() == "html"


def test_expand_mixed_domain_and_specific():
    """混合场景：nlp 扩展，html 保持严格"""
    result = expand_required_skills(["nlp", "html"])
    result_lower = [s.lower() for s in result]
    # nlp 扩展后的技术
    assert "nlp" in result_lower
    assert "bert" in result_lower
    assert "fasttext" in result_lower
    # html 保持原样
    assert "html" in result_lower


def test_expand_empty_list():
    """空列表不扩展"""
    assert expand_required_skills([]) == []


def test_expand_none_items_filtered():
    """非字符串项被过滤"""
    result = expand_required_skills(["nlp", None, "", 123])
    result_lower = [s.lower() for s in result]
    assert "nlp" in result_lower
    assert "bert" in result_lower
    assert None not in result
    assert "" not in result


def test_expand_case_insensitive():
    """大写领域词也能扩展"""
    result = expand_required_skills(["NLP", "CV"])
    result_lower = [s.lower() for s in result]
    assert "nlp" in result_lower
    assert "bert" in result_lower
    assert "cv" in result_lower
    assert "opencv" in result_lower


def test_expand_does_not_include_other_domain_skills():
    """nlp 扩展不应包含 cv 领域的技能"""
    result = expand_required_skills(["nlp"])
    result_lower = [s.lower() for s in result]
    assert "opencv" not in result_lower
    assert "yolo" not in result_lower
    assert "resnet" not in result_lower


def test_expand_frontend_includes_html_css_js():
    """frontend 领域扩展应包含 html/css/js"""
    result = expand_required_skills(["frontend"])
    result_lower = [s.lower() for s in result]
    assert "html" in result_lower
    assert "css" in result_lower
    assert "javascript" in result_lower
    assert "vue" in result_lower


def test_all_domain_terms_have_non_empty_synonyms():
    """所有领域词的同义词列表不能为空"""
    for domain, synonyms in DOMAIN_SYNONYMS.items():
        assert synonyms, f"领域词 {domain} 的同义词列表为空"
        assert domain in synonyms, f"领域词 {domain} 的同义词列表应包含自身"
