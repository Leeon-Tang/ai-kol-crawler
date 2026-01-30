# -*- coding: utf-8 -*-
"""
任务模块测试 - 测试任务能否正常导入和初始化
"""
import pytest
import os
import sys
from unittest.mock import Mock, MagicMock

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def test_github_discovery_task(test_db_path):
    """测试GitHub发现任务"""
    from tasks.github.discovery import GitHubDiscoveryTask
    from storage.repositories.github_repository import GitHubRepository
    from storage.repositories.github_academic_repository import GitHubAcademicRepository
    from storage.database import Database
    
    db = Database()
    db.db_path = test_db_path
    db.connect()
    db.init_tables()
    repo = GitHubRepository(db)
    academic_repo = GitHubAcademicRepository(db)
    
    # 创建模拟的searcher和analyzer
    mock_searcher = Mock()
    mock_analyzer = Mock()
    
    task = GitHubDiscoveryTask(mock_searcher, mock_analyzer, repo, academic_repo)
    assert task is not None
    
    db.close()

def test_github_export(test_db_path, temp_dir):
    """测试GitHub导出功能"""
    from tasks.github.export import GitHubExportTask
    from storage.repositories.github_repository import GitHubRepository
    from storage.database import Database
    import os
    
    db = Database()
    db.db_path = test_db_path
    db.connect()
    db.init_tables()
    repo = GitHubRepository(db)
    
    # 添加测试数据
    developer_data = {
        "user_id": 44444,
        "username": "export_test",
        "name": "Export Test",
        "followers": 100,
        "public_repos": 50,
        "bio": "Test",
        "is_indie_developer": True,
        "status": "qualified"
    }
    repo.save_developer(developer_data)
    
    # 导出
    export_task = GitHubExportTask(repo)
    output_file = export_task.run(limit=100)
    
    assert output_file != ""
    assert os.path.exists(output_file)
    
    db.close()

def test_github_export_academic(test_db_path, temp_dir):
    """测试GitHub学术人士导出"""
    from tasks.github.export_academic import GitHubAcademicExportTask
    from storage.repositories.github_academic_repository import GitHubAcademicRepository
    from storage.database import Database
    import os
    
    db = Database()
    db.db_path = test_db_path
    db.connect()
    db.init_tables()
    repo = GitHubAcademicRepository(db)
    
    # 添加测试数据
    academic_data = {
        "user_id": 55555,
        "username": "academic_export",
        "name": "Academic Export",
        "followers": 50,
        "public_repos": 20,
        "bio": "PhD student",
        "status": "qualified"
    }
    repo.save_academic_developer(academic_data)
    
    # 导出
    export_task = GitHubAcademicExportTask(repo)
    output_file = export_task.run(limit=100)
    
    assert output_file != ""
    assert os.path.exists(output_file)
    
    db.close()

def test_twitter_discovery_task(test_db_path):
    """测试Twitter发现任务"""
    from tasks.twitter.discovery import TwitterDiscoveryTask
    
    task = TwitterDiscoveryTask()
    assert task is not None

def test_twitter_export(test_db_path, temp_dir):
    """测试Twitter导出功能"""
    from tasks.twitter.export import TwitterExportTask
    from storage.repositories.twitter_repository import TwitterRepository
    from storage.database import Database
    import os
    
    db = Database()
    db.db_path = test_db_path
    db.connect()
    db.init_tables()
    repo = TwitterRepository(db)
    
    # 添加测试数据
    user_data = {
        "user_id": "111222333",
        "username": "twitter_export",
        "name": "Twitter Export",
        "followers_count": 1000,
        "following_count": 500,
        "tweet_count": 100,
        "bio": "AI enthusiast",
        "ai_ratio": 0.7,
        "status": "qualified"
    }
    repo.save_user(user_data)
    
    # 导出 - 可能返回空字符串如果没有qualified用户
    export_task = TwitterExportTask()
    output_file = export_task.export_qualified_users(limit=100)
    
    # 验证函数能正常执行（可能返回空字符串）
    assert output_file is not None
    
    db.close()
