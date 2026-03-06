#!/usr/bin/env python3
"""
锦成盛危机监测系统 - 数据获取模块
基于锦成盛资管危机监测框架 (2024.07-2026.01)
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

# FRED API (免费，需要注册获取API Key)
# https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = "YOUR_FRED_API_KEY"  # 需要替换为真实API Key

# 数据缓存
_cache = {}
_cache_time = {}

def get_from_cache(key: str, max_age_seconds: int = 300) -> Optional[dict]:
    """从缓存获取数据，默认缓存5分钟"""
    if key in _cache and key in _cache_time:
        if time.time() - _cache_time[key] < max_age_seconds:
            return _cache[key]
    return None

def save_to_cache(key: str, data: dict):
    """保存数据到缓存"""
    _cache[key] = data
    _cache_time[key] = time.time()

# ============ Swap Spread 数据 ============

def fetch_swap_spread_fred(series_id: str = "DSWP3") -> Optional[Dict]:
    """
    从FRED获取Swap Spread数据
    
    FRED Swap Spread序列:
    - DSWP3: 3-Year Swap Spread
    - DSWP5: 5-Year Swap Spread
    - DSWP10: 10-Year Swap Spread
    
    返回: {value: 当前值, change: 变化, date: 日期}
    """
    cache_key = f"swap_spread_{series_id}"
    cached = get_from_cache(cache_key, 300)
    if cached:
        return cached
    
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": 10,  # 获取最近10个数据点
            "sort_order": "desc"
        }
        
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if "observations" not in data:
            return {"error": "No data from FRED", "series": series_id}
        
        obs = data["observations"]
        current = float(obs[0]["value"]) if obs[0]["value"] != "." else None
        prev = float(obs[1]["value"]) if len(obs) > 1 and obs[1]["value"] != "." else None
        
        result = {
            "series": series_id,
            "value": current,
            "prev_value": prev,
            "change": current - prev if current and prev else None,
            "date": obs[0]["date"],
            "unit": "basis points",
            "source": "FRED"
        }
        
        save_to_cache(cache_key, result)
        return result
        
    except Exception as e:
        return {"error": str(e), "series": series_id}

def calculate_swap_spread_risk(spread_data: Dict) -> Dict:
    """
    根据锦成盛框架计算Swap Spread风险等级
    
    阈值（基于锦成盛文档）：
    - 正常: > -20bp
    - 警戒: -20bp 到 -30bp
    - 危险: -30bp 到 -40bp
    - 紧急: < -40bp (如2025年4月跌破-36bp)
    """
    if "error" in spread_data or spread_data.get("value") is None:
        return {"level": "unknown", "status": "数据不可用"}
    
    value = spread_data["value"]
    change = spread_data.get("change", 0)
    
    # 风险等级判定
    if value > -20:
        level = "normal"
        status = "正常"
        color = "green"
    elif value > -30:
        level = "warning"
        status = "警戒"
        color = "yellow"
    elif value > -40:
        level = "danger"
        status = "危险"
        color = "orange"
    else:
        level = "critical"
        status = "紧急"
        color = "red"
    
    # 急剧变化加分
    if change and change < -5:  # 单日下降超过5bp
        urgency = "急剧恶化"
        level = "critical" if level != "critical" else level
    else:
        urgency = "平稳"
    
    return {
        "level": level,
        "status": status,
        "color": color,
        "urgency": urgency,
        "interpretation": f"Dealer压力{'较大' if value < -30 else '适中'}, {urgency}"
    }

# ============ VIX 波动率 ============

def fetch_vix_yahoo() -> Optional[Dict]:
    """从Yahoo Finance获取VIX数据（模拟数据，实际需要API）"""
    cache_key = "vix"
    cached = get_from_cache(cache_key, 60)
    if cached:
        return cached
    
    try:
        # Yahoo Finance VIX
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
        params = {"interval": "1d", "range": "5d"}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        result = data["chart"]["result"][0]
        meta = result["meta"]
        quotes = result["indicators"]["quote"][0]
        
        current = meta.get("regularMarketPrice")
        prev_close = quotes["close"][-2] if len(quotes["close"]) > 1 else None
        
        result_data = {
            "value": current,
            "prev_value": prev_close,
            "change": current - prev_close if current and prev_close else None,
            "change_pct": (current - prev_close) / prev_close * 100 if current and prev_close else None,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "Yahoo Finance"
        }
        
        save_to_cache(cache_key, result_data)
        return result_data
        
    except Exception as e:
        # 返回模拟数据作为后备
        return {
            "value": None,
            "error": str(e),
            "source": "Yahoo Finance",
            "note": "实际部署时需要配置可靠数据源"
        }

def calculate_vix_risk(vix_data: Dict) -> Dict:
    """
    VIX风险等级
    
    阈值：
    - 正常: < 15
    - 警戒: 15-20
    - 危险: 20-30
    - 紧急: > 30
    """
    if vix_data.get("value") is None:
        return {"level": "unknown", "status": "数据不可用"}
    
    value = vix_data["value"]
    
    if value < 15:
        level = "normal"
        status = "平静"
        color = "green"
    elif value < 20:
        level = "warning"
        status = "略高"
        color = "yellow"
    elif value < 30:
        level = "danger"
        status = "恐慌"
        color = "orange"
    else:
        level = "critical"
        status = "极端恐慌"
        color = "red"
    
    return {
        "level": level,
        "status": status,
        "color": color,
        "interpretation": f"市场波动{'正常' if value < 20 else '较高'}"
    }

# ============ 货币基差 (EUR/JPY Cross Currency Basis) ============

def fetch_cross_currency_basis() -> Dict:
    """
    获取EUR/JPY对美元的货币基差
    
    注意：此数据较难免费获取，实际部署需要：
    1. Bloomberg Terminal
    2. Refinitiv
    3. 或使用ICE/BIS的公开数据
    
    这里提供模拟数据框架
    """
    cache_key = "ccy_basis"
    cached = get_from_cache(cache_key, 300)
    if cached:
        return cached
    
    # 模拟数据 - 实际需要真实数据源
    result = {
        "eur_usd_basis": {
            "value": None,
            "note": "需要Bloomberg/Refinitiv数据源",
            "source": "待配置"
        },
        "jpy_usd_basis": {
            "value": None,
            "note": "需要Bloomberg/Refinitiv数据源",
            "source": "待配置"
        },
        "date": datetime.now().strftime("%Y-%m-%d"),
        "warning": "货币基差数据需要付费数据源"
    }
    
    save_to_cache(cache_key, result)
    return result

def calculate_ccy_basis_risk(basis_data: Dict) -> Dict:
    """
    货币基差风险等级（锦成盛框架核心）
    
    关键判断：
    - 基差平稳 = 流动性危机（可恢复）
    - 基差急剧恶化 = 系统性危机（需救助）
    """
    eur = basis_data.get("eur_usd_basis", {}).get("value")
    jpy = basis_data.get("jpy_usd_basis", {}).get("value")
    
    if eur is None or jpy is None:
        return {
            "level": "unknown",
            "status": "数据不可用",
            "note": "货币基差是区分流动性危机vs系统性危机的关键指标",
            "interpretation": "无法判断危机类型"
        }
    
    # 风险判断逻辑
    # 负值加深 = 美元融资紧张
    if eur > -20 and jpy > -30:
        level = "normal"
        status = "平稳"
        crisis_type = "无危机迹象"
    elif eur > -50 and jpy > -70:
        level = "warning"
        status = "小幅紧张"
        crisis_type = "流动性紧张（可恢复）"
    else:
        level = "critical"
        status = "严重恶化"
        crisis_type = "系统性风险（需央行干预）"
    
    return {
        "level": level,
        "status": status,
        "crisis_type": crisis_type,
        "interpretation": f"离岸美元流动性{'充裕' if level == 'normal' else '紧张'}"
    }

# ============ 综合危机评估 ============

def calculate_overall_crisis_level(
    swap_spread_risk: Dict,
    vix_risk: Dict,
    ccy_basis_risk: Dict
) -> Dict:
    """
    综合危机等级评估
    
    基于锦成盛框架的核心判断逻辑：
    1. Swap Spread = Dealer压力（早期预警）
    2. 货币基差 = 危机类型判断（核心）
    3. VIX = 市场情绪
    
    判断优先级：货币基差 > Swap Spread > VIX
    """
    
    # 权重
    weights = {
        "swap_spread": 0.35,  # Dealer压力
        "ccy_basis": 0.40,    # 核心判断
        "vix": 0.25           # 市场情绪
    }
    
    # 分数转换
    level_scores = {
        "normal": 0,
        "warning": 1,
        "danger": 2,
        "critical": 3,
        "unknown": 1  # 未知数据取中间值
    }
    
    ss_score = level_scores.get(swap_spread_risk.get("level", "unknown"), 1)
    vix_score = level_scores.get(vix_risk.get("level", "unknown"), 1)
    ccy_score = level_scores.get(ccy_basis_risk.get("level", "unknown"), 1)
    
    # 加权平均
    total_score = (
        ss_score * weights["swap_spread"] +
        ccy_score * weights["ccy_basis"] +
        vix_score * weights["vix"]
    )
    
    # 综合等级
    if total_score < 0.5:
        level = "normal"
        status = "正常"
        color = "green"
        advice = "市场运行正常，可正常操作"
    elif total_score < 1.2:
        level = "warning"
        status = "警戒"
        color = "yellow"
        advice = "市场有压力迹象，需密切关注"
    elif total_score < 2.0:
        level = "danger"
        status = "危险"
        color = "orange"
        advice = "危机信号明显，建议降低仓位"
    else:
        level = "critical"
        status = "紧急"
        color = "red"
        advice = "系统性风险可能，建议避险"
    
    # 危机类型判断（基于货币基差）
    crisis_type = ccy_basis_risk.get("crisis_type", "无法判断")
    
    return {
        "level": level,
        "status": status,
        "color": color,
        "score": round(total_score, 2),
        "crisis_type": crisis_type,
        "advice": advice,
        "components": {
            "swap_spread": {
                "weight": weights["swap_spread"],
                "score": ss_score,
                "risk": swap_spread_risk
            },
            "ccy_basis": {
                "weight": weights["ccy_basis"],
                "score": ccy_score,
                "risk": ccy_basis_risk
            },
            "vix": {
                "weight": weights["vix"],
                "score": vix_score,
                "risk": vix_risk
            }
        }
    }

# ============ 主数据获取函数 ============

def fetch_all_indicators() -> Dict:
    """获取所有监测指标"""
    
    # 获取原始数据
    swap_spread_3y = fetch_swap_spread_fred("DSWP3")
    swap_spread_5y = fetch_swap_spread_fred("DSWP5")
    vix = fetch_vix_yahoo()
    ccy_basis = fetch_cross_currency_basis()
    
    # 计算风险等级
    ss_3y_risk = calculate_swap_spread_risk(swap_spread_3y)
    ss_5y_risk = calculate_swap_spread_risk(swap_spread_5y)
    vix_risk = calculate_vix_risk(vix)
    ccy_basis_risk = calculate_ccy_basis_risk(ccy_basis)
    
    # 综合评估
    overall = calculate_overall_crisis_level(ss_3y_risk, vix_risk, ccy_basis_risk)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "swap_spread": {
            "3y": {
                "data": swap_spread_3y,
                "risk": ss_3y_risk
            },
            "5y": {
                "data": swap_spread_5y,
                "risk": ss_5y_risk
            }
        },
        "vix": {
            "data": vix,
            "risk": vix_risk
        },
        "cross_currency_basis": {
            "data": ccy_basis,
            "risk": ccy_basis_risk
        },
        "overall": overall,
        "framework": "锦成盛危机监测框架 (2024.07-2026.01)"
    }

# ============ 测试 ============

if __name__ == "__main__":
    print("=" * 60)
    print("锦成盛危机监测系统 - 数据获取测试")
    print("=" * 60)
    
    data = fetch_all_indicators()
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))