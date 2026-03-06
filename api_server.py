#!/usr/bin/env python3
"""
锦成盛危机监测系统 - API服务器
提供REST API供前端调用
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_data import fetch_all_indicators

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# ============ API路由 ============

@app.route('/')
def index():
    """重定向到监控页面"""
    return '''
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/monitor">
    </head>
    <body>
        <p>正在跳转到危机监测系统...</p>
    </body>
    </html>
    '''

@app.route('/api/indicators')
def get_indicators():
    """获取所有监测指标数据"""
    try:
        data = fetch_all_indicators()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/swap_spread')
def get_swap_spread():
    """获取Swap Spread数据"""
    from fetch_data import fetch_swap_spread_fred, calculate_swap_spread_risk
    
    series = request.args.get('series', 'DSWP3')
    data = fetch_swap_spread_fred(series)
    risk = calculate_swap_spread_risk(data)
    
    return jsonify({
        "data": data,
        "risk": risk
    })

@app.route('/api/vix')
def get_vix():
    """获取VIX数据"""
    from fetch_data import fetch_vix_yahoo, calculate_vix_risk
    
    data = fetch_vix_yahoo()
    risk = calculate_vix_risk(data)
    
    return jsonify({
        "data": data,
        "risk": risk
    })

@app.route('/api/crisis_level')
def get_crisis_level():
    """获取综合危机等级"""
    try:
        data = fetch_all_indicators()
        return jsonify(data["overall"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "锦成盛危机监测系统"
    })

# ============ 监控页面 ============

@app.route('/monitor')
def monitor_page():
    """返回监控页面HTML"""
    return MONITOR_HTML

# ============ HTML模板 ============

MONITOR_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>锦成盛危机监测系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            color: #888;
            font-size: 0.9em;
        }
        
        .update-time {
            margin-top: 10px;
            font-size: 0.85em;
            color: #666;
        }
        
        /* 危机等级大卡片 */
        .crisis-level-card {
            background: rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            text-align: center;
            border: 2px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }
        
        .crisis-level-card.normal { border-color: #00ff88; box-shadow: 0 0 30px rgba(0,255,136,0.2); }
        .crisis-level-card.warning { border-color: #ffcc00; box-shadow: 0 0 30px rgba(255,204,0,0.2); }
        .crisis-level-card.danger { border-color: #ff8800; box-shadow: 0 0 30px rgba(255,136,0,0.3); }
        .crisis-level-card.critical { border-color: #ff0044; box-shadow: 0 0 30px rgba(255,0,68,0.4); }
        
        .crisis-status {
            font-size: 4em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .crisis-status.normal { color: #00ff88; }
        .crisis-status.warning { color: #ffcc00; }
        .crisis-status.danger { color: #ff8800; }
        .crisis-status.critical { color: #ff0044; }
        
        .crisis-type {
            font-size: 1.2em;
            color: #aaa;
            margin-bottom: 20px;
        }
        
        .crisis-advice {
            background: rgba(0,0,0,0.3);
            padding: 15px 25px;
            border-radius: 10px;
            font-size: 1.1em;
        }
        
        /* 指标网格 */
        .indicators-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .indicator-card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            border-left: 4px solid #444;
            transition: all 0.3s ease;
        }
        
        .indicator-card.normal { border-left-color: #00ff88; }
        .indicator-card.warning { border-left-color: #ffcc00; }
        .indicator-card.danger { border-left-color: #ff8800; }
        .indicator-card.critical { border-left-color: #ff0044; }
        
        .indicator-title {
            font-size: 0.9em;
            color: #888;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .indicator-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .indicator-change {
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .indicator-change.positive { color: #00ff88; }
        .indicator-change.negative { color: #ff4444; }
        
        .indicator-status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }
        
        .indicator-status.normal { background: rgba(0,255,136,0.2); color: #00ff88; }
        .indicator-status.warning { background: rgba(255,204,0,0.2); color: #ffcc00; }
        .indicator-status.danger { background: rgba(255,136,0,0.2); color: #ff8800; }
        .indicator-status.critical { background: rgba(255,0,68,0.2); color: #ff0044; }
        
        .indicator-interpretation {
            margin-top: 15px;
            font-size: 0.85em;
            color: #aaa;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        /* 框架说明 */
        .framework-info {
            background: rgba(255,255,255,0.03);
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
        }
        
        .framework-info h3 {
            margin-bottom: 15px;
            color: #00d4ff;
        }
        
        .framework-info ul {
            list-style: none;
            padding-left: 0;
        }
        
        .framework-info li {
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .framework-info li:last-child {
            border-bottom: none;
        }
        
        /* 刷新按钮 */
        .refresh-btn {
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            border: none;
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-top: 20px;
        }
        
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,212,255,0.3);
        }
        
        .refresh-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* 加载动画 */
        .loading {
            text-align: center;
            padding: 50px;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #00d4ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* 响应式 */
        @media (max-width: 768px) {
            h1 { font-size: 1.8em; }
            .crisis-status { font-size: 2.5em; }
            .indicator-value { font-size: 2em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚨 锦成盛危机监测系统</h1>
            <p class="subtitle">基于锦成盛资管危机监测框架 (2024.07-2026.01)</p>
            <p class="update-time">最后更新: <span id="updateTime">加载中...</span></p>
        </header>
        
        <!-- 危机等级大卡片 -->
        <div id="crisisCard" class="crisis-level-card loading">
            <div class="spinner"></div>
            <p>正在获取数据...</p>
        </div>
        
        <!-- 指标网格 -->
        <div class="indicators-grid">
            <!-- Swap Spread 3Y -->
            <div id="swapSpread3yCard" class="indicator-card">
                <div class="indicator-title">Swap Spread (3Y)</div>
                <div class="indicator-value" id="ss3yValue">--</div>
                <div class="indicator-change" id="ss3yChange">--</div>
                <span class="indicator-status" id="ss3yStatus">--</span>
                <div class="indicator-interpretation" id="ss3yInterpretation">--</div>
            </div>
            
            <!-- Swap Spread 5Y -->
            <div id="swapSpread5yCard" class="indicator-card">
                <div class="indicator-title">Swap Spread (5Y)</div>
                <div class="indicator-value" id="ss5yValue">--</div>
                <div class="indicator-change" id="ss5yChange">--</div>
                <span class="indicator-status" id="ss5yStatus">--</span>
                <div class="indicator-interpretation" id="ss5yInterpretation">--</div>
            </div>
            
            <!-- VIX -->
            <div id="vixCard" class="indicator-card">
                <div class="indicator-title">VIX 波动率指数</div>
                <div class="indicator-value" id="vixValue">--</div>
                <div class="indicator-change" id="vixChange">--</div>
                <span class="indicator-status" id="vixStatus">--</span>
                <div class="indicator-interpretation" id="vixInterpretation">--</div>
            </div>
            
            <!-- 货币基差 -->
            <div id="ccyBasisCard" class="indicator-card">
                <div class="indicator-title">货币基差 (EUR/JPY)</div>
                <div class="indicator-value" id="ccyBasisValue">--</div>
                <div class="indicator-change" id="ccyBasisChange">--</div>
                <span class="indicator-status" id="ccyBasisStatus">--</span>
                <div class="indicator-interpretation" id="ccyBasisInterpretation">--</div>
            </div>
        </div>
        
        <!-- 框架说明 -->
        <div class="framework-info">
            <h3>📊 锦成盛危机监测框架</h3>
            <ul>
                <li><strong>Swap Spread</strong> - Dealer压力温度计，急剧走负（如3Y跌破-36bp）= Dealer躺平</li>
                <li><strong>货币基差 (EUR/JPY)</strong> - 离岸美元流动性，平稳=流动性危机（可恢复），急剧恶化=系统性危机</li>
                <li><strong>VIX</strong> - 市场恐慌情绪，>30=极端恐慌</li>
                <li><strong>危机演进链</strong>: 资产下跌 → 抛售扩散 → 中性策略解盘 → Dealer躺平 → Flight to Quality</li>
            </ul>
            <p style="margin-top: 15px; color: #666; font-size: 0.85em;">
                ⚠️ 核心哲学："从叙事驱动转向机制驱动" — 拒绝宏大故事，从Dealer行为、杠杆链条、资金流向入手
            </p>
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="refreshData()">🔄 刷新数据</button>
        </div>
    </div>
    
    <script>
        // API基础URL
        const API_BASE = window.location.origin;
        
        // 格式化数字
        function formatNumber(num, decimals = 2) {
            if (num === null || num === undefined) return '--';
            return num.toFixed(decimals);
        }
        
        // 更新危机等级卡片
        function updateCrisisCard(overall) {
            const card = document.getElementById('crisisCard');
            card.className = `crisis-level-card ${overall.level}`;
            card.innerHTML = `
                <div class="crisis-status ${overall.level}">${overall.status}</div>
                <div class="crisis-type">${overall.crisis_type || ''}</div>
                <div class="crisis-advice">💡 ${overall.advice}</div>
                <p style="margin-top: 15px; color: #666; font-size: 0.85em;">
                    综合评分: ${overall.score} / 3.0
                </p>
            `;
        }
        
        // 更新指标卡片
        function updateIndicatorCard(prefix, data, risk) {
            const valueEl = document.getElementById(`${prefix}Value`);
            const changeEl = document.getElementById(`${prefix}Change`);
            const statusEl = document.getElementById(`${prefix}Status`);
            const interpEl = document.getElementById(`${prefix}Interpretation`);
            const cardEl = document.getElementById(`${prefix}Card`);
            
            if (data.error) {
                valueEl.textContent = '数据不可用';
                changeEl.textContent = data.error;
                statusEl.textContent = '未知';
                statusEl.className = 'indicator-status warning';
                return;
            }
            
            // 值
            if (prefix === 'ss3y' || prefix === 'ss5y') {
                valueEl.textContent = `${formatNumber(data.value)} bp`;
            } else if (prefix === 'vix') {
                valueEl.textContent = formatNumber(data.value);
            } else {
                valueEl.textContent = data.value ? formatNumber(data.value) : '待配置';
            }
            
            // 变化
            if (data.change !== null && data.change !== undefined) {
                const changeClass = data.change >= 0 ? 'positive' : 'negative';
                const changeSign = data.change >= 0 ? '+' : '';
                changeEl.textContent = `${changeSign}${formatNumber(data.change)}`;
                changeEl.className = `indicator-change ${changeClass}`;
            } else {
                changeEl.textContent = '--';
            }
            
            // 状态
            statusEl.textContent = risk.status;
            statusEl.className = `indicator-status ${risk.level}`;
            
            // 卡片样式
            cardEl.className = `indicator-card ${risk.level}`;
            
            // 解读
            interpEl.textContent = risk.interpretation || '--';
        }
        
        // 获取数据
        async function fetchData() {
            try {
                const response = await fetch(`${API_BASE}/api/indicators`);
                const data = await response.json();
                
                // 更新时间
                document.getElementById('updateTime').textContent = 
                    new Date(data.timestamp).toLocaleString('zh-CN');
                
                // 更新危机等级
                updateCrisisCard(data.overall);
                
                // 更新各指标
                updateIndicatorCard('ss3y', 
                    data.swap_spread['3y'].data, 
                    data.swap_spread['3y'].risk
                );
                updateIndicatorCard('ss5y', 
                    data.swap_spread['5y'].data, 
                    data.swap_spread['5y'].risk
                );
                updateIndicatorCard('vix', 
                    data.vix.data, 
                    data.vix.risk
                );
                updateIndicatorCard('ccyBasis', 
                    data.cross_currency_basis.data, 
                    data.cross_currency_basis.risk
                );
                
            } catch (error) {
                console.error('获取数据失败:', error);
                document.getElementById('crisisCard').innerHTML = `
                    <div style="color: #ff4444;">
                        <p>❌ 数据获取失败</p>
                        <p style="font-size: 0.9em; color: #888;">${error.message}</p>
                    </div>
                `;
            }
        }
        
        // 刷新数据
        function refreshData() {
            const btn = document.querySelector('.refresh-btn');
            btn.disabled = true;
            btn.textContent = '⏳ 刷新中...';
            
            fetchData().finally(() => {
                btn.disabled = false;
                btn.textContent = '🔄 刷新数据';
            });
        }
        
        // 初始加载
        fetchData();
        
        // 自动刷新（每5分钟）
        setInterval(fetchData, 5 * 60 * 1000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("=" * 60)
    print("🚨 锦成盛危机监测系统 - 启动中...")
    print("=" * 60)
    print(f"访问地址: http://localhost:5000/monitor")
    print(f"API地址: http://localhost:5000/api/indicators")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)