"""
重试机制
"""
import time
import json
from functools import wraps
from utils.config_loader import get_absolute_path


def load_retry_config():
    """加载重试配置"""
    config_path = get_absolute_path('config/config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['crawler']['max_retries']


def retry_on_failure(max_retries=None):
    """重试装饰器"""
    if max_retries is None:
        max_retries = load_retry_config()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"尝试 {attempt + 1}/{max_retries} 失败: {str(e)}, 重试中...")
                    time.sleep(2 ** attempt)  # 指数退避
            return None
        return wrapper
    return decorator
