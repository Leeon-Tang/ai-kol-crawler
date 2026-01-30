# -*- coding: utf-8 -*-
"""
YouTube初始发现任务 - 关键词搜索发现KOL
"""
from utils.logger import setup_logger
from utils.config_loader import load_config


logger = setup_logger()


class YouTubeDiscoveryTask:
    """YouTube发现任务"""
    
    def __init__(self, searcher, analyzer, filter_module, repository):
        self.searcher = searcher
        self.analyzer = analyzer
        self.filter = filter_module
        self.repository = repository
        self.config = load_config()
        self.exclusion_channels = self._load_exclusion_channels()
    
    def _load_exclusion_channels(self) -> set:
        """加载频道黑名单"""
        youtube_config = self.config.get('youtube', {})
        youtube_exclusion = youtube_config.get('exclusion_rules', {})
        exclusion_list = youtube_exclusion.get('exclusion_channels', [])
        # 转为小写的set，方便快速查找
        exclusion_set = {channel_id.lower() for channel_id in exclusion_list if channel_id}
        if exclusion_set:
            logger.info(f"已加载YouTube频道黑名单: {len(exclusion_set)} 个")
        return exclusion_set
    
    def _is_in_exclusion_list(self, channel_id: str) -> bool:
        """检查频道是否在黑名单中"""
        return channel_id.lower() in self.exclusion_channels
    
    def run(self, keyword_limit=30):
        """
        执行发现任务
        1. 关键词搜索
        2. 分析候选KOL
        3. 筛选入库
        """
        logger.info("=" * 50)
        logger.info("开始执行发现任务")
        logger.info("=" * 50)
        logger.info(f"配置信息:")
        logger.info(f"  - 关键词数量: {keyword_limit}")
        logger.info(f"  - AI占比阈值: {self.filter.threshold:.0%}")
        logger.info(f"  - 互动率计算: (点赞×{self.analyzer.like_weight} + 评论×{self.analyzer.comment_weight}) / 观看数")
        if self.exclusion_channels:
            logger.info(f"  - 黑名单: {len(self.exclusion_channels)} 个频道将被跳过")
        logger.info("=" * 50)
        
        # 检查是否已达上限
        if self.filter.should_stop_discovery():
            logger.info("已达到KOL数量上限，停止发现")
            return
        
        # 1. 关键词搜索
        logger.info("阶段1: 关键词搜索")
        candidate_channels = self.searcher.search_by_keywords(keyword_limit)
        
        # 去重
        new_channels = self.filter.deduplicate(candidate_channels)
        logger.info(f"待分析的新频道数: {len(new_channels)}")
        
        # 2. 分析每个候选频道
        logger.info("阶段2: 分析候选KOL")
        qualified_count = 0
        rejected_count = 0
        
        for i, channel_id in enumerate(new_channels):
            # 检查是否达到上限
            if self.filter.should_stop_discovery():
                logger.info("达到上限，停止分析")
                break
            
            logger.info(f"\n分析进度: [{i+1}/{len(new_channels)}]")
            
            # 检查是否在黑名单中
            if self._is_in_exclusion_list(channel_id):
                logger.info(f"🚫 频道在黑名单中，跳过: {channel_id}")
                continue
            
            try:
                # 先获取频道基本信息，检查是否为竞对
                from platforms.youtube.scraper import YouTubeScraper
                temp_scraper = YouTubeScraper()
                channel_info = temp_scraper.get_channel_info(channel_id)
                
                # 检查是否为竞对（提前过滤，节省资源）
                if self.filter.is_competitor(channel_info['channel_name']):
                    logger.info(f"✗ 跳过竞对频道: {channel_info['channel_name']}")
                    continue
                
                # 分析频道
                result = self.analyzer.analyze_channel(
                    channel_id, 
                    discovered_from=f"keyword_search"
                )
                
                if not result:
                    continue
                
                kol_data = result['kol_data']
                video_data_list = result['video_data_list']
                
                # 3. 保存到数据库
                self.repository.add_kol(kol_data)
                
                # 保存视频数据
                for video_data in video_data_list:
                    self.repository.add_video(video_data)
                
                # 如果合格，加入扩散队列
                if kol_data['status'] == 'qualified':
                    qualified_count += 1
                    priority = self.analyzer.calculate_priority(kol_data)
                    self.repository.add_to_expansion_queue(channel_id, priority)
                else:
                    rejected_count += 1
                
            except Exception as e:
                logger.error(f"分析频道失败: {channel_id}, {str(e)}")
                continue
        
        # 总结
        logger.info("=" * 50)
        logger.info(f"发现任务完成")
        logger.info(f"合格KOL: {qualified_count}")
        logger.info(f"不合格KOL: {rejected_count}")
        logger.info(f"总计KOL数: {self.repository.count_qualified_kols()}")
        logger.info("=" * 50)
