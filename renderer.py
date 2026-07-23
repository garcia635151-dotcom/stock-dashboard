"""
renderer.py — HTML 看板渲染模块
使用 Jinja2 模板引擎渲染卡片式看板
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def render(raw_data: dict, analysis: dict, output_path: str = None) -> str:
    """
    渲染 HTML 看板
    Args:
        raw_data:  fetch_data() 返回的原始数据
        analysis:  ai_analyzer.analyze() 返回的分析结果
        output_path: 输出文件路径（可选，默认 output/dashboard_YYYY-MM-DD.html）
    Returns:
        生成的 HTML 文件路径
    """
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    # 合并数据传给模板
    template_data = {
        "raw": raw_data,
        "analysis": analysis,
    }

    template = env.get_template("dashboard.html")
    html = template.render(data=template_data)

    # 确定输出路径
    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        date_str = raw_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        output_path = os.path.join(OUTPUT_DIR, f"dashboard_{date_str}.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    # 同时输出一份 latest.html 方便查看
    latest_path = os.path.join(OUTPUT_DIR, "latest.html")
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def get_latest_path() -> str:
    """获取最新看板路径"""
    return os.path.join(OUTPUT_DIR, "latest.html")
