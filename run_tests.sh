#!/bin/bash

# 测试运行脚本
# 控制 API 使用和测试执行

echo "=== 开始运行测试 ==="

# 设置测试环境
export TESTING=true
export MAX_TOKENS_TEST=500
export TEMPERATURE_TEST=0.1

# 检查 API 密钥是否存在
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "警告: DASHSCOPE_API_KEY 未设置，将跳过需要 API 的测试"
    export SKIP_EXPENSIVE_TESTS=true
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "警告: TAVILY_API_KEY 未设置，将跳过需要 API 的测试"
fi

echo "环境变量设置:"
echo "- TESTING: $TESTING"
echo "- MAX_TOKENS_TEST: $MAX_TOKENS_TEST"
echo "- SKIP_EXPENSIVE_TESTS: $SKIP_EXPENSIVE_TESTS"

# 运行基础测试（不需要 API）
echo "\n=== 运行基础测试 ==="
python -m pytest tests/test_basic.py tests/test_models.py -v --tb=short

if [ $? -ne 0 ]; then
    echo "基础测试失败！"
    exit 1
fi

# 运行真实 API 测试（如果 API 密钥存在）
if [ -n "$DASHSCOPE_API_KEY" ]; then
    echo "\n=== 运行真实 API 测试 ==="
    python -m pytest tests/test_real_api.py -v --tb=short

    if [ $? -ne 0 ]; then
        echo "真实 API 测试失败！"
        exit 1
    fi
else
    echo "\n=== 跳过真实 API 测试（无 API 密钥） ==="
fi

# 运行覆盖率测试
echo "\n=== 运行覆盖率测试 ==="
python -m pytest tests/test_basic.py tests/test_models.py tests/test_real_api.py \
    --cov=src --cov=main --cov-report=xml --cov-report=html

COVERAGE_RESULT=$?

echo "\n=== 测试完成 ==="

if [ $COVERAGE_RESULT -eq 0 ]; then
    echo "✅ 所有测试通过！"
    echo "📊 覆盖率报告已生成在 htmlcov/ 目录"
    exit 0
else
    echo "❌ 测试失败或覆盖率不足"
    exit 1
fi