"""
发现任务 - 关键词搜索发现KOL
"""
from utils.logger import setup_logger


logger = setup_logger()


class DiscoveryTask:
    """发现任务"""
    
    def __init__(self, searcher, analyzer, filter_module, repository):
        self.searcher = searcher
        self.analyzer = analyzer
        self.filter = filter_module
        self.repository = repository
    
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
            
            try:
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
