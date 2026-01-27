# -*- coding: utf-8 -*-
"""
GitHub开发者数据访问层
"""
from typing import List, Dict, Optional
from datetime import datetime
import json


class GitHubRepository:
    """GitHub开发者仓库"""
    
    def __init__(self, db):
        self.db = db
    
    def save_developer(self, developer_data: Dict) -> bool:
        """保存开发者信息"""
        try:
            # 转换top_languages为JSON字符串
            top_languages = json.dumps(developer_data.get('top_languages', []))
            
            query = """
                INSERT OR REPLACE INTO github_developers (
                    user_id, username, name, profile_url, avatar_url, bio,
                    company, location, blog, twitter, email, contact_info,
                    public_repos, followers, following,
                    analyzed_repos, total_stars, total_forks, avg_stars, avg_forks,
                    top_languages, original_repos, is_indie_developer, status,
                    discovered_from, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+8 hours'))
            """
            
            params = (
                developer_data.get('user_id'),
                developer_data.get('username'),
                developer_data.get('name', ''),
                developer_data.get('profile_url', ''),
                developer_data.get('avatar_url', ''),
                developer_data.get('bio', ''),
                developer_data.get('company', ''),
                developer_data.get('location', ''),
                developer_data.get('blog', ''),
                developer_data.get('twitter', ''),
                developer_data.get('email', ''),
                developer_data.get('contact_info', ''),
                developer_data.get('public_repos', 0),
                developer_data.get('followers', 0),
                developer_data.get('following', 0),
                developer_data.get('analyzed_repos', 0),
                developer_data.get('total_stars', 0),
                developer_data.get('total_forks', 0),
                developer_data.get('avg_stars', 0),
                developer_data.get('avg_forks', 0),
                top_languages,
                developer_data.get('original_repos', 0),
                1 if developer_data.get('is_indie_developer') else 0,
                developer_data.get('status', 'pending'),
                developer_data.get('discovered_from', '')
            )
            
            self.db.execute(query, params)
            return True
            
        except Exception as e:
            print(f"保存开发者失败: {e}")
            return False
    
    def save_repository(self, repo_data: Dict) -> bool:
        """保存仓库信息"""
        try:
            query = """
                INSERT OR REPLACE INTO github_repositories (
                    repo_id, repo_name, repo_url, username, description,
                    stars, forks, language, is_fork, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                repo_data.get('repo_id'),
                repo_data.get('repo_name'),
                repo_data.get('repo_url', ''),
                repo_data.get('username'),
                repo_data.get('description', ''),
                repo_data.get('stars', 0),
                repo_data.get('forks', 0),
                repo_data.get('language', ''),
                1 if repo_data.get('is_fork') else 0,
                repo_data.get('created_at'),
                repo_data.get('updated_at')
            )
            
            self.db.execute(query, params)
            return True
            
        except Exception as e:
            print(f"保存仓库失败: {e}")
            return False
    
    def get_developer_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取开发者"""
        query = "SELECT * FROM github_developers WHERE username = ?"
        return self.db.fetchone(query, (username,))
    
    def developer_exists(self, username: str) -> bool:
        """检查开发者是否已存在"""
        query = "SELECT COUNT(*) as count FROM github_developers WHERE username = ?"
        result = self.db.fetchone(query, (username,))
        return result['count'] > 0 if result else False
    
    def get_qualified_developers(self, limit: int = 100) -> List[Dict]:
        """获取合格的开发者列表"""
        query = """
            SELECT * FROM github_developers 
            WHERE status = 'qualified' AND is_indie_developer = 1
            ORDER BY total_stars DESC, followers DESC
            LIMIT ?
        """
        return self.db.fetchall(query, (limit,))
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        stats = {}
        
        # 总开发者数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM github_developers")
        stats['total_developers'] = result['count'] if result else 0
        
        # 合格开发者数
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM github_developers WHERE status = 'qualified' AND is_indie_developer = 1"
        )
        stats['qualified_developers'] = result['count'] if result else 0
        
        # 待分析开发者数
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM github_developers WHERE status = 'pending'"
        )
        stats['pending_developers'] = result['count'] if result else 0
        
        # 总仓库数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM github_repositories")
        stats['total_repositories'] = result['count'] if result else 0
        
        return stats
    
    def update_developer_status(self, username: str, status: str) -> bool:
        """更新开发者状态"""
        try:
            query = "UPDATE github_developers SET status = ?, last_updated = datetime('now', '+8 hours') WHERE username = ?"
            self.db.execute(query, (status, username))
            return True
        except Exception as e:
            print(f"更新开发者状态失败: {e}")
            return False
