# -*- coding: utf-8 -*-
"""
测试 app.py 主程序
确保配置正确加载，避免 NameError
"""
import pytest
import os
import sys

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def test_app_imports():
    """测试 app.py 的基本导入不会出错"""
    try:
        # 测试导入关键模块
        from utils.log_manager import add_log, clear_logs
        from utils.session_manager import init_session_state, connect_database, get_statistics
        from utils.crawler_status import set_crawler_running, is_crawler_running, check_and_fix_crawler_status
        from utils.config_loader import load_config
        
        assert True, "所有导入成功"
    except ImportError as e:
        pytest.fail(f"导入失败: {e}")


def test_config_loaded_globally():
    """测试配置在全局作用域正确加载"""
    # 读取 app.py 文件内容
    app_path = os.path.join(PROJECT_ROOT, 'app.py')
    
    with open(app_path, 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    # 检查是否导入了 load_config
    assert 'from utils.config_loader import load_config' in app_content, \
        "app.py 必须导入 load_config"
    
    # 检查是否在全局作用域加载了 config
    # 查找 "config = load_config()" 且不在函数内部
    lines = app_content.split('\n')
    found_global_config = False
    in_function = False
    
    for i, line in enumerate(lines):
        # 检测函数定义
        if line.strip().startswith('def '):
            in_function = True
        # 检测函数结束（下一个非缩进行）
        elif in_function and line and not line[0].isspace():
            in_function = False
        
        # 查找 config = load_config()
        if 'config = load_config()' in line and not in_function:
            found_global_config = True
            break
    
    assert found_global_config, \
        "app.py 必须在全局作用域加载 config (config = load_config())"


def test_config_variable_accessible():
    """测试 config 变量可以被访问"""
    from utils.config_loader import load_config
    
    # 模拟 app.py 的全局配置加载
    config = load_config()
    
    # 验证 config 是字典
    assert isinstance(config, dict), "config 应该是字典类型"
    
    # 验证包含必要的配置项
    assert 'github' in config, "config 必须包含 github 配置"
    
    github_config = config.get('github', {})
    assert 'max_developers_per_run' in github_config, \
        "github 配置必须包含 max_developers_per_run"
    assert 'min_repo_stars' in github_config, \
        "github 配置必须包含 min_repo_stars"


def test_render_github_crawler_signature():
    """测试 render_github_crawler 函数签名包含 config 参数"""
    app_path = os.path.join(PROJECT_ROOT, 'app.py')
    
    with open(app_path, 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    # 查找 render_github_crawler 函数
    assert 'def render_github_crawler():' in app_content, \
        "必须有 render_github_crawler 函数"
    
    # 查找函数内部是否调用了 render_crawler 并传递 config
    # 提取函数内容
    lines = app_content.split('\n')
    in_function = False
    function_content = []
    
    for line in lines:
        if 'def render_github_crawler():' in line:
            in_function = True
            continue
        
        if in_function:
            # 遇到下一个函数定义，停止
            if line.strip().startswith('def ') and not line.strip().startswith('def render_github_crawler'):
                break
            function_content.append(line)
    
    function_text = '\n'.join(function_content)
    
    # 检查是否传递了 config 参数
    assert 'config=config' in function_text, \
        "render_github_crawler 必须传递 config 参数给 render_crawler"


def test_app_syntax():
    """测试 app.py 语法正确"""
    import py_compile
    
    app_path = os.path.join(PROJECT_ROOT, 'app.py')
    
    try:
        py_compile.compile(app_path, doraise=True)
    except py_compile.PyCompileError as e:
        pytest.fail(f"app.py 语法错误: {e}")


def test_no_undefined_config_usage():
    """测试 app.py 中没有未定义就使用 config 的情况"""
    app_path = os.path.join(PROJECT_ROOT, 'app.py')
    
    with open(app_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    config_defined = False
    config_used_before_definition = False
    problematic_line = None
    
    for i, line in enumerate(lines, 1):
        # 检查是否定义了 config
        if 'config = load_config()' in line and not line.strip().startswith('#'):
            config_defined = True
        
        # 检查是否在定义前使用了 config
        if not config_defined and 'config=' in line and 'config=config' in line:
            # 这是在函数调用中传递 config 参数
            if not line.strip().startswith('#'):
                config_used_before_definition = True
                problematic_line = i
                break
    
    assert not config_used_before_definition, \
        f"app.py 第 {problematic_line} 行在定义前使用了 config 变量"


def test_config_passed_to_github_crawler():
    """测试 config 正确传递给 GitHub 爬虫 UI"""
    app_path = os.path.join(PROJECT_ROOT, 'app.py')
    
    with open(app_path, 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    # 查找 render_github_crawler 函数
    assert 'def render_github_crawler():' in app_content, \
        "必须有 render_github_crawler 函数"
    
    # 查找 render_crawler 调用
    assert 'render_crawler(' in app_content, \
        "render_github_crawler 必须调用 render_crawler"
    
    # 提取 render_github_crawler 函数内容
    lines = app_content.split('\n')
    in_function = False
    function_lines = []
    
    for line in lines:
        if 'def render_github_crawler():' in line:
            in_function = True
            continue
        
        if in_function:
            # 遇到下一个函数定义，停止
            if line.strip().startswith('def ') and 'render_github_crawler' not in line:
                break
            function_lines.append(line)
    
    function_text = '\n'.join(function_lines)
    
    # 验证传递了 config 参数
    assert 'config=config' in function_text, \
        "render_github_crawler 必须传递 config=config 参数给 render_crawler"
    
    print("✓ config 正确传递给 GitHub 爬虫 UI")


if __name__ == "__main__":
    # 直接运行测试
    print("=" * 60)
    print("测试 app.py 配置加载")
    print("=" * 60)
    
    tests = [
        ("基本导入", test_app_imports),
        ("全局配置加载", test_config_loaded_globally),
        ("配置变量可访问", test_config_variable_accessible),
        ("函数签名正确", test_render_github_crawler_signature),
        ("语法正确", test_app_syntax),
        ("无未定义使用", test_no_undefined_config_usage),
        ("config传递给爬虫UI", test_config_passed_to_github_crawler),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n测试: {name}")
            test_func()
            print(f"  ✓ 通过")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
