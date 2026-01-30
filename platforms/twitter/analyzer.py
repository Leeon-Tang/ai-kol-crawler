# -*- coding: utf-8 -*-
"""
Twitter用户分析器 - 分析用户质量和AI相关度
"""
from typing import Dict, List
from datetime import datetime, timedelta
from utils.logger import setup_logger
from utils.text_matcher import TextMatcher
from utils.config_loader import load_config

logger = setup_logger(__name__)


class TwitterAnalyzer:
    """Twitter用户分析器"""
    
    def __init__(self, scraper):
        self.scraper = scraper
        self.text_matcher = TextMatcher()
        self.config = load_config()
        
        # 配置阈值
        self.min_followers = self.config.get('twitter', {}).get('min_followers', 1000)
        self.min_tweets = self.config.get('twitter', {}).get('min_tweets', 50)
        self.ai_ratio_threshold = self.config.get('twitter', {}).get('ai_ratio_threshold', 0.3)
        self.sample_tweet_count = self.config.get('twitter', {}).get('sample_tweet_count', 20)
    
    def analyze_user(self, username: str) -> Dict:
        """
        分析Twitter用户
        
        Args:
            username: 用户名
            
        Returns:
            分析结果
        """
        logger.info(f"开始分析用户: @{username}")
        
        # 获取用户信息
        user_info = self.scraper.get_user_info(username)
        if not user_info:
            logger.error(f"无法获取用户信息: @{username}")
            return {'status': 'failed', 'reason': '无法获取用户信息'}
        
        # 获取最近推文
        tweets = self.scraper.get_user_tweets(username, limit=self.sample_tweet_count)
        if not tweets:
            logger.warning(f"无法获取推文: @{username}")
            return {'status': 'failed', 'reason': '无法获取推文'}
        
        # 分析推文
        analysis = self._analyze_tweets(tweets)
        
        # 计算质量分数
        quality_score = self._calculate_quality_score(user_info, analysis)
        
        # 判断是否合格
        is_qualified = self._is_qualified(user_info, analysis, quality_score)
        
        result = {
            'username': username,
            'user_info': user_info,
            'analysis': analysis,
            'quality_score': quality_score,
            'is_qualified': is_qualified,
            'status': 'qualified' if is_qualified else 'unqualified'
        }
        
        logger.info(f"分析完成: @{username}, 质量分数: {quality_score:.2f}, 状态: {result['status']}")
        return result
    
    def _analyze_tweets(self, tweets: List[Dict]) -> Dict:
        """分析推文内容"""
        total_tweets = len(tweets)
        ai_tweets = 0
        total_engagement = 0
        original_tweets = 0
        
        matched_keywords = set()
        
        for tweet in tweets:
            text = tweet.get('text', '')
            
            # 检查是否AI相关
            is_ai, keywords = self.text_matcher.is_ai_related(text)
            if is_ai:
                ai_tweets += 1
                matched_keywords.update(keywords)
            
            # 计算互动
            engagement = (
                tweet.get('like_count', 0) +
                tweet.get('retweet_count', 0) * 2 +
                tweet.get('reply_count', 0) * 1.5
            )
            total_engagement += engagement
            
            # 统计原创推文
            if not tweet.get('is_retweet', False):
                original_tweets += 1
        
        ai_ratio = ai_tweets / total_tweets if total_tweets > 0 else 0
        avg_engagement = total_engagement / total_tweets if total_tweets > 0 else 0
        original_ratio = original_tweets / total_tweets if total_tweets > 0 else 0
        
        return {
            'total_tweets': total_tweets,
            'ai_tweets': ai_tweets,
            'ai_ratio': ai_ratio,
            'avg_engagement': avg_engagement,
            'original_tweets': original_tweets,
            'original_ratio': original_ratio,
            'matched_keywords': list(matched_keywords)
        }
    
    def _calculate_quality_score(self, user_info: Dict, analysis: Dict) -> float:
        """
        计算用户质量分数 (0-100)
        
        综合考虑:
        - 粉丝数 (30%)
        - AI相关度 (30%)
        - 互动率 (20%)
        - 原创率 (10%)
        - 认证状态 (10%)
        """
        score = 0.0
        
        # 粉丝数得分 (30分)
        followers = user_info.get('followers_count', 0)
        if followers >= 100000:
            score += 30
        elif followers >= 50000:
            score += 25
        elif followers >= 10000:
            score += 20
        elif followers >= 5000:
            score += 15
        elif followers >= 1000:
            score += 10
        else:
            score += 5
        
        # AI相关度得分 (30分)
        ai_ratio = analysis.get('ai_ratio', 0)
        score += ai_ratio * 30
        
        # 互动率得分 (20分)
        avg_engagement = analysis.get('avg_engagement', 0)
        followers = max(followers, 1)
        engagement_rate = (avg_engagement / followers) * 100
        
        if engagement_rate >= 5:
            score += 20
        elif engagement_rate >= 2:
            score += 15
        elif engagement_rate >= 1:
            score += 10
        elif engagement_rate >= 0.5:
            score += 5
        
        # 原创率得分 (10分)
        original_ratio = analysis.get('original_ratio', 0)
        score += original_ratio * 10
        
        # 认证状态得分 (10分)
        if user_info.get('verified', False):
            score += 10
        elif user_info.get('is_blue_verified', False):
            score += 5
        
        return min(score, 100.0)
    
    def _is_qualified(self, user_info: Dict, analysis: Dict, quality_score: float) -> bool:
        """判断用户是否合格"""
        # 基本条件
        if user_info.get('followers_count', 0) < self.min_followers:
            logger.info(f"粉丝数不足: {user_info.get('followers_count', 0)} < {self.min_followers}")
            return False
        
        if user_info.get('tweet_count', 0) < self.min_tweets:
            logger.info(f"推文数不足: {user_info.get('tweet_count', 0)} < {self.min_tweets}")
            return False
        
        # AI相关度
        if analysis.get('ai_ratio', 0) < self.ai_ratio_threshold:
            logger.info(f"AI相关度不足: {analysis.get('ai_ratio', 0):.2f} < {self.ai_ratio_threshold}")
            return False
        
        # 质量分数
        if quality_score < 50:
            logger.info(f"质量分数不足: {quality_score:.2f} < 50")
            return False
        
        return True
