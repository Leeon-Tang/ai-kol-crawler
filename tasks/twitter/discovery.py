# -*- coding: utf-8 -*-
"""
Twitter用户发现任务
"""
from typing import List, Dict
from utils.logger import setup_logger
from platforms.factory import PlatformFactory
from storage.database import Database
from storage.repositories.twitter_repository import TwitterRepository

logger = setup_logger(__name__)


class TwitterDiscoveryTask:
    """Twitter用户发现任务"""
    
    def __init__(self):
        self.platform = PlatformFactory.get_platform('twitter')
        self.db = Database()
        self.db.connect()
        self.db.init_tables()
        self.repository = TwitterRepository(self.db)
    
    def discover_by_keywords(self, keywords: List[str], max_results_per_keyword: int = 10) -> Dict:
        """
        通过关键词发现用户
        
        Args:
            keywords: 关键词列表
            max_results_per_keyword: 每个关键词的最大结果数
            
        Returns:
            发现结果统计
        """
        logger.info(f"开始关键词发现任务，关键词数量: {len(keywords)}")
        
        # 搜索用户
        discovered_users = self.platform.search_by_keywords(keywords, limit=max_results_per_keyword)
        
        stats = {
            'total_discovered': len(discovered_users),
            'new_users': 0,
            'existing_users': 0,
            'analyzed': 0,
            'qualified': 0,
            'failed': 0
        }
        
        # 分析每个用户
        for user_dict in discovered_users:
            # 检查停止标志
            from utils.crawler_status import should_stop
            if should_stop():
                logger.warning("\n⚠️ 检测到停止信号，立即停止")
                logger.info(f"当前进度: 已分析 {stats['analyzed']}, 合格 {stats['qualified']}")
                break
            
            username = user_dict['username']
            
            # 检查是否已存在
            if self.repository.user_exists(username):
                stats['existing_users'] += 1
                logger.info(f"用户已存在: @{username}")
                continue
            
            stats['new_users'] += 1
            
            # 分析用户
            try:
                result = self.platform.analyze_profile(username)
                
                if result.get('status') == 'failed':
                    stats['failed'] += 1
                    continue
                
                stats['analyzed'] += 1
                
                # 保存用户信息
                user_info = result['user_info']
                analysis = result['analysis']
                
                user_data = {
                    **user_info,
                    'analyzed_tweets': analysis['total_tweets'],
                    'ai_tweets': analysis['ai_tweets'],
                    'ai_ratio': analysis['ai_ratio'],
                    'avg_engagement': analysis['avg_engagement'],
                    'original_tweets': analysis['original_tweets'],
                    'original_ratio': analysis['original_ratio'],
                    'quality_score': result['quality_score'],
                    'matched_keywords': analysis['matched_keywords'],
                    'status': result['status'],
                    'discovered_from': 'keyword_search'
                }
                
                self.repository.save_user(user_data)
                
                if result['is_qualified']:
                    stats['qualified'] += 1
                    logger.info(f"✓ 发现合格用户: @{username}, 质量分数: {result['quality_score']:.2f}")
                else:
                    logger.info(f"✗ 用户不合格: @{username}")
                
            except Exception as e:
                logger.error(f"分析用户失败 @{username}: {e}")
                stats['failed'] += 1
        
        logger.info(f"发现任务完成: {stats}")
        return stats
    
    def discover_by_hashtags(self, hashtags: List[str], max_results: int = 20) -> Dict:
        """
        通过话题标签发现用户
        
        Args:
            hashtags: 话题标签列表
            max_results: 最大结果数
            
        Returns:
            发现结果统计
        """
        logger.info(f"开始话题标签发现任务，标签数量: {len(hashtags)}")
        
        # 搜索用户
        discovered_users = self.platform.searcher.search_by_hashtags(hashtags, max_results=max_results)
        
        stats = {
            'total_discovered': len(discovered_users),
            'new_users': 0,
            'existing_users': 0,
            'analyzed': 0,
            'qualified': 0,
            'failed': 0
        }
        
        # 分析每个用户
        for username in discovered_users:
            # 检查停止标志
            from utils.crawler_status import should_stop
            if should_stop():
                logger.warning("\n⚠️ 检测到停止信号，立即停止")
                logger.info(f"当前进度: 已分析 {stats['analyzed']}, 合格 {stats['qualified']}")
                break
            
            # 检查是否已存在
            if self.repository.user_exists(username):
                stats['existing_users'] += 1
                continue
            
            stats['new_users'] += 1
            
            # 分析用户
            try:
                result = self.platform.analyze_profile(username)
                
                if result.get('status') == 'failed':
                    stats['failed'] += 1
                    continue
                
                stats['analyzed'] += 1
                
                # 保存用户信息
                user_info = result['user_info']
                analysis = result['analysis']
                
                user_data = {
                    **user_info,
                    'analyzed_tweets': analysis['total_tweets'],
                    'ai_tweets': analysis['ai_tweets'],
                    'ai_ratio': analysis['ai_ratio'],
                    'avg_engagement': analysis['avg_engagement'],
                    'original_tweets': analysis['original_tweets'],
                    'original_ratio': analysis['original_ratio'],
                    'quality_score': result['quality_score'],
                    'matched_keywords': analysis['matched_keywords'],
                    'status': result['status'],
                    'discovered_from': 'hashtag_search'
                }
                
                self.repository.save_user(user_data)
                
                if result['is_qualified']:
                    stats['qualified'] += 1
                    logger.info(f"✓ 发现合格用户: @{username}")
                
            except Exception as e:
                logger.error(f"分析用户失败 @{username}: {e}")
                stats['failed'] += 1
        
        logger.info(f"话题发现任务完成: {stats}")
        return stats
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'db'):
            self.db.close()
