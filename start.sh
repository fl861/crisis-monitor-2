#!/bin/bash
# 锦成盛危机监测系统 - 启动脚本

cd "$(dirname "$0")"

echo "=============================================="
echo "🚨 锦成盛危机监测系统"
echo "=============================================="
echo ""
echo "正在启动服务..."
echo ""

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ 未找到Python，请先安装Python 3.x"
    exit 1
fi

echo "Python: $($PYTHON --version)"
echo ""

# 启动服务
echo "启动API服务器..."
echo "访问地址: http://localhost:5000/monitor"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=============================================="

$PYTHON api_server.py