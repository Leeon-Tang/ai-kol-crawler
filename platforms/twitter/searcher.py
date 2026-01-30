# -*- coding: utf-8 -*-
"""
Twitter搜索器 - 通过关键词发现AI相关用户
"""
from typing import List, Set, Dict, Optional
from utils.logger import setup_logger
from utils.text_matcher import TextMatcher

logger = setup_logger(__name__)


class TwitterSearcher:
    """Twitter搜索器"""
    
    def __init__(self, scraper):
        self.scraper = scraper
        self.text_matcher = TextMatcher()
    
    def search_by_keywords(self, keywords: List[str], max_results_per_keyword: int = 10) -> Set[str]:
        """
        通过关键词搜索用户
        
        Args:
            keywords: 关键词列表
            max_results_per_keyword: 每个关键词返回的最大结果数
            
        Returns:
            用户名集合
        """
        discovered_users = set()
        
        for keyword in keywords:
            logger.info(f"搜索关键词: {keyword}")
            
            try:
                # 搜索推文
                tweets = self.scraper.search_tweets(keyword, limit=max_results_per_keyword * 2)
                
                # 提取用户名
                for tweet in tweets:
                    username = tweet.get('username')
                    if username and username not in discovered_users:
                        # 简单过滤：检查用户是否发布AI相关内容
                        if self._is_ai_related_user(tweet):
                            discovered_users.add(username)
                            logger.info(f"发现用户: @{username}")
                            
                            if len(discovered_users) >= max_results_per_keyword:
                                break
                
            except Exception as e:
                logger.error(f"搜索关键词失败 {keyword}: {e}")
                continue
        
        logger.info(f"搜索完成，共发现 {len(discovered_users)} 个用户")
        return discovered_users
    
    def search_by_hashtags(self, hashtags: List[str], max_results: int = 20) -> Set[str]:
        """
        通过话题标签搜索用户
        
        Args:
            hashtags: 话题标签列表 (不带#)
            max_results: 最大结果数
            
        Returns:
            用户名集合
        """
        discovered_users = set()
        
        for hashtag in hashtags:
            search_query = f"#{hashtag}"
            logger.info(f"搜索话题: {search_query}")
            
            try:
                tweets = self.scraper.search_tweets(search_query, limit=max_results)
                
                for tweet in tweets:
                    username = tweet.get('username')
                    if username and username not in discovered_users:
                        discovered_users.add(username)
                        logger.info(f"发现用户: @{username}")
                
            except Exception as e:
                logger.error(f"搜索话题失败 {search_query}: {e}")
                continue
        
        logger.info(f"话题搜索完成，共发现 {len(discovered_users)} 个用户")
        return discovered_users
    
    def _is_ai_related_user(self, tweet: Dict) -> bool:
        """
        判断用户是否与AI相关
        
        Args:
            tweet: 推文数据
            
        Returns:
            是否AI相关
        """
        # 检查推文文本
        text = tweet.get('text', '').lower()
        
        # AI相关关键词
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml',
            'deep learning', 'neural network', 'llm', 'gpt', 'chatgpt',
            'generative ai', 'diffusion', 'transformer', 'openai',
            'anthropic', 'claude', 'gemini', 'midjourney', 'stable diffusion'
        ]
        
        # 检查是否包含AI关键词
        for keyword in ai_keywords:
            if keyword in text:
                return True
        
        return False
