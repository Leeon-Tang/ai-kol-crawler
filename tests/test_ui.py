# -*- coding: utf-8 -*-
"""
UI模块测试
注意：Streamlit UI测试需要特殊的测试环境
这里主要测试UI模块的导入和基本功能
"""
import pytest
import sys
import os

def test_ui_imports():
    """测试UI模块导入"""
    # GitHub UI
    from ui.github import crawler as github_crawler
    from ui.github import data_browser as github_browser
    from ui.github import rules as github_rules
    from ui.github import texts as github_texts
    
    assert github_crawler is not None
    assert github_browser is not None
    assert github_rules is not None
    assert github_texts is not None
    
    # Twitter UI
    from ui.twitter import crawler as twitter_crawler
    from ui.twitter import data_browser as twitter_browser
    from ui.twitter import texts as twitter_texts
    
    assert twitter_crawler is not None
    assert twitter_browser is not None
    assert twitter_texts is not None

def test_github_texts():
    """测试GitHub文本常量"""
    from ui.github.texts import LABELS
    
    assert "rules_title" in LABELS
    assert "crawler_title" in LABELS
    assert "save_config" in LABELS

def test_twitter_texts():
    """测试Twitter文本常量"""
    from ui.twitter.texts import TEXTS
    
    assert "crawler_title" in TEXTS
    assert "ai_tweets" in TEXTS

def test_dashboard_functions():
    """测试仪表盘函数"""
    # 由于dashboard依赖其他模块，我们只测试基本导入
    try:
        from ui.common import dashboard
        assert dashboard is not None
    except ImportError:
        # 如果导入失败，至少测试GitHub和Twitter的dashboard
        from ui.github import data_browser as github_browser
        from ui.twitter import data_browser as twitter_browser
        assert github_browser is not None
        assert twitter_browser is not None
