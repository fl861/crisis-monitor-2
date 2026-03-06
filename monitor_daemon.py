#!/usr/bin/env python3
"""
锦成盛危机监测系统 - 后端监控服务
自动获取数据并报警
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
import sys
import os

# ============ 配置 ============

# FRED API Key (免费注册: https://fred.stlouisfed.org/docs/api/api_key.html)
FRED_API_KEY = os.environ.get('FRED_API_KEY', 'YOUR_FRED_API_KEY')

# 飞书 Webhook URL (用于报警通知)
FEISHU_WEBHOOK = os.environ.get('FEISHU_WEBHOOK', '')

# 报警阈值配置
ALERT_THRESHOLDS = {
    'swap_spread_3y': {
        'warning': -25,    # 警戒
        'danger': -35,     # 危险
        'critical': -40,   # 紧急
    },
    'swap_spread_5y': {
        'warning': -25,
        'danger': -35,
        'critical': -40,
    },
    'vix': {
        'warning': 18,
        'danger': 25,
        'critical': 35,
    }
}

# 状态缓存（用于检测状态变化）
last_status = {
    'swap_spread_3y': None,
    'swap_spread_5y': None,
    'vix': None,
    'overall': None
}

# ============ 数据获取 ============

def fetch_fred_series(series_id: str) -> Optional[Dict]:
    """从FRED获取数据"""
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": 5,
            "sort_order": "desc"
        }
        
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        
        if "observations" not in data or len(data["observations"]) == 0:
            return None
            
        obs = data["observations"]
        current = float(obs[0]["value"]) if obs[0]["value"] != "." else None
        prev = float(obs[1]["value"]) if len(obs) > 1 and obs[1]["value"] != "." else None
        
        return {
            "value": current,
            "prev_value": prev,
            "change": current - prev if current and prev else None,
            "date": obs[0]["date"]
        }
    except Exception as e:
        print(f"❌ FRED API错误 ({series_id}): {e}")
        return None

def fetch_vix() -> Optional[Dict]:
    """获取VIX数据"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
        params = {"interval": "1d", "range": "5d"}
        headers = {"User-Agent": "Mozilla/5.0"}
        
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        if data.get("chart", {}).get("result"):
            result = data["chart"]["result"][0]
            meta = result.get("meta", {})
            return {
                "value": meta.get("regularMarketPrice"),
                "prev_close": meta.get("chartPreviousClose"),
                "date": datetime.now().strftime("%Y-%m-%d")
            }
    except Exception as e:
        print(f"❌ VIX获取错误: {e}")
    return None

# ============ 风险计算 ============

def calc_swap_spread_risk(value: float) -> Tuple[str, str]:
    """计算Swap Spread风险等级"""
    if value is None:
        return 'unknown', '数据不可用'
    if value > -20:
        return 'normal', '正常'
    elif value > -30:
        return 'warning', '警戒'
    elif value > -40:
        return 'danger', '危险'
    else:
        return 'critical', '紧急'

def calc_vix_risk(value: float) -> Tuple[str, str]:
    """计算VIX风险等级"""
    if value is None:
        return 'unknown', '数据不可用'
    if value < 15:
        return 'normal', '平静'
    elif value < 20:
        return 'warning', '略高'
    elif value < 30:
        return 'danger', '恐慌'
    else:
        return 'critical', '极端恐慌'

def calc_overall_risk(ss_risk: str, vix_risk: str) -> Tuple[str, str, str]:
    """综合风险评估"""
    scores = {'normal': 0, 'warning': 1, 'danger': 2, 'critical': 3, 'unknown': 1}
    weights = {'ss': 0.55, 'vix': 0.45}
    
    score = scores.get(ss_risk, 1) * weights['ss'] + scores.get(vix_risk, 1) * weights['vix']
    
    if score < 0.5:
        return 'normal', '正常', '市场运行正常'
    elif score < 1.2:
        return 'warning', '警戒', '市场有压力迹象'
    elif score < 2.0:
        return 'danger', '危险', '危机信号明显'
    else:
        return 'critical', '紧急', '系统性风险可能'

# ============ 通知发送 ============

def send_feishu_alert(title: str, content: str, level: str = 'info'):
    """发送飞书通知"""
    if not FEISHU_WEBHOOK:
        print("⚠️ 未配置飞书Webhook，跳过通知")
        return False
    
    # 颜色映射
    color_map = {
        'normal': 'green',
        'warning': 'yellow', 
        'danger': 'orange',
        'critical': 'red',
        'info': 'blue'
    }
    
    # 构建消息卡片
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color_map.get(level, 'blue')
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": content}
                },
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                }
            ]
        }
    }
    
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=card, timeout=10)
        result = resp.json()
        if result.get('StatusCode') == 0:
            print(f"✅ 飞书通知发送成功: {title}")
            return True
        else:
            print(f"❌ 飞书通知失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 发送飞书通知错误: {e}")
        return False

def format_alert_message(ss3y_data: Dict, ss5y_data: Dict, vix_data: Dict, 
                         ss3y_risk: str, vix_risk: str, overall_risk: str) -> str:
    """格式化报警消息"""
    lines = ["## 🚨 锦成盛危机监测警报\n"]
    
    # Swap Spread
    if ss3y_data and ss3y_data.get('value'):
        lines.append(f"**Swap Spread (3Y)**: {ss3y_data['value']:.1f} bp")
        if ss3y_data.get('change'):
            lines.append(f"- 变化: {ss3y_data['change']:+.2f} bp")
        lines.append(f"- 状态: **{ss3y_risk[1]}**\n")
    
    # VIX
    if vix_data and vix_data.get('value'):
        lines.append(f"**VIX**: {vix_data['value']:.1f}")
        if vix_data.get('prev_close'):
            change = vix_data['value'] - vix_data['prev_close']
            lines.append(f"- 变化: {change:+.2f}")
        lines.append(f"- 状态: **{vix_risk[1]}**\n")
    
    # 综合评估
    lines.append(f"---\n**综合评估**: {overall_risk[1]} ({overall_risk[2]})")
    
    return '\n'.join(lines)

# ============ 主监控循环 ============

def check_and_alert():
    """检查数据并发送警报"""
    print(f"\n{'='*50}")
    print(f"🔍 锦成盛危机监测 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # 获取数据
    ss3y_data = fetch_fred_series('DSWP3')
    ss5y_data = fetch_fred_series('DSWP5')
    vix_data = fetch_vix()
    
    # 计算风险
    ss3y_risk = calc_swap_spread_risk(ss3y_data['value'] if ss3y_data else None)
    vix_risk = calc_vix_risk(vix_data['value'] if vix_data else None)
    overall_risk = calc_overall_risk(ss3y_risk[0], vix_risk[0])
    
    # 打印状态
    print(f"\n📊 监测数据:")
    if ss3y_data:
        print(f"  Swap Spread 3Y: {ss3y_data['value']:.1f} bp [{ss3y_risk[1]}]")
    if vix_data:
        print(f"  VIX: {vix_data['value']:.1f} [{vix_risk[1]}]")
    print(f"\n  综合评估: {overall_risk[1]} - {overall_risk[2]}")
    
    # 检测状态变化
    status_changed = False
    alert_needed = False
    
    # 检查是否需要报警
    if ss3y_risk[0] in ['danger', 'critical'] and last_status['swap_spread_3y'] != ss3y_risk[0]:
        alert_needed = True
        status_changed = True
        print(f"  ⚠️ Swap Spread状态变化: {last_status['swap_spread_3y']} → {ss3y_risk[0]}")
    
    if vix_risk[0] in ['danger', 'critical'] and last_status['vix'] != vix_risk[0]:
        alert_needed = True
        status_changed = True
        print(f"  ⚠️ VIX状态变化: {last_status['vix']} → {vix_risk[0]}")
    
    if overall_risk[0] in ['danger', 'critical'] and last_status['overall'] != overall_risk[0]:
        alert_needed = True
        status_changed = True
        print(f"  ⚠️ 综合状态变化: {last_status['overall']} → {overall_risk[0]}")
    
    # 发送警报
    if alert_needed:
        message = format_alert_message(ss3y_data, ss5y_data, vix_data, ss3y_risk, vix_risk, overall_risk)
        send_feishu_alert(
            f"🚨 危机监测警报 [{overall_risk[1]}]",
            message,
            overall_risk[0]
        )
    
    # 更新状态缓存
    last_status['swap_spread_3y'] = ss3y_risk[0]
    last_status['swap_spread_5y'] = calc_swap_spread_risk(ss5y_data['value'] if ss5y_data else None)[0]
    last_status['vix'] = vix_risk[0]
    last_status['overall'] = overall_risk[0]
    
    # 保存数据到文件
    save_data_to_file(ss3y_data, ss5y_data, vix_data, ss3y_risk, vix_risk, overall_risk)
    
    return {
        'ss3y': ss3y_data,
        'vix': vix_data,
        'risk': {
            'ss3y': ss3y_risk,
            'vix': vix_risk,
            'overall': overall_risk
        }
    }

def save_data_to_file(ss3y_data, ss5y_data, vix_data, ss3y_risk, vix_risk, overall_risk):
    """保存数据到JSON文件供前端使用"""
    data = {
        'timestamp': datetime.now().isoformat(),
        'swap_spread': {
            '3y': {
                'data': ss3y_data,
                'risk': {'level': ss3y_risk[0], 'status': ss3y_risk[1]}
            },
            '5y': {
                'data': ss5y_data,
                'risk': {'level': calc_swap_spread_risk(ss5y_data['value'] if ss5y_data else None)[0]}
            }
        },
        'vix': {
            'data': vix_data,
            'risk': {'level': vix_risk[0], 'status': vix_risk[1]}
        },
        'overall': {
            'level': overall_risk[0],
            'status': overall_risk[1],
            'advice': overall_risk[2]
        }
    }
    
    # 保存到文件
    output_file = '/home/admin/.openclaw/workspace/crisis_monitor/data.json'
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✅ 数据已保存到: {output_file}")

# ============ 主函数 ============

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='锦成盛危机监测系统')
    parser.add_argument('--webhook', type=str, help='飞书Webhook URL')
    parser.add_argument('--fred-key', type=str, help='FRED API Key')
    parser.add_argument('--daemon', action='store_true', help='持续监控模式')
    parser.add_argument('--interval', type=int, default=300, help='监控间隔(秒)')
    
    args = parser.parse_args()
    
    # 设置配置
    if args.webhook:
        FEISHU_WEBHOOK = args.webhook
    if args.fred_key:
        FRED_API_KEY = args.fred_key
    
    if args.daemon:
        print("🚀 启动持续监控模式...")
        print(f"⏱️ 检查间隔: {args.interval}秒")
        while True:
            try:
                check_and_alert()
            except Exception as e:
                print(f"❌ 监控错误: {e}")
            time.sleep(args.interval)
    else:
        # 单次检查
        check_and_alert()