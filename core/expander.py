"""
扩散模块 - 从已有KOL发现新KOL
"""
import json
from utils.logger import setup_logger


logger = setup_logger()


class KOLExpander:
    """KOL扩散器"""
    
    def __init__(self, scraper, config_path='config/config.json'):
        self.scraper = scraper
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.expand_batch_size = config['crawler']['expand_batch_size']
        self.recommended_videos_count = config['crawler']['expand_recommended_videos']
    
    def expand_from_kol(self, channel_id):
        """
        从一个KOL扩散，发现新的频道
        策略：分析该KOL视频的推荐列表
        """
        logger.info(f"开始从频道 {channel_id} 扩散")
        
        discovered_channels = set()
        
        try:
            # 1. 获取该频道的最近视频
            videos = self.scraper.get_channel_videos(channel_id, limit=10)
            
            # 2. 对每个视频获取推荐列表
            for video in videos[:self.recommended_videos_count]:
                video_id = video.get('id', '')
                
                try:
                    recommended = self.scraper.get_recommended_videos(video_id)
                    
                    # 3. 从推荐视频中提取频道
                    for rec_video in recommended:
                        rec_channel_id = self.scraper.extract_channel_id(rec_video)
                        if rec_channel_id and rec_channel_id != channel_id:
                            discovered_channels.add(rec_channel_id)
                
                except Exception as e:
                    logger.error(f"获取推荐视频失败: {video_id}, {str(e)}")
                    continue
            
            logger.info(f"从频道 {channel_id} 发现 {len(discovered_channels)} 个新频道")
            return list(discovered_channels)
            
        except Exception as e:
            logger.error(f"扩散失败: {channel_id}, {str(e)}")
            return []
    
    def expand_from_multiple_kols(self, kol_list):
        """
        从多个KOL批量扩散
        """
        logger.info(f"开始批量扩散，来源KOL数: {len(kol_list)}")
        
        all_discovered = set()
        
        for kol in kol_list[:self.expand_batch_size]:
            channel_id = kol['channel_id']
            discovered = self.expand_from_kol(channel_id)
            all_discovered.update(discovered)
        
        logger.info(f"批量扩散完成，共发现 {len(all_discovered)} 个新频道")
        return list(all_discovered)
    
    def extract_channels_from_recommendations(self, video_list):
        """从推荐视频列表中提取频道"""
        channels = set()
        for video in video_list:
            channel_id = self.scraper.extract_channel_id(video)
            if channel_id:
                channels.add(channel_id)
        return list(channels)
