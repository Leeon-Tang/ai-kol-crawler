# -*- coding: utf-8 -*-
"""
测试配置修改 - 验证新增的配置项
"""
import pytest
from utils.config_loader import load_config
from platforms.github.searcher import GitHubSearcher


def test_github_config_has_new_fields():
    """测试GitHub配置包含新字段"""
    config = load_config()
    github_config = config.get('github', {})
    
    # 验证新增的配置项存在
    assert 'max_developers_per_run' in github_config, "缺少 max_developers_per_run 配置"
    assert 'min_repo_stars' in github_config, "缺少 min_repo_stars 配置"
    
    # 验证配置值的类型和范围
    max_developers = github_config['max_developers_per_run']
    min_repo_stars = github_config['min_repo_stars']
    
    assert isinstance(max_developers, int), "max_developers_per_run 应该是整数"
    assert isinstance(min_repo_stars, int), "min_repo_stars 应该是整数"
    
    assert 10 <= max_developers <= 1000, "max_developers_per_run 应该在 10-1000 之间"
    assert 0 <= min_repo_stars <= 1000, "min_repo_stars 应该在 0-1000 之间"
    
    print(f"✓ max_developers_per_run: {max_developers}")
    print(f"✓ min_repo_stars: {min_repo_stars}")


def test_searcher_loads_min_repo_stars():
    """测试搜索器正确加载 min_repo_stars 配置"""
    searcher = GitHubSearcher()
    
    # 验证搜索器有 min_repo_stars 属性
    assert hasattr(searcher, 'min_repo_stars'), "搜索器缺少 min_repo_stars 属性"
    
    # 验证值的类型
    assert isinstance(searcher.min_repo_stars, int), "min_repo_stars 应该是整数"
    
    # 验证值在合理范围内
    assert 0 <= searcher.min_repo_stars <= 1000, "min_repo_stars 应该在 0-1000 之间"
    
    print(f"✓ 搜索器的 min_repo_stars: {searcher.min_repo_stars}")


def test_config_default_values():
    """测试配置的默认值在合理范围内"""
    config = load_config()
    github_config = config.get('github', {})
    
    # 验证配置值在合理范围内
    max_developers = github_config.get('max_developers_per_run', 100)
    min_repo_stars = github_config.get('min_repo_stars', 100)
    
    # 验证值的类型和范围（不强制要求具体值）
    assert isinstance(max_developers, int), "max_developers_per_run 应该是整数"
    assert isinstance(min_repo_stars, int), "min_repo_stars 应该是整数"
    assert 10 <= max_developers <= 1000, "max_developers_per_run 应该在 10-1000 之间"
    assert 0 <= min_repo_stars <= 1000, "min_repo_stars 应该在 0-1000 之间"
    
    print(f"✓ 配置值验证通过: max_developers={max_developers}, min_repo_stars={min_repo_stars}")


if __name__ == "__main__":
    # 直接运行测试
    print("=" * 60)
    print("测试配置修改")
    print("=" * 60)
    
    try:
        test_github_config_has_new_fields()
        print("\n✓ 测试1通过: GitHub配置包含新字段\n")
    except AssertionError as e:
        print(f"\n✗ 测试1失败: {e}\n")
    
    try:
        test_searcher_loads_min_repo_stars()
        print("\n✓ 测试2通过: 搜索器正确加载配置\n")
    except AssertionError as e:
        print(f"\n✗ 测试2失败: {e}\n")
    
    try:
        test_config_default_values()
        print("\n✓ 测试3通过: 默认值正确\n")
    except AssertionError as e:
        print(f"\n✗ 测试3失败: {e}\n")
    
    print("=" * 60)
    print("所有测试完成")
    print("=" * 60)
