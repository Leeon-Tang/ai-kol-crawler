"""
扩散任务 - 从已有KOL扩散发现新KOL
"""
from backend.utils.logger import setup_logger
from backend.utils.config_loader import load_config


logger = setup_logger()


class YouTubeExpandTask:
    """扩散任务"""
    
    def __init__(self, expander, analyzer, filter_module, repository):
        self.expander = expander
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
        exclusion_set = {channel_id.lower() for channel_id in exclusion_list if channel_id}
        if exclusion_set:
            logger.info(f"已加载YouTube频道黑名单: {len(exclusion_set)} 个")
        return exclusion_set
    
    def _is_in_exclusion_list(self, channel_id: str) -> bool:
        """检查频道是否在黑名单中"""
        return channel_id.lower() in self.exclusion_channels
    
    def run(self):
        """
        执行扩散任务
        1. 从扩散队列获取KOL
        2. 扩散发现新频道
        3. 分析新频道
        4. 筛选入库
        """
        logger.info("=" * 50)
        logger.info("开始执行扩散任务")
        logger.info("=" * 50)
        logger.info(f"配置信息:")
        logger.info(f"  - AI占比阈值: {self.filter.threshold:.0%}")
        logger.info(f"  - 互动率计算: (点赞×{self.analyzer.like_weight} + 评论×{self.analyzer.comment_weight}) / 观看数")
        if self.exclusion_channels:
            logger.info(f"  - 黑名单: {len(self.exclusion_channels)} 个频道将被跳过")
        logger.info("=" * 50)
        
        # 检查是否已达上限
        if self.filter.should_stop_discovery():
            logger.info("已达到KOL数量上限，停止扩散")
            return
        
        # 1. 获取待扩散的KOL
        expansion_queue = self.repository.get_expansion_queue(limit=10)
        
        if not expansion_queue:
            logger.info("扩散队列为空，无法执行扩散")
            return
        
        logger.info(f"待扩散KOL数: {len(expansion_queue)}")
        
        all_discovered = set()
        
        # 2. 对每个KOL进行扩散
        for queue_item in expansion_queue:
            channel_id = queue_item['channel_id']
            queue_id = queue_item['id']
            
            # 更新状态为处理中
            self.repository.update_expansion_status(queue_id, 'processing')
            
            try:
                # 扩散
                discovered = self.expander.expand_from_kol(channel_id)
                all_discovered.update(discovered)
                
                # 更新状态为完成
                self.repository.update_expansion_status(queue_id, 'completed')
                
            except Exception as e:
                logger.error(f"扩散失败: {channel_id}, {str(e)}")
                continue
        
        # 3. 去重
        new_channels = self.filter.deduplicate(list(all_discovered))
        logger.info(f"扩散发现新频道数: {len(new_channels)}")
        
        # 4. 分析新频道
        qualified_count = 0
        rejected_count = 0
        
        for i, channel_id in enumerate(new_channels):
            # 检查是否达到上限
            if self.filter.should_stop_discovery():
                logger.info("达到上限，停止分析")
                break
            
            logger.info(f"分析进度: [{i+1}/{len(new_channels)}]")
            
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
                    discovered_from=f"expansion"
                )
                
                if not result:
                    continue
                
                kol_data = result['kol_data']
                video_data_list = result['video_data_list']
                
                # 保存到数据库
                self.repository.add_kol(kol_data)
                
                for video_data in video_data_list:
                    self.repository.add_video(video_data)
                
                # 如果合格，加入扩散队列
                if kol_data['status'] == 'qualified':
                    qualified_count += 1
                    priority = self.analyzer.calculate_priority(kol_data)
                    self.repository.add_to_expansion_queue(channel_id, priority)
                    
                    logger.info(f"✓ 合格: {kol_data['channel_name']} - AI占比: {kol_data['ai_ratio']:.1%}")
                else:
                    rejected_count += 1
                    logger.info(f"✗ 不合格: {kol_data['channel_name']} - AI占比: {kol_data['ai_ratio']:.1%}")
                
            except Exception as e:
                logger.error(f"分析频道失败: {channel_id}, {str(e)}")
                continue
        
        # 总结
        logger.info("=" * 50)
        logger.info(f"扩散任务完成")
        logger.info(f"新增合格KOL: {qualified_count}")
        logger.info(f"新增不合格KOL: {rejected_count}")
        logger.info(f"总计KOL数: {self.repository.count_qualified_kols()}")
        logger.info("=" * 50)
