# -*- coding: utf-8 -*-
"""
GitHub开发者分析器
"""
from typing import Dict, List
from utils.logger import setup_logger
from .scraper import GitHubScraper

logger = setup_logger()


class GitHubAnalyzer:
    """GitHub开发者分析器"""
    
    def __init__(self, scraper: GitHubScraper = None):
        self.scraper = scraper or GitHubScraper()
    
    def analyze_developer(self, username: str) -> Dict:
        """
        分析GitHub开发者
        
        Args:
            username: 用户名
            
        Returns:
            分析结果
        """
        logger.info(f"开始分析开发者: {username}")
        
        # 获取用户信息
        user_info = self.scraper.get_user_info(username)
        if not user_info:
            logger.error(f"无法获取用户 {username} 的信息")
            return {}
        
        # 获取用户仓库
        repositories = self.scraper.get_user_repositories(username, max_repos=30)
        
        # 判断是否为独立开发者
        is_indie = self.scraper.check_is_indie_developer(user_info, repositories)
        
        # 计算统计数据
        stats = self._calculate_stats(repositories)
        
        # 提取联系方式
        contact_info = self._extract_contact_info(user_info)
        
        # 如果没有任何联系方式，标记为不合格
        if not contact_info:
            logger.info(f"开发者 {username} 没有任何联系方式，标记为不合格")
            is_indie = False
        
        result = {
            'username': username,
            'user_id': user_info['user_id'],
            'name': user_info.get('name', ''),
            'profile_url': user_info['profile_url'],
            'avatar_url': user_info.get('avatar_url', ''),
            'bio': user_info.get('bio', ''),
            'company': user_info.get('company', ''),
            'location': user_info.get('location', ''),
            'blog': user_info.get('blog', ''),
            'twitter': user_info.get('twitter', ''),
            'email': user_info.get('email', ''),
            'contact_info': contact_info,
            
            'public_repos': user_info.get('public_repos', 0),
            'followers': user_info.get('followers', 0),
            'following': user_info.get('following', 0),
            
            'analyzed_repos': len(repositories),
            'total_stars': stats['total_stars'],
            'total_forks': stats['total_forks'],
            'avg_stars': stats['avg_stars'],
            'avg_forks': stats['avg_forks'],
            'top_languages': stats['top_languages'],
            'original_repos': stats['original_repos'],
            
            'is_indie_developer': is_indie,
            'status': 'qualified' if is_indie else 'rejected',
            
            'created_at': user_info.get('created_at'),
            'updated_at': user_info.get('updated_at')
        }
        
        logger.info(f"开发者 {username} 分析完成: {'合格' if is_indie else '不合格'}")
        return result
    
    def _calculate_stats(self, repositories: List[Dict]) -> Dict:
        """计算仓库统计数据"""
        if not repositories:
            return {
                'total_stars': 0,
                'total_forks': 0,
                'avg_stars': 0,
                'avg_forks': 0,
                'top_languages': [],
                'original_repos': 0
            }
        
        total_stars = sum(r.get('stars', 0) for r in repositories)
        total_forks = sum(r.get('forks', 0) for r in repositories)
        original_repos = len([r for r in repositories if not r.get('is_fork', False)])
        
        # 统计语言
        language_count = {}
        for repo in repositories:
            lang = repo.get('language')
            if lang:
                language_count[lang] = language_count.get(lang, 0) + 1
        
        # 排序获取top语言
        top_languages = sorted(language_count.items(), key=lambda x: x[1], reverse=True)[:5]
        top_languages = [lang for lang, _ in top_languages]
        
        return {
            'total_stars': total_stars,
            'total_forks': total_forks,
            'avg_stars': total_stars // len(repositories) if repositories else 0,
            'avg_forks': total_forks // len(repositories) if repositories else 0,
            'top_languages': top_languages,
            'original_repos': original_repos
        }
    
    def _extract_contact_info(self, user_info: Dict) -> str:
        """提取联系方式（带图标）"""
        contacts = []
        
        if user_info.get('email'):
            contacts.append(f"📧 {user_info['email']}")
        
        if user_info.get('blog'):
            contacts.append(f"🌐 {user_info['blog']}")
        
        if user_info.get('twitter'):
            contacts.append(f"🐦 @{user_info['twitter']}")
        
        return ' | '.join(contacts) if contacts else ''
