# -*- coding: utf-8 -*-
"""
Pytest配置文件 - 提供测试fixtures和配置
"""
import pytest
import os
import sys
import tempfile
import shutil
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

@pytest.fixture(scope="session")
def project_root():
    """返回项目根目录"""
    return PROJECT_ROOT

@pytest.fixture(scope="function")
def temp_dir():
    """创建临时目录用于测试"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture(scope="function")
def test_db_path(temp_dir):
    """创建测试数据库路径"""
    return os.path.join(temp_dir, "test_crawler.db")

@pytest.fixture(scope="function")
def test_config():
    """返回测试配置"""
    return {
        "database": {
            "type": "sqlite"
        },
        "crawler": {
            "ai_ratio_threshold": 0.3,
            "sample_video_count": 5,
            "rate_limit_delay": 0.1,
            "max_retries": 2
        },
        "github": {
            "min_followers": 10,
            "min_stars": 10,
            "search_keywords": ["test", "ai"]
        },
        "twitter": {
            "min_followers": 100,
            "min_tweets": 10
        }
    }

@pytest.fixture(scope="function")
def mock_logs():
    """模拟日志列表"""
    return []

@pytest.fixture(scope="function")
def add_log_func(mock_logs):
    """返回添加日志的函数"""
    def add_log(message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mock_logs.append(f"[{timestamp}] [{level}] {message}")
    return add_log
