#!/bin/bash

# Markio 服务启动脚本
# Start script for Markio services

echo "🚀 启动 Markio 服务..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装或不在PATH中"
    exit 1
fi

# 创建输出目录
mkdir -p outputs
mkdir -p logs

# 启动后端API服务
echo "🔧 启动 Markio 后端API服务..."
python3 markio/main.py &
API_PID=$!
echo "✅ 后端API服务已启动 (PID: $API_PID)"

# 等待API服务启动
sleep 3

# 启动Gradio前端
echo "🌐 启动 Markio Gradio前端..."
python3 markio/web/gradio_frontend.py &
FRONTEND_PID=$!
echo "✅ Gradio前端已启动 (PID: $FRONTEND_PID)"


echo "📚 API文档: http://localhost:8000/docs"
echo "🌐 Web界面: http://localhost:7860"
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $API_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
