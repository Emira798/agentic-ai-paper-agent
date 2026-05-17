"""
测试配置文件
用于配置测试环境和 API 使用限制
"""

import pytest
import os


def pytest_configure(config):
    """配置测试环境"""
    # 设置测试环境变量
    os.environ["TESTING"] = "true"

    # 限制 API 使用以避免过高成本
    os.environ["MAX_TOKENS_TEST"] = "500"  # 测试时最大 token 数
    os.environ["TEMPERATURE_TEST"] = "0.1"  # 测试时低温以确保一致性


@pytest.fixture(autouse=True)
def setup_test_env():
    """为每个测试设置环境"""
    # 保存原始环境变量
    original_env = {
        "DASHSCOPE_API_KEY": os.environ.get("DASHSCOPE_API_KEY"),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY"),
        "DASHSCOPE_BASE_URL": os.environ.get("DASHSCOPE_BASE_URL"),
    }

    yield

    # 测试完成后恢复环境变量（如果需要）
    # 这里我们不需要恢复，因为每个测试都是独立的


def pytest_collection_modifyitems(config, items):
    """修改测试收集，跳过标记为高成本的测试"""
    # 如果环境变量指示跳过高成本测试
    if os.environ.get("SKIP_EXPENSIVE_TESTS", "").lower() == "true":
        skip_expensive = pytest.mark.skip(reason="跳过高成本 API 测试")
        for item in items:
            if "expensive" in item.keywords:
                item.add_marker(skip_expensive)


# 测试数据库配置
@pytest.fixture(scope="session")
def test_database_url():
    """测试数据库 URL"""
    return "sqlite:///:memory:"


# API 限制配置
@pytest.fixture
def api_limits():
    """API 使用限制配置"""
    return {
        "max_tokens": int(os.environ.get("MAX_TOKENS_TEST", "500")),
        "temperature": float(os.environ.get("TEMPERATURE_TEST", "0.1")),
        "max_retries": 1,  # 测试时减少重试次数
        "timeout": 30,     # 30秒超时
    }