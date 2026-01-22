"""
过滤模块
"""
import json
from utils.logger import setup_logger
from utils.config_loader import get_absolute_path


logger = setup_logger()


class KOLFilter:
    """KOL过滤器"""
    
    def __init__(self, repository, config_path='config/config.json'):
        self.repository = repository
        
        config_path = get_absolute_path(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.threshold = config['crawler']['ai_ratio_threshold']
    
    def filter_by_ratio(self, kol_data):
        """按AI内容占比过滤"""
        return kol_data['ai_ratio'] >= self.threshold
    
    def deduplicate(self, channel_list):
        """
        去重 - 排除数据库中已存在的频道
        返回: 新的频道列表
        """
        new_channels = []
        
        for channel_id in channel_list:
            if not self.repository.exists(channel_id):
                new_channels.append(channel_id)
        
        logger.info(f"去重: 原始 {len(channel_list)} 个，新增 {len(new_channels)} 个")
        return new_channels
    
    def should_stop_discovery(self):
        """
        判断是否应该停止发现
        基于已有合格KOL数量
        """
        qualified_count = self.repository.count_qualified_kols()
        
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        max_kols = config['crawler']['max_qualified_kols']
        
        if qualified_count >= max_kols:
            logger.info(f"已达到最大KOL数量: {qualified_count}/{max_kols}")
            return True
        
        return False
