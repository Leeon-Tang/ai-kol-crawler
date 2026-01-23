# -*- coding: utf-8 -*-
"""
平台基类 - 定义所有平台爬虫的通用接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BasePlatform(ABC):
    """平台基类"""
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台名称"""
        pass
    
    @property
    @abstractmethod
    def platform_display_name(self) -> str:
        """平台显示名称（中文）"""
        pass
    
    @abstractmethod
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """
        通过关键词搜索
        
        Args:
            keywords: 关键词列表
            limit: 每个关键词返回的结果数量
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    def get_profile_info(self, profile_id: str) -> Optional[Dict]:
        """
        获取个人/频道详细信息
        
        Args:
            profile_id: 个人/频道ID
            
        Returns:
            详细信息字典
        """
        pass
    
    @abstractmethod
    def analyze_profile(self, profile_id: str) -> Dict:
        """
        分析个人/频道
        
        Args:
            profile_id: 个人/频道ID
            
        Returns:
            分析结果
        """
        pass
    
    @abstractmethod
    def extract_contact_info(self, profile_data: Dict) -> Optional[str]:
        """
        提取联系方式
        
        Args:
            profile_data: 个人/频道数据
            
        Returns:
            联系方式字符串
        """
        pass
