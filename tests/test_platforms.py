# -*- coding: utf-8 -*-
"""
平台模块测试
"""
import pytest
from unittest.mock import Mock, patch

def test_platform_factory():
    """测试平台工厂"""
    from platforms.factory import PlatformFactory
    
    # 测试获取GitHub平台
    github_platform = PlatformFactory.get_platform("github")
    assert github_platform is not None
    
    # 测试获取Twitter平台
    twitter_platform = PlatformFactory.get_platform("twitter")
    assert twitter_platform is not None
    
    # 测试无效平台
    invalid_platform = PlatformFactory.get_platform("invalid")
    assert invalid_platform is None

def test_github_scraper():
    """测试GitHub爬虫"""
    from platforms.github.scraper import GitHubScraper
    
    scraper = GitHubScraper()
    assert scraper is not None
    
    # 注意：实际API调用需要网络连接和API token
    # 这里只测试对象创建

def test_github_searcher(test_db_path):
    """测试GitHub搜索器"""
    from platforms.github.searcher import GitHubSearcher
    from platforms.github.scraper import GitHubScraper
    from storage.repositories.github_repository import GitHubRepository
    from storage.database import Database
    
    db = Database()
    db.db_path = test_db_path
    db.connect()
    db.init_tables()
    repo = GitHubRepository(db)
    scraper = GitHubScraper()
    searcher = GitHubSearcher(scraper, repo)
    
    assert searcher is not None
    
    db.close()

def test_github_analyzer():
    """测试GitHub分析器"""
    from platforms.github.analyzer import GitHubAnalyzer
    from platforms.github.scraper import GitHubScraper
    
    scraper = GitHubScraper()
    analyzer = GitHubAnalyzer(scraper)
    
    assert analyzer is not None
    
    # 测试分析逻辑（使用模拟数据）
    mock_repos = [
        {"name": "ai-project", "description": "AI and machine learning", "stargazers_count": 100},
        {"name": "web-app", "description": "Web application", "stargazers_count": 50}
    ]
    
    # 这里可以添加更多的单元测试

def test_twitter_scraper():
    """测试Twitter爬虫"""
    from platforms.twitter.scraper import TwitterScraper
    
    scraper = TwitterScraper()
    assert scraper is not None

def test_twitter_searcher():
    """测试Twitter搜索器"""
    from platforms.twitter.searcher import TwitterSearcher
    from platforms.twitter.scraper import TwitterScraper
    
    scraper = TwitterScraper()
    searcher = TwitterSearcher(scraper)
    
    assert searcher is not None

def test_twitter_analyzer():
    """测试Twitter分析器"""
    from platforms.twitter.analyzer import TwitterAnalyzer
    from platforms.twitter.scraper import TwitterScraper
    
    scraper = TwitterScraper()
    analyzer = TwitterAnalyzer(scraper)
    
    assert analyzer is not None
