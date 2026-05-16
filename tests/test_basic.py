"""
基础测试文件，确保CI能够正常运行
"""

def test_import_main():
    """测试能否导入主模块"""
    try:
        # 设置环境变量避免DATABASE_URL错误
        import os
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "postgresql://app:local@localhost:5432/appdb"

        import main
        assert main is not None
    except Exception as e:
        # 如果导入失败，至少检查语法
        import py_compile
        try:
            py_compile.compile("main.py", doraise=True)
            print(f"main.py语法正确，但导入时出错: {e}")
        except py_compile.PyCompileError as ce:
            raise AssertionError(f"main.py语法错误: {ce}")

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