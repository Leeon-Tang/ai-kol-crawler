# -*- coding: utf-8 -*-
"""
平台工厂 - 创建和管理不同平台的实例
"""
from typing import Dict, Optional
from .base import BasePlatform
from .youtube import YouTubePlatform
from .github import GitHubPlatform


class PlatformFactory:
    """平台工厂"""
    
    _platforms: Dict[str, BasePlatform] = {}
    
    @classmethod
    def register_platform(cls, platform: BasePlatform):
        """注册平台"""
        cls._platforms[platform.platform_name] = platform
    
    @classmethod
    def get_platform(cls, platform_name: str) -> Optional[BasePlatform]:
        """获取平台实例"""
        if platform_name not in cls._platforms:
            # 懒加载
            if platform_name == 'youtube':
                cls._platforms[platform_name] = YouTubePlatform()
            elif platform_name == 'github':
                cls._platforms[platform_name] = GitHubPlatform()
        
        return cls._platforms.get(platform_name)
    
    @classmethod
    def get_all_platforms(cls) -> Dict[str, str]:
        """获取所有支持的平台"""
        return {
            'youtube': 'YouTube',
            'github': 'GitHub'
        }
    
    @classmethod
    def get_platform_display_name(cls, platform_name: str) -> str:
        """获取平台显示名称"""
        platform = cls.get_platform(platform_name)
        return platform.platform_display_name if platform else platform_name
