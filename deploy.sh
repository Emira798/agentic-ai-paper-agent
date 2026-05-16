#!/bin/bash

# 生产环境部署脚本
set -e

echo "🚀 开始部署多AI智能体论文写作系统..."

# 检查环境变量
if [ -z "${OPENAI_API_KEY}" ]; then
    echo "❌ 错误: OPENAI_API_KEY 环境变量未设置"
    exit 1
fi

if [ -z "${TAVILY_API_KEY}" ]; then
    echo "❌ 错误: TAVILY_API_KEY 环境变量未设置"
    exit 1
fi

# 创建环境变量文件
cat > .env << EOF
OPENAI_API_KEY=${OPENAI_API_KEY}
TAVILY_API_KEY=${TAVILY_API_KEY}
EOF

echo "✅ 环境变量配置完成"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

echo "✅ Docker环境检查通过"

# 停止现有服务（如果存在）
if docker-compose ps | grep -q "Up"; then
    echo "🔄 停止现有服务..."
    docker-compose down
fi

# 构建和启动服务
echo "🔨 构建Docker镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo "✅ 服务启动成功!"
    echo "🌐 应用地址: http://localhost:8000"
    echo "📚 API文档: http://localhost:8000/docs"
else
    echo "❌ 服务启动失败，请检查日志:"
    docker-compose logs
    exit 1
fi

echo "🎉 部署完成!"