#!/usr/bin/env python3
"""
main.py — A股每日分析看板 V4
  python main.py                  # mock数据
  python main.py --real           # 真实数据
  python main.py --real --strict  # 仅真实数据，缺失报错
"""
import sys, os, argparse
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_fetcher import fetch_data
from ai_analyzer import analyze
from renderer import render, get_latest_path


def main():
    parser = argparse.ArgumentParser(description="A股每日分析看板")
    parser.add_argument("--real", action="store_true", help="真实数据模式")
    parser.add_argument("--strict", action="store_true", help="严格模式: 不允许mock数据")
    parser.add_argument("--llm", type=str, default=None, metavar="KEY", help="LLM分析")
    parser.add_argument("--output", type=str, default=None, help="输出路径")
    args = parser.parse_args()

    print("=" * 60)
    print("  A股每日分析看板" + (" [严格模式]" if args.strict else ""))
    print("=" * 60)

    # Step 1: 获取数据
    print("\n[1/3] 正在获取市场数据...")
    data = fetch_data(use_real=args.real, strict=args.strict)

    # 数据源报告
    if "modules" in data:
        ok_count = sum(1 for v in data["modules"].values() if v["status"] == "ok")
        fail_count = sum(1 for v in data["modules"].values() if v["status"] == "fail")
        mock_count = sum(1 for v in data["modules"].values() if v["status"] == "mock")
        print(f"  数据来源: {data['source']} | 日期: {data['date']}")
        print(f"  数据完整性: OK={ok_count} FAIL={fail_count} MOCK={mock_count}")

    # ---- Step 2: AI分析 ----
    print("\n[2/3] 正在进行结构化分析...")
    api_key = args.llm or os.environ.get("OPENAI_API_KEY")
    use_llm = bool(api_key)
    analysis = analyze(data, use_llm=use_llm, api_key=api_key)
    print(f"  ✓ 分析完成 (引擎: {'LLM' if use_llm else '规则引擎'})")
    print(f"  ✓ 市场温度: {analysis['market_summary']['temperature']}")
    print(f"  ✓ 综合评分: {analysis['trade_advice']['overall_score']}")
    print(f"  ✓ 操作建议: {analysis['trade_advice']['position_advice']}")

    # ---- Step 3: 渲染看板 ----
    print("\n[3/3] 正在生成HTML看板...")
    output_path = render(data, analysis, output_path=args.output)
    print(f"  ✓ 看板已生成: {output_path}")
    print(f"  ✓ 快速查看: {get_latest_path()}")

    # ---- 摘要 ----
    print("\n" + "=" * 60)
    print("  今日摘要")
    print("=" * 60)
    a = analysis
    ms = a["market_summary"]
    gm = a["global_markets"]
    mt = a["main_theme"]
    nw = a["news_impact"]
    au = a["call_auction"]
    dt = a["dragon_tiger"]
    lm = a["limit_up_streak"]
    ta = a["trade_advice"]
    print(f"  市场温度: {ms['temperature']} ({ms['temperature_score']}分)")
    print(f"  成交额:   {ms['volume']:.0f} 亿元 — {ms['volume_desc']}")
    print(f"  涨跌比:   {ms['up_count']}↑ / {ms['down_count']}↓  涨停{ms['limit_up']} / 跌停{ms['limit_down']}")
    print(f"  外围情绪: {gm['a_share_impact']} ({gm['impact_score']}分) — {gm['vix_note']}")
    print(f"  竞价方向: {au['direction_signal']} ({au['direction_score']}分) — {au['summary']}")
    print(f"  消息面:   {nw['mood']} ({nw['sentiment_score']}分) — 强相关{nw['bullish_count']}/{len(nw.get('strong_news',[]))}")
    if mt["top_theme"]:
        print(f"  核心主线: {mt['top_theme']['name']} ({mt['top_theme']['composite_score']}分) — 平均热度{mt['avg_score']}分")
    print(f"  龙虎联动: {dt['linkage_score']}分 — {dt['summary'][:40]}...")
    print(f"  涨停梯队: {lm['streak_score']}分 — {lm['summary'][:40]}...")
    print(f"  仓位建议: {ta['position_advice']} — 风险: {ta['risk_level']}")
    print(f"  关注板块: {'、'.join(ta['watch_sectors'][:5]) if ta['watch_sectors'] else '暂无'}")
    # 数据完整性报告
    if "modules" in data:
        print("\n" + "-" * 40)
        print("  数据完整性报告")
        print("-" * 40)
        mods = data["modules"]
        for name, info in mods.items():
            s = info["status"]
            if s == "ok":       icon = "REAL"
            elif s == "analysis": icon = "AI"
            elif s == "mock":   icon = "MOCK"
            else:               icon = "FAIL"
            extra = f" - {info.get('reason','')}" if s=="fail" else f" | {info['api']}"
            print(f"  [{icon}] {name}{extra}")
        total = len(mods)
        real_n = sum(1 for v in mods.values() if v["status"]=="ok")
        ai_n = sum(1 for v in mods.values() if v["status"]=="analysis")
        fail_n = sum(1 for v in mods.values() if v["status"]=="fail")
        print(f"\n  总计: {real_n}个真实API + {ai_n}个AI推算 + {fail_n}个待修复")
        print(f"  只有数值型数据(点位/成交额)需要真实API; 分析型模块由AI基于可用数据推算")

    print(f"\n  在浏览器中打开: file:///{output_path}")
    print()


if __name__ == "__main__":
    main()
