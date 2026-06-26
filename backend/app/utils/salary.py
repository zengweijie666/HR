"""
文件名: app/utils/salary.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 薪资字符串解析，对应 AC2.9
入参: 薪资字符串如 "20-30K" / "20000-30000元"
出参: {"min": int, "max": int} 或 None
"""
import re


def parse_salary(text: str) -> dict | None:
    """解析薪资字符串为 {min, max}（单位 K）"""
    if not text:
        return None
    text = text.strip()
    # 先匹配 "20000-30000元" → 转 K（避免被通用区间正则误捕获）
    m = re.match(r"(\d+)\s*[-~]\s*(\d+)\s*元", text)
    if m:
        return {"min": int(m.group(1)) // 1000, "max": int(m.group(2)) // 1000}
    # 匹配 "20-30K" / "15-25k" / "20-30"
    m = re.match(r"(\d+)\s*[-~]\s*(\d+)\s*[kK]?", text)
    if m:
        return {"min": int(m.group(1)), "max": int(m.group(2))}
    # 匹配 "30K" / "30k"
    m = re.match(r"(\d+)\s*[kK]", text)
    if m:
        v = int(m.group(1))
        return {"min": v, "max": v}
    return None
