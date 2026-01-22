"""
关键词搜索模块
"""
import json
import random
from utils.logger import setup_logger


logger = setup_logger()


class KeywordSearcher:
    """关键词搜索器"""
    
    def __init__(self, scraper, config_path='config/config.json'):
        self.scraper = scraper
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.keywords = self._load_keywords(config)
        self.max_results = config['crawler']['search_results_per_keyword']
    
    def _load_keywords(self, config):
        """加载所有关键词"""
        keywords = []
        for priority in ['priority_high', 'priority_medium', 'priority_low']:
            keywords.extend(config['keywords'][priority])
        return keywords
    
    def search_by_keywords(self, keyword_limit=30):
        """
        按关键词搜索，返回候选频道列表
        使用随机关键词避免每次都是相同的
        """
        logger.info(f"开始关键词搜索，从 {len(self.keywords)} 个关键词中随机选择 {keyword_limit} 个")
        
        # 随机选择关键词
        if keyword_limit >= len(self.keywords):
            selected_keywords = self.keywords
        else:
            selected_keywords = random.sample(self.keywords, keyword_limit)
        
        logger.info(f"本次使用的关键词: {', '.join(selected_keywords[:5])}{'...' if len(selected_keywords) > 5 else ''}")
        
        all_channels = set()
        
        for i, keyword in enumerate(selected_keywords):
            logger.info(f"搜索关键词 [{i+1}/{len(selected_keywords)}]: '{keyword}'")
            
            try:
                videos = self.scraper.search_videos(keyword, self.max_results)
                
                # 提取频道ID
                channels_found = 0
                for video in videos:
                    channel_id = self.scraper.extract_channel_id(video)
                    if channel_id:
                        all_channels.add(channel_id)
                        channels_found += 1
                
                logger.info(f"  └─ 从 {len(videos)} 个视频中提取 {channels_found} 个频道")
                
            except Exception as e:
                logger.error(f"  └─ 搜索失败: {str(e)}")
                continue
        
        logger.info(f"关键词搜索完成，发现 {len(all_channels)} 个唯一频道")
        logger.info(f"说明: 3个关键词 × 10个视频/关键词 = 最多30个视频，来自 {len(all_channels)} 个不同频道")
        return list(all_channels)
    
    def extract_channels_from_videos(self, videos):
        """从视频列表提取唯一的频道列表"""
        channels = set()
        for video in videos:
            channel_id = self.scraper.extract_channel_id(video)
            if channel_id:
                channels.add(channel_id)
        return list(channels)
