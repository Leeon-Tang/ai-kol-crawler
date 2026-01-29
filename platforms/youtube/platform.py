# -*- coding: utf-8 -*-
"""
YouTube平台实现
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import Dict, List, Optional
from platforms.base import BasePlatform
from platforms.youtube.scraper import YouTubeScraper
from platforms.youtube.searcher import KeywordSearcher
from platforms.youtube.analyzer import KOLAnalyzer
from utils.contact_extractor import ContactExtractor


class YouTubePlatform(BasePlatform):
    """YouTube平台实现"""
    
    def __init__(self):
        self.scraper = YouTubeScraper()
        self.searcher = KeywordSearcher(self.scraper)
        self.analyzer = KOLAnalyzer(self.scraper)
        self.contact_extractor = ContactExtractor()
    
    @property
    def platform_name(self) -> str:
        return "youtube"
    
    @property
    def platform_display_name(self) -> str:
        return "YouTube"
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """通过关键词搜索YouTube视频"""
        results = []
        for keyword in keywords:
            videos = self.searcher.search_videos(keyword, max_results=limit)
            results.extend(videos)
        return results
    
    def get_profile_info(self, profile_id: str) -> Optional[Dict]:
        """获取YouTube频道信息"""
        return self.scraper.get_channel_info(profile_id)
    
    def analyze_profile(self, profile_id: str) -> Dict:
        """分析YouTube频道"""
        return self.analyzer.analyze_channel(profile_id)
    
    def extract_contact_info(self, profile_data: Dict) -> Optional[str]:
        """提取YouTube频道联系方式"""
        return self.contact_extractor.extract_all_contacts(profile_data.get('description', ''))
