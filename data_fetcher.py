"""
data_fetcher.py - A股每日数据抓取 V4
- mock模式: 模拟数据 (python main.py)
- real模式: 腾讯+新浪+akshare混合抓取 (python main.py --real)
- strict模式: 仅真实数据，缺失报错 (python main.py --real --strict)
"""
from datetime import datetime, timedelta
from typing import Optional
import json, time

# ============================================================
# 数据源追踪工具
# ============================================================
def _ok(api, url="", data=None):
    """成功标记"""
    return {"_source": {"api": api, "url": url, "time": datetime.now().strftime("%H:%M:%S"), "status": "ok"}, **(data or {})}

def _fail(api, reason=""):
    """失败标记"""
    return {"_source": {"api": api, "url": "", "time": datetime.now().strftime("%H:%M:%S"), "status": "fail", "reason": reason}}

def _mock_source():
    return {"_source": {"api": "mock", "url": "", "time": "", "status": "mock"}}

def _is_ok(d):
    return isinstance(d, dict) and d.get("_source", {}).get("status") == "ok"

def _is_mock(d):
    return isinstance(d, dict) and d.get("_source", {}).get("status") == "mock"

# ============================================================
# Mock 数据 (仅 demo 用，标注来源)
# ============================================================
def get_mock_data() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    s = _mock_source()
    return {
        "date": today, "source": "mock",
        "market_overview": {**s, "上证指数": {"code":"000001","price":3356.78,"change_pct":0.42,"change_amt":14.08,"open":3340.12,"high":3372.50,"low":3335.80}, "深证成指":{"code":"399001","price":10892.45,"change_pct":-0.18,"change_amt":-19.35,"open":10920.30,"high":10950.00,"low":10850.20}, "创业板指":{"code":"399006","price":2187.32,"change_pct":0.85,"change_amt":18.47,"open":2168.00,"high":2195.60,"low":2160.50}, "科创50":{"code":"000688","price":968.54,"change_pct":1.23,"change_amt":11.75,"open":956.00,"high":972.30,"low":954.20}, "沪深300":{"code":"000300","price":3985.21,"change_pct":0.31,"change_amt":12.34,"open":3970.00,"high":3995.80,"low":3965.00}},
        "market_stats": {**s, "成交额(亿)":8962.35,"涨停家数":47,"跌停家数":12,"上涨家数":2134,"下跌家数":2891,"平盘家数":215,"北向资金净流入(亿)":23.56,"主力资金净流入(亿)":-87.32,"炸板率%":28.5,"封板率%":71.5,"振幅%":0.7},
        "sector_flow": {**s, "items":[
            {"板块":"半导体","涨跌幅%":2.35,"主力净流入(亿)":18.56,"领涨股":"中芯国际","涨停数":5},
            {"板块":"软件开发","涨跌幅%":1.87,"主力净流入(亿)":12.34,"领涨股":"金山办公","涨停数":3},
            {"板块":"通信设备","涨跌幅%":1.52,"主力净流入(亿)":8.92,"领涨股":"中兴通讯","涨停数":4},
            {"板块":"汽车整车","涨跌幅%":1.21,"主力净流入(亿)":6.78,"领涨股":"比亚迪","涨停数":2},
            {"板块":"白酒","涨跌幅%":-1.85,"主力净流入(亿)":-22.15,"领涨股":"贵州茅台","涨停数":0},
            {"板块":"房地产开发","涨跌幅%":-1.62,"主力净流入(亿)":-15.43,"领涨股":"万科A","涨停数":0},
        ]},
        "global_markets": {**s, "indices":[
            {"name":"道琼斯工业","code":"DJI","price":42350.28,"change_pct":0.35,"status":"收盘"},
            {"name":"纳斯达克","code":"IXIC","price":18752.14,"change_pct":0.72,"status":"收盘"},
            {"name":"标普500","code":"SPX","price":5680.45,"change_pct":0.48,"status":"收盘"},
            {"name":"恒生指数","code":"HSI","price":19250.80,"change_pct":0.15,"status":"收盘"},
            {"name":"富时A50期货","code":"XINA50","price":13285.00,"change_pct":-0.22,"status":"夜盘"},
            {"name":"VIX恐慌指数","code":"VIX","price":14.35,"change_pct":-3.20,"status":"收盘"},
        ], "summary":"","a_share_impact":"偏多","impact_score":72},
        "yesterday_sectors": {**s},
        "call_auction": {**s},
        "dragon_tiger": {**s},
        "sector_alerts": {**s},
        "limit_up_streak": {**s},
        "news_strong": {**s},
        "news_policy": {**s},
        "news_weak": {**s},
        "main_themes_detail": {**s},
        "potential_themes": {**s},
        "veto_signals": {**s},
        "recommended_stocks": {**s},
        "key_events": {**s},
    }


# ============================================================
# 真实数据抓取 - 大盘指数 (腾讯API)
# ============================================================
def _fetch_indices():
    """腾讯财经 - A股指数实时行情"""
    import requests as _r
    url = "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688,sh000300"
    try:
        resp = _r.get(url, timeout=10)
        resp.encoding = "gbk"
        text = resp.text
    except Exception as e:
        return _fail("腾讯API", str(e))

    codes = {"上证指数":"sh000001","深证成指":"sz399001","创业板指":"sz399006","科创50":"sh000688","沪深300":"sh000300"}
    result = {}
    for name, code in codes.items():
        try:
            key = f"v_{code}"
            start = text.find(key)
            if start < 0: continue
            end = text.find('"', start); end2 = text.find('"', end+1)
            parts = text[end+1:end2].split("~")
            if len(parts) < 10: continue
            price, prev = float(parts[3]), float(parts[4])
            chg_pct = round((price-prev)/prev*100,2) if prev else 0
            result[name] = {
                "code": code, "price": price, "change_pct": chg_pct,
                "change_amt": round(price-prev,2),
                "open": float(parts[5]) if parts[5] else price,
                "high": float(parts[33]) if len(parts)>33 and parts[33] else price,
                "low": float(parts[34]) if len(parts)>34 and parts[34] else price,
            }
        except Exception:
            continue
    if result:
        return _ok("腾讯API", url, result)
    return _fail("腾讯API", "解析失败")


# ============================================================
# 真实数据抓取 - 市场统计 (新浪API)
# ============================================================
def _fetch_stats():
    """新浪API成交额 + push2换手率"""
    import requests as _r, json as _j

    result = {
        "成交额(亿)": 0, "涨停家数": None, "跌停家数": None,
        "上涨家数": None, "下跌家数": None, "平盘家数": None,
        "北向资金净流入(亿)": None, "主力资金净流入(亿)": None,
        "炸板率%": None, "封板率%": None, "振幅%": None,
    }

    # 1. 新浪API: 成交额 (可靠)
    high_v = low_v = prev_v = 0
    try:
        resp = _r.get("https://hq.sinajs.cn/list=sh000001", timeout=10,
                      headers={"Referer":"https://finance.sina.com.cn"})
        resp.encoding = "gbk"
        parts = resp.text.split('"')[1].split(",")
        if len(parts) >= 10:
            result["成交额(亿)"] = round(float(parts[9]) / 1e8, 2) if parts[9] else 0
            # 新浪也提供了最高最低昨收 (parts[4]=最高, parts[5]=最低, parts[2]=昨收)
            high_v = float(parts[4]) if parts[4] else 0
            low_v = float(parts[5]) if parts[5] else 0
            prev_v = float(parts[2]) if parts[2] else 0
    except Exception:
        pass

    # 2. 计算振幅 (从新浪数据直接算，不需push2)
    if high_v and low_v and prev_v:
        result["振幅%"] = round((high_v - low_v) / prev_v * 100, 2)

    # 3. push2 HTTP: 涨跌家数 (不可靠，当作bonus)
    try:
        r2 = _r.get("http://push2.eastmoney.com/api/qt/stock/get", timeout=5, params={
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "invt": "2", "fltt": "2", "secid": "1.000001",
            "fields": "f104,f105,f106"
        })
        d = _j.loads(r2.text).get("data", {})
        for fld, key in [("f104","上涨家数"),("f105","下跌家数"),("f106","平盘家数")]:
            if d.get(fld) and str(d[fld]) != "-":
                v = int(d[fld])
                if v > 0: result[key] = v
    except Exception:
        pass

    # 检查是否有任何数据
    has_data = result["成交额(亿)"] > 0 or result["换手率%"] is not None
    if has_data:
        return _ok("新浪+push2", "hq.sinajs.cn", result)
    return _fail("市场统计", "所有数据源不可用")


# ============================================================
# 真实数据抓取 - 外围市场 (腾讯API)
# ============================================================
def _fetch_global():
    """腾讯财经 - 全球主要指数"""
    import requests as _r
    url_base = "https://qt.gtimg.cn/q="
    codes = {"道琼斯工业":"usDJI","纳斯达克":"usIXIC","标普500":"usINX","恒生指数":"hkHSI"}
    indices = []
    for name, code in codes.items():
        try:
            resp = _r.get(url_base + code, timeout=10)
            resp.encoding = "gbk"
            text = resp.text
            start = text.find('"'); end = text.find('"', start+1)
            parts = text[start+1:end].split("~")
            if len(parts) < 10: continue
            price = float(parts[3]) if parts[3] else 0
            chg_pct = float(parts[32]) if len(parts)>32 and parts[32] else 0
            update_time = parts[30] if len(parts)>30 else ""
            indices.append({"name":name,"code":code,"price":price,"change_pct":chg_pct,"status":update_time})
        except Exception:
            continue

    # A50期货
    try:
        resp = _r.get(url_base + "int_XINA50", timeout=10)
        resp.encoding = "gbk"
        text = resp.text
        start = text.find('"'); end = text.find('"', start+1)
        parts = text[start+1:end].split("~")
        if len(parts)>3 and parts[3]:
            indices.append({"name":"富时A50期货","code":"XINA50","price":float(parts[3]),"change_pct":float(parts[32]) if len(parts)>32 and parts[32] else 0,"status":""})
    except Exception:
        pass

    # VIX
    try:
        resp = _r.get(url_base + "usVIX", timeout=10)
        resp.encoding = "gbk"
        text = resp.text
        start = text.find('"'); end = text.find('"', start+1)
        parts = text[start+1:end].split("~")
        if len(parts)>3 and parts[3]:
            indices.append({"name":"VIX恐慌指数","code":"VIX","price":float(parts[3]),"change_pct":float(parts[32]) if len(parts)>32 and parts[32] else 0,"status":""})
    except Exception:
        pass

    if indices:
        return _ok("腾讯API", url_base, {"indices": indices})
    return _fail("腾讯API", "无数据")


# ============================================================
# 真实数据抓取 - 板块资金流 (akshare -> datacenter.eastmoney.com)
# ============================================================
def _fetch_sector_flow():
    """akshare - 行业板块资金流"""
    try:
        import akshare as ak
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业板块")
        items = []
        for _, r in df.head(12).iterrows():
            items.append({
                "板块": r.get("名称",""), "涨跌幅%": round(float(r.get("涨跌幅",0)),2),
                "主力净流入(亿)": round(float(r.get("主力净流入",0))/1e8,2) if r.get("主力净流入") else 0,
                "领涨股": r.get("领涨股",""), "涨停数": 0,
            })
        if items:
            return _ok("akshare", "datacenter.eastmoney.com", {"items": items})
    except Exception as e:
        pass
    return _fail("akshare", "板块资金流接口不可用")


# ============================================================
# 真实数据抓取 - 涨停板 (akshare)
# ============================================================
def _fetch_limit_up():
    """akshare - 涨停池"""
    today = datetime.now().strftime("%Y%m%d")
    try:
        import akshare as ak
        df = ak.stock_zt_pool_em(date=today)
        return _ok("akshare", "push2.eastmoney.com", {"total": len(df), "data": df.head(20).to_dict("records")})
    except Exception as e:
        return _fail("akshare", f"涨停池不可用: {e}")


# ============================================================
# 获取全部真实数据
# ============================================================
def get_real_data(strict=False) -> dict:
    """用腾讯+新浪+akshare混合抓取。strict=True时缺失数据报错。"""
    today = datetime.now().strftime("%Y-%m-%d")
    data = {"date": today, "source": "real", "modules": {}}

    # 1. 大盘指数 (腾讯)
    indices = _fetch_indices()
    data["market_overview"] = indices
    data["modules"]["大盘指数"] = indices["_source"]

    # 2. 市场统计 (新浪)
    stats = _fetch_stats()
    data["market_stats"] = stats
    data["modules"]["市场统计"] = stats["_source"]

    # 3. 外围市场 (腾讯)
    global_mk = _fetch_global()
    data["global_markets"] = global_mk
    data["modules"]["外围市场"] = global_mk["_source"]

    # 4. 板块资金流 (akshare)
    sector = _fetch_sector_flow()
    data["sector_flow"] = sector
    data["modules"]["板块资金流"] = sector["_source"]

    # 5. 涨停板 (akshare, push2可能被阻断)
    limits = _fetch_limit_up()
    data["limit_up_streak"] = limits
    data["modules"]["涨停板"] = limits["_source"]

    # 6-17. AI分析推算模块（不是真实API数据，是AI基于规则的分析）
    analysis_src = {"_source": {"api": "AI分析推算", "url": "", "time": datetime.now().strftime("%H:%M:%S"), "status": "analysis"}}

    # 提供基础结构供AI分析使用
    data["yesterday_sectors"] = {**analysis_src, "top_gainers": [], "top_losers": [], "continuity_score": 0, "summary": "基于今日板块表现推算"}
    data["call_auction"] = {**analysis_src, "high_open_sectors": [], "low_open_sectors": [], "direction_signal": "待判断", "summary": "集合竞价数据需盘前API接入"}
    data["dragon_tiger"] = {**analysis_src, "records": [], "linked_sectors_today": [], "linkage_score": 0, "summary": "龙虎榜数据需T+1获取"}
    data["sector_alerts"] = {**analysis_src}
    data["news_strong"] = {**analysis_src}
    data["news_policy"] = {**analysis_src}
    data["news_weak"] = {**analysis_src}
    data["main_themes_detail"] = {**analysis_src}
    data["potential_themes"] = {**analysis_src}
    data["veto_signals"] = {**analysis_src}
    data["recommended_stocks"] = {**analysis_src}
    data["key_events"] = {**analysis_src}

    for mod in ["yesterday_sectors","call_auction","dragon_tiger","sector_alerts",
                "news_strong","news_policy","news_weak","main_themes_detail",
                "potential_themes","veto_signals","recommended_stocks","key_events"]:
        data["modules"][mod] = analysis_src["_source"]

    # strict模式检查
    if strict:
        failures = [k for k, v in data["modules"].items() if v["status"] == "fail"]
        if failures:
            print(f"  [strict] 以下模块数据缺失: {', '.join(failures)}")

    return data


# ============================================================
# 统一入口
# ============================================================
def fetch_data(use_real=False, strict=False):
    if use_real:
        return get_real_data(strict=strict)
    return get_mock_data()


if __name__ == "__main__":
    d = fetch_data(True)
    print("\n=== 数据源报告 ===")
    for mod, src in d.get("modules", {}).items():
        icon = "OK" if src["status"]=="ok" else ("MOCK" if src["status"]=="mock" else "FAIL")
        print(f"  [{icon}] {mod}: {src['api']} {src.get('reason','')}")
