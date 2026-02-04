# -*- coding: utf-8 -*-
"""
GitHub平台实现
"""
from typing import Dict, List, Optional
from backend.platforms.base import BasePlatform
from .scraper import GitHubScraper
from .searcher import GitHubSearcher
from .analyzer import GitHubAnalyzer


class GitHubPlatform(BasePlatform):
    """GitHub平台实现"""
    
    def __init__(self):
        self.scraper = GitHubScraper()
        self.searcher = GitHubSearcher(self.scraper)
        self.analyzer = GitHubAnalyzer(self.scraper)
    
    @property
    def platform_name(self) -> str:
        return "github"
    
    @property
    def platform_display_name(self) -> str:
        return "GitHub"
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """通过关键词搜索GitHub开发者"""
        developers = self.searcher.search_by_keywords(keywords, max_results_per_keyword=limit)
        return [{'username': username} for username in developers]
    
    def get_profile_info(self, profile_id: str) -> Optional[Dict]:
        """获取GitHub用户信息"""
        return self.scraper.get_user_info(profile_id)
    
    def analyze_profile(self, profile_id: str) -> Dict:
        """分析GitHub开发者"""
        return self.analyzer.analyze_developer(profile_id)
    
    def extract_contact_info(self, profile_data: Dict) -> Optional[str]:
        """提取GitHub用户联系方式"""
        return profile_data.get('contact_info', '')
