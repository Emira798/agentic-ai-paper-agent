"""
基础测试文件，确保CI能够正常运行
"""

def test_import_main():
    """测试能否导入主模块"""
    try:
        import main
        assert main is not None
    except ImportError as e:
        raise AssertionError(f"无法导入main模块: {e}")

def test_import_agents():
    """测试能否导入agents模块"""
    try:
        from src import agents
        assert agents is not None
    except ImportError as e:
        raise AssertionError(f"无法导入agents模块: {e}")

def test_import_planning():
    """测试能否导入planning_agent模块"""
    try:
        from src import planning_agent
        assert planning_agent is not None
    except ImportError as e:
        raise AssertionError(f"无法导入planning_agent模块: {e}")

def test_import_research_tools():
    """测试能否导入research_tools模块"""
    try:
        from src import research_tools
        assert research_tools is not None
    except ImportError as e:
        raise AssertionError(f"无法导入research_tools模块: {e}")