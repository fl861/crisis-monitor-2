#!/bin/bash
# 锦成盛危机监测系统 - 定时监控脚本
# 每30分钟检查一次，触发阈值时发送飞书通知

cd "$(dirname "$0")"

# 配置
FRED_API_KEY="${FRED_API_KEY:-}"
FEISHU_WEBHOOK="${FEISHU_WEBHOOK:-}"

# 检查配置
if [ -z "$FRED_API_KEY" ]; then
    echo "❌ 错误: 未设置 FRED_API_KEY 环境变量"
    echo "请运行: export FRED_API_KEY=your_api_key"
    exit 1
fi

if [ -z "$FEISHU_WEBHOOK" ]; then
    echo "⚠️ 警告: 未设置 FEISHU_WEBHOOK，将不会发送飞书通知"
fi

echo "=============================================="
echo "🚨 锦成盛危机监测系统"
echo "=============================================="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 运行监控
python3 monitor_daemon.py \
    --fred-key "$FRED_API_KEY" \
    --webhook "$FEISHU_WEBHOOK"

echo ""
echo "✅ 检查完成"