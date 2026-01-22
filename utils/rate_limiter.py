"""
请求频率控制
"""
import time
import json
from utils.config_loader import get_absolute_path


class RateLimiter:
    """频率限制器"""
    
    def __init__(self, config_path='config/config.json'):
        config_path = get_absolute_path(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.delay = config['crawler']['rate_limit_delay']
        self.last_request_time = 0
    
    def wait(self):
        """等待到可以发送下一个请求"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
