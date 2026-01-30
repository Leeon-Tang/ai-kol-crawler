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
        分析GitHub开发者，并自动分类为商业/学术
        
        优化原则：只要满足一个不合格条件，立即返回，不再继续判断
        
        Args:
            username: 用户名
            
        Returns:
            分析结果，包含developer_type字段（'commercial'或'academic'）
        """
        logger.info(f"开始分析开发者: {username}")
        
        # 检查停止标志
        from utils.crawler_status import should_stop
        if should_stop():
            logger.warning(f"⚠️ 检测到停止信号，跳过分析 {username}")
            return {}
        
        # 获取用户信息
        user_info = self.scraper.get_user_info(username)
        if not user_info:
            logger.error(f"无法获取用户 {username} 的信息")
            return {}
        
        # 再次检查停止标志
        if should_stop():
            logger.warning(f"⚠️ 检测到停止信号，停止分析")
            return {}
        
        # 获取用户仓库
        repositories = self.scraper.get_user_repositories(username, max_repos=30)
        
        # 计算统计数据（所有类型都需要）
        stats = self._calculate_stats(repositories)
        
        # 先检查是否为学术人士
        is_academic, academic_indicators, research_areas = self.scraper.check_is_academic(user_info, repositories)
        
        # 如果是学术人士
        if is_academic:
            # 提取联系方式
            contact_info = self._extract_contact_info(user_info)
            
            # 学术人士也需要有联系方式
            if not contact_info:
                logger.info(f"学术人士 {username} 没有联系方式，尝试从commit提取...")
                commit_email = self.scraper._extract_email_from_commits(username)
                if commit_email:
                    user_info['email'] = commit_email
                    contact_info = self._extract_contact_info(user_info)
                    logger.info(f"✓ 从commit提取到邮箱: {commit_email}")
                else:
                    logger.info(f"✗ 学术人士无联系方式，不合格")
                    # 立即返回不合格结果，不再继续
                    return self._build_result(username, user_info, stats, repositories, 
                                             'academic', False, contact_info,
                                             academic_indicators=academic_indicators,
                                             research_areas=research_areas)
            
            # 学术人士合格
            logger.info(f"✓ {username} 学术人士合格")
            return self._build_result(username, user_info, stats, repositories,
                                     'academic', True, contact_info,
                                     academic_indicators=academic_indicators,
                                     research_areas=research_areas)
        
        # 不是学术人士，检查是否为商业/独立开发者
        is_indie = self.scraper.check_is_indie_developer(user_info, repositories)
        
        # 如果影响力不足，立即返回不合格（不再检查联系方式）
        if not is_indie:
            logger.info(f"✗ {username} 不符合独立开发者标准，不合格")
            return self._build_result(username, user_info, stats, repositories,
                                     'commercial', False, '')
        
        # 影响力合格，检查联系方式
        contact_info = self._extract_contact_info(user_info)
        
        if not contact_info:
            logger.info(f"商业开发者 {username} 没有联系方式，尝试从commit提取...")
            commit_email = self.scraper._extract_email_from_commits(username)
            if commit_email:
                user_info['email'] = commit_email
                contact_info = self._extract_contact_info(user_info)
                logger.info(f"✓ 从commit提取到邮箱: {commit_email}")
            else:
                logger.info(f"✗ 商业开发者无联系方式，不合格")
                # 立即返回不合格结果
                return self._build_result(username, user_info, stats, repositories,
                                         'commercial', False, contact_info)
        
        # 商业开发者合格
        logger.info(f"✓ {username} 商业开发者合格")
        return self._build_result(username, user_info, stats, repositories,
                                 'commercial', True, contact_info)
    
    def _build_result(self, username: str, user_info: Dict, stats: Dict, 
                     repositories: List[Dict], developer_type: str, 
                     is_qualified: bool, contact_info: str,
                     academic_indicators: List[str] = None,
                     research_areas: List[str] = None) -> Dict:
        """构建统一的返回结果"""
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
            
            'developer_type': developer_type,
            'status': 'qualified' if is_qualified else 'rejected',
            
            'created_at': user_info.get('created_at'),
            'updated_at': user_info.get('updated_at')
        }
        
        # 学术人士特有字段
        if developer_type == 'academic':
            result['academic_indicators'] = academic_indicators or []
            result['research_areas'] = research_areas or []
        else:
            # 商业开发者特有字段
            result['is_indie_developer'] = is_qualified
        
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
