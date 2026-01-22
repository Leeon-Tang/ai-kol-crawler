"""
KOL分析模块
"""
import json
from datetime import datetime, timedelta
from utils.text_matcher import TextMatcher
from utils.exclusion_rules import ExclusionRules
from utils.logger import setup_logger
from utils.config_loader import get_absolute_path


logger = setup_logger()


class KOLAnalyzer:
    """KOL分析器"""
    
    def __init__(self, scraper, config_path='config/config.json'):
        self.scraper = scraper
        self.text_matcher = TextMatcher(config_path)
        self.exclusion_rules = ExclusionRules(config_path)
        
        config_path = get_absolute_path(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.sample_size = config['crawler']['sample_video_count']
        self.active_days_threshold = config['crawler']['active_days_threshold']
    
    def analyze_channel(self, channel_id, discovered_from='unknown'):
        """
        分析频道，返回完整的KOL数据
        """
        logger.info(f"")
        logger.info(f"{'='*70}")
        logger.info(f"开始分析频道: {channel_id}")
        logger.info(f"{'='*70}")
        
        try:
            # 1. 获取频道基本信息
            logger.info(f"")
            logger.info(f"▶ 阶段 1/3: 获取频道基本信息")
            logger.info(f"{'-'*70}")
            channel_info = self.scraper.get_channel_info(channel_id)
            logger.info(f"  频道名称: {channel_info['channel_name']}")
            logger.info(f"  订阅数: {channel_info['subscribers']:,}")
            logger.info(f"  视频数: {channel_info['total_videos']:,}")
            logger.info(f"  链接: {channel_info['channel_url']}")
            
            # 2. 获取频道视频
            logger.info(f"")
            logger.info(f"▶ 阶段 2/3: 获取视频列表 (最多{self.sample_size}个)")
            logger.info(f"{'-'*70}")
            videos = self.scraper.get_channel_videos(channel_id, limit=self.sample_size)
            
            if not videos:
                logger.warning(f"  频道没有视频，跳过分析")
                return None
            
            logger.info(f"  成功获取 {len(videos)} 个视频")
            
            # 3. 分析每个视频
            logger.info(f"")
            logger.info(f"▶ 阶段 3/3: 分析视频内容")
            logger.info(f"{'-'*70}")
            ai_videos = 0
            total_views = 0
            total_likes = 0
            video_data_list = []
            last_video_date = None
            failed_videos = 0
            
            for idx, video in enumerate(videos, 1):
                video_id = video.get('id', '')
                if not video_id:
                    continue
                    
                title = video.get('title', '')
                description = video.get('description', '')
                
                # 判断是否AI相关
                is_ai, matched_keywords = self.text_matcher.is_ai_related(title, description)
                
                # 获取详细信息
                try:
                    video_info = self.scraper.get_video_info(video_id)
                    total_views += (video_info['views'] or 0)
                    total_likes += (video_info['likes'] or 0)
                    
                    # 记录最新视频日期
                    if last_video_date is None or video_info['published_at'] > last_video_date:
                        last_video_date = video_info['published_at']
                    
                    video_info['is_ai_related'] = is_ai
                    video_info['matched_keywords'] = matched_keywords
                    video_data_list.append(video_info)
                    
                    # 详细日志输出
                    if is_ai:
                        ai_videos += 1
                        logger.info(f"  视频 {idx}/{len(videos)} ✓ AI相关")
                        logger.info(f"    标题: {title[:60]}...")
                        logger.info(f"    匹配关键词: {', '.join(matched_keywords[:3])}")
                        logger.info(f"    数据: 观看 {video_info['views']:,} | 点赞 {video_info['likes']:,}")
                        logger.info(f"    链接: {video_info['video_url']}")
                    else:
                        logger.info(f"  视频 {idx}/{len(videos)} ✗ 非AI内容")
                        logger.info(f"    标题: {title[:60]}...")
                        logger.info(f"    原因: 标题和描述中未找到AI关键词")
                        logger.info(f"    数据: 观看 {video_info['views']:,} | 点赞 {video_info['likes']:,}")
                        logger.info(f"    链接: {video_info['video_url']}")
                    
                except Exception as e:
                    failed_videos += 1
                    logger.warning(f"  视频 {idx}/{len(videos)} ⚠ 获取失败")
                    logger.warning(f"    标题: {title[:60]}...")
                    logger.warning(f"    原因: {str(e)}")
                    continue
            
            # 输出统计
            logger.info(f"")
            logger.info(f"  统计: 成功 {len(video_data_list)} | AI相关 {ai_videos} | 非AI {len(video_data_list)-ai_videos} | 失败 {failed_videos}")
            
            # 如果没有成功获取任何视频详情，返回None
            if not video_data_list:
                logger.warning(f"  └─ ✗ 无法获取任何视频详情，跳过")
                return None
            
            # 4. 计算指标
            logger.info(f"  计算分析指标...")
            analyzed_videos = len(video_data_list)
            ai_ratio = ai_videos / analyzed_videos if analyzed_videos > 0 else 0
            avg_views = total_views // analyzed_videos if analyzed_videos > 0 else 0
            avg_likes = total_likes // analyzed_videos if analyzed_videos > 0 else 0
            engagement_rate = total_likes / total_views if total_views > 0 else 0
            
            # 计算距离最后视频的天数
            days_since_last_video = None
            if last_video_date:
                days_since_last_video = (datetime.now() - last_video_date).days
            
            # 5. 判断状态
            status = 'qualified' if ai_ratio >= 0.3 else 'rejected'
            
            # 检查排除规则
            video_titles = [v.get('title', '') for v in video_data_list]
            if self.exclusion_rules.should_exclude_channel(channel_info['channel_name'], video_titles):
                status = 'rejected'
            
            # 6. 输出分析结果
            logger.info(f"")
            logger.info(f"{'='*70}")
            logger.info(f"分析结果")
            logger.info(f"{'='*70}")
            logger.info(f"  频道: {channel_info['channel_name']}")
            logger.info(f"  分析视频: {analyzed_videos} | AI视频: {ai_videos} | AI占比: {ai_ratio:.1%}")
            logger.info(f"  平均观看: {avg_views:,} | 平均点赞: {avg_likes:,} | 互动率: {engagement_rate:.2%}")
            logger.info(f"  最后更新: {days_since_last_video}天前 | 状态: {'✓ 合格' if status == 'qualified' else '✗ 不合格'} (阈值: 30%)")
            logger.info(f"{'='*70}")
            
            # 7. 组装结果
            kol_data = {
                **channel_info,
                'analyzed_videos': analyzed_videos,
                'ai_videos': ai_videos,
                'ai_ratio': round(ai_ratio, 3),
                'avg_views': avg_views,
                'avg_likes': avg_likes,
                'engagement_rate': round(engagement_rate, 4),
                'last_video_date': last_video_date,
                'days_since_last_video': days_since_last_video,
                'status': status,
                'discovered_from': discovered_from,
            }
            
            if status == 'qualified':
                logger.info(f"✓✓✓ {channel_info['channel_name']} - 合格 (AI占比: {ai_ratio:.1%})")
            else:
                logger.warning(f"✗✗✗ {channel_info['channel_name']} - 不合格 (AI占比: {ai_ratio:.1%})")
            
            return {
                'kol_data': kol_data,
                'video_data_list': video_data_list
            }
            
        except Exception as e:
            logger.error(f"✗✗✗ 分析频道失败: {channel_id}, 错误: {str(e)}")
            return None
    
    def is_active(self, days_since_last_video):
        """判断KOL是否活跃"""
        if days_since_last_video is None:
            return False
        return days_since_last_video <= self.active_days_threshold
    
    def calculate_priority(self, kol_data):
        """计算扩散优先级"""
        # 基于AI占比和订阅数计算优先级
        ai_ratio_score = kol_data['ai_ratio'] * 100
        subscriber_score = min(kol_data['subscribers'] / 10000, 100)
        
        priority = int(ai_ratio_score * 0.6 + subscriber_score * 0.4)
        return priority
