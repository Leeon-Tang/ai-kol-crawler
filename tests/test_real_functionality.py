# -*- coding: utf-8 -*-
"""
真实功能测试 - 测试实际模块能否正常工作
"""
import pytest
import os
import sys

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def test_github_export_task_import():
    """测试GitHub导出任务能否导入和初始化"""
    try:
        from tasks.github.export import GitHubExportTask
        from storage.database import Database
        from storage.repositories.github_repository import GitHubRepository
        
        db = Database()
        db.connect()
        db.init_tables()
        repo = GitHubRepository(db)
        task = GitHubExportTask(repo)
        
        assert task is not None
        db.close()
    except Exception as e:
        pytest.fail(f"GitHub导出任务初始化失败: {e}")


def test_github_academic_export_task_import():
    """测试GitHub学术导出任务能否导入和初始化"""
    try:
        from tasks.github.export_academic import GitHubAcademicExportTask
        from storage.database import Database
        from storage.repositories.github_academic_repository import GitHubAcademicRepository
        
        db = Database()
        db.connect()
        db.init_tables()
        repo = GitHubAcademicRepository(db)
        task = GitHubAcademicExportTask(repo)
        
        assert task is not None
        db.close()
    except Exception as e:
        pytest.fail(f"GitHub学术导出任务初始化失败: {e}")


def test_twitter_export_task_import():
    """测试Twitter导出任务能否导入和初始化"""
    try:
        from tasks.twitter.export import TwitterExportTask
        
        task = TwitterExportTask()
        assert task is not None
        
        # 清理
        if hasattr(task, 'db'):
            task.db.close()
    except Exception as e:
        pytest.fail(f"Twitter导出任务初始化失败: {e}")


def test_github_discovery_task_import():
    """测试GitHub发现任务能否导入"""
    try:
        from tasks.github.discovery import GitHubDiscoveryTask
        assert GitHubDiscoveryTask is not None
    except Exception as e:
        pytest.fail(f"GitHub发现任务导入失败: {e}")


def test_twitter_discovery_task_import():
    """测试Twitter发现任务能否导入"""
    try:
        from tasks.twitter.discovery import TwitterDiscoveryTask
        task = TwitterDiscoveryTask()
        assert task is not None
    except Exception as e:
        pytest.fail(f"Twitter发现任务导入失败: {e}")


def test_github_platform_import():
    """测试GitHub平台模块能否导入"""
    try:
        from platforms.github.platform import GitHubPlatform
        from platforms.github.scraper import GitHubScraper
        from platforms.github.searcher import GitHubSearcher
        from platforms.github.analyzer import GitHubAnalyzer
        
        assert GitHubPlatform is not None
        assert GitHubScraper is not None
        assert GitHubSearcher is not None
        assert GitHubAnalyzer is not None
    except Exception as e:
        pytest.fail(f"GitHub平台模块导入失败: {e}")


def test_twitter_platform_import():
    """测试Twitter平台模块能否导入"""
    try:
        from platforms.twitter.platform import TwitterPlatform
        from platforms.twitter.scraper import TwitterScraper
        from platforms.twitter.searcher import TwitterSearcher
        from platforms.twitter.analyzer import TwitterAnalyzer
        
        assert TwitterPlatform is not None
        assert TwitterScraper is not None
        assert TwitterSearcher is not None
        assert TwitterAnalyzer is not None
    except Exception as e:
        pytest.fail(f"Twitter平台模块导入失败: {e}")


def test_utils_modules_import():
    """测试工具模块能否导入"""
    try:
        from utils.config_loader import load_config
        from utils.logger import setup_logger
        from utils.log_manager import add_log
        from utils.crawler_status import set_crawler_running, is_crawler_running
        from utils.rate_limiter import RateLimiter
        from utils.retry import retry_on_failure
        from utils.text_matcher import TextMatcher
        from utils.contact_extractor import ContactExtractor
        from utils.exclusion_rules import ExclusionRules
        
        assert load_config is not None
        assert setup_logger is not None
        assert add_log is not None
        assert set_crawler_running is not None
        assert RateLimiter is not None
        assert retry_on_failure is not None
        assert TextMatcher is not None
        assert ContactExtractor is not None
        assert ExclusionRules is not None
    except Exception as e:
        pytest.fail(f"工具模块导入失败: {e}")


def test_database_operations():
    """测试数据库基本操作"""
    try:
        from storage.database import Database
        
        db = Database()
        db.connect()
        db.init_tables()
        
        # 测试基本查询
        result = db.fetchone("SELECT COUNT(*) as count FROM github_developers")
        assert result is not None
        
        db.close()
    except Exception as e:
        pytest.fail(f"数据库操作失败: {e}")


def test_config_loading():
    """测试配置文件加载"""
    try:
        from utils.config_loader import load_config
        
        config = load_config()
        assert config is not None
        assert 'database' in config
        assert 'crawler' in config
        assert 'github' in config
    except Exception as e:
        pytest.fail(f"配置加载失败: {e}")


def test_platform_factory():
    """测试平台工厂"""
    try:
        from platforms.factory import PlatformFactory
        
        github = PlatformFactory.get_platform('github')
        twitter = PlatformFactory.get_platform('twitter')
        
        assert github is not None
        assert twitter is not None
    except Exception as e:
        pytest.fail(f"平台工厂测试失败: {e}")
