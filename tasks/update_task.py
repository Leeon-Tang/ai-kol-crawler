"""
更新任务 - 更新已有KOL的数据
"""
import json
from datetime import datetime
from utils.logger import setup_logger


logger = setup_logger()


class UpdateTask:
    """更新任务"""
    
    def __init__(self, scraper, analyzer, repository, config_path='config/config.json'):
        self.scraper = scraper
        self.analyzer = analyzer
        self.repository = repository
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.update_video_count = config['crawler']['update_recent_videos']
        
        # 互动率权重配置
        engagement_config = config.get('engagement', {})
        self.like_weight = engagement_config.get('like_weight', 0.4)
        self.comment_weight = engagement_config.get('comment_weight', 0.6)
    
    def run(self):
        """
        执行更新任务
        1. 获取所有合格的KOL
        2. 更新每个KOL的最新数据
        """
        logger.info("=" * 50)
        logger.info("开始执行更新任务")
        logger.info("=" * 50)
        
        # 获取所有合格的KOL
        qualified_kols = self.repository.get_qualified_kols()
        
        if not qualified_kols:
            logger.info("没有需要更新的KOL")
            return
        
        logger.info(f"待更新KOL数: {len(qualified_kols)}")
        
        updated_count = 0
        downgraded_count = 0
        
        for i, kol in enumerate(qualified_kols):
            channel_id = kol['channel_id']
            logger.info(f"更新进度: [{i+1}/{len(qualified_kols)}] - {kol['channel_name']}")
            
            try:
                # 获取最新视频
                videos = self.scraper.get_channel_videos(channel_id, limit=self.update_video_count)
                
                if not videos:
                    logger.warning(f"频道 {channel_id} 没有新视频")
                    continue
                
                # 分析最新视频
                ai_videos = 0
                total_views = 0
                total_likes = 0
                total_comments = 0
                last_video_date = None
                
                for video in videos:
                    video_id = video.get('id', '')
                    title = video.get('title', '')
                    description = video.get('description', '')
                    
                    # 判断是否AI相关
                    is_ai, _ = self.analyzer.text_matcher.is_ai_related(title, description)
                    if is_ai:
                        ai_videos += 1
                    
                    # 获取详细信息
                    try:
                        video_info = self.scraper.get_video_info(video_id)
                        total_views += video_info['views']
                        total_likes += video_info['likes']
                        total_comments += video_info['comments']
                        
                        if last_video_date is None or video_info['published_at'] > last_video_date:
                            last_video_date = video_info['published_at']
                    
                    except Exception as e:
                        logger.error(f"获取视频详情失败: {video_id}, {str(e)}")
                        continue
                
                # 计算新的指标
                analyzed_videos = len(videos)
                new_ai_ratio = ai_videos / analyzed_videos if analyzed_videos > 0 else 0
                new_avg_views = total_views // analyzed_videos if analyzed_videos > 0 else 0
                new_avg_likes = total_likes // analyzed_videos if analyzed_videos > 0 else 0
                new_avg_comments = total_comments // analyzed_videos if analyzed_videos > 0 else 0
                
                # 新的互动率计算公式: (平均点赞*like_weight + 平均评论*comment_weight) / 平均观看数
                if new_avg_views > 0:
                    new_engagement_rate = (new_avg_likes * self.like_weight + new_avg_comments * self.comment_weight) / new_avg_views
                else:
                    new_engagement_rate = 0
                
                days_since_last_video = None
                if last_video_date:
                    days_since_last_video = (datetime.now() - last_video_date).days
                
                # 更新数据
                update_data = {
                    'avg_views': new_avg_views,
                    'avg_likes': new_avg_likes,
                    'avg_comments': new_avg_comments,
                    'engagement_rate': round(new_engagement_rate, 4),
                    'last_video_date': last_video_date,
                    'days_since_last_video': days_since_last_video,
                }
                
                # 检查AI占比是否下降
                if new_ai_ratio < 0.3:
                    update_data['status'] = 'rejected'
                    downgraded_count += 1
                    logger.warning(f"KOL降级: {kol['channel_name']} - 新AI占比: {new_ai_ratio:.1%}")
                
                self.repository.update_kol(channel_id, update_data)
                updated_count += 1
                
                logger.info(f"✓ 更新完成: {kol['channel_name']}")
                
            except Exception as e:
                logger.error(f"更新KOL失败: {channel_id}, {str(e)}")
                continue
        
        # 总结
        logger.info("=" * 50)
        logger.info(f"更新任务完成")
        logger.info(f"成功更新: {updated_count}")
        logger.info(f"降级KOL: {downgraded_count}")
        logger.info("=" * 50)
