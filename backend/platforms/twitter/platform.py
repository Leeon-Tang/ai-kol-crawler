# -*- coding: utf-8 -*-
"""
Twitter/X平台实现
"""
from typing import Dict, List, Optional
from backend.platforms.base import BasePlatform
from .scraper import TwitterScraper
from .searcher import TwitterSearcher
from .analyzer import TwitterAnalyzer


class TwitterPlatform(BasePlatform):
    """Twitter/X平台实现"""
    
    def __init__(self):
        self.scraper = TwitterScraper()
        self.searcher = TwitterSearcher(self.scraper)
        self.analyzer = TwitterAnalyzer(self.scraper)
    
    @property
    def platform_name(self) -> str:
        return "twitter"
    
    @property
    def platform_display_name(self) -> str:
        return "Twitter/X"
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """通过关键词搜索Twitter用户"""
        users = self.searcher.search_by_keywords(keywords, max_results_per_keyword=limit)
        return [{'username': username} for username in users]
    
    def get_profile_info(self, profile_id: str) -> Optional[Dict]:
        """获取Twitter用户信息"""
        return self.scraper.get_user_info(profile_id)
    
    def analyze_profile(self, profile_id: str) -> Dict:
        """分析Twitter用户"""
        return self.analyzer.analyze_user(profile_id)
    
    def extract_contact_info(self, profile_data: Dict) -> Optional[str]:
        """提取Twitter用户联系方式"""
        return profile_data.get('contact_info', '')
