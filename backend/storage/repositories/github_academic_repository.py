# -*- coding: utf-8 -*-
"""
GitHub学术人士数据访问层
"""
from typing import List, Dict, Optional
from datetime import datetime
import json


class GitHubAcademicRepository:
    """GitHub学术人士仓库"""
    
    def __init__(self, db):
        self.db = db
    
    def save_academic_developer(self, developer_data: Dict) -> bool:
        """保存学术人士信息"""
        try:
            # 转换top_languages为JSON字符串
            top_languages = json.dumps(developer_data.get('top_languages', []))
            
            # 转换academic_indicators为JSON字符串
            academic_indicators = json.dumps(developer_data.get('academic_indicators', []))
            
            # 转换research_areas为JSON字符串
            research_areas = json.dumps(developer_data.get('research_areas', []))
            
            query = """
                INSERT OR REPLACE INTO github_academic_developers (
                    user_id, username, name, profile_url, avatar_url, bio,
                    company, location, blog, twitter, email, contact_info,
                    public_repos, followers, following,
                    analyzed_repos, total_stars, total_forks, avg_stars, avg_forks,
                    top_languages, original_repos, academic_indicators, research_areas,
                    status, discovered_from, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+8 hours'))
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
                academic_indicators,
                research_areas,
                developer_data.get('status', 'pending'),
                developer_data.get('discovered_from', '')
            )
            
            self.db.execute(query, params)
            return True
            
        except Exception as e:
            print(f"保存学术人士失败: {e}")
            return False
    
    def get_academic_developer_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取学术人士"""
        query = "SELECT * FROM github_academic_developers WHERE username = ?"
        return self.db.fetchone(query, (username,))
    
    def academic_developer_exists(self, username: str) -> bool:
        """检查学术人士是否已存在"""
        query = "SELECT COUNT(*) as count FROM github_academic_developers WHERE username = ?"
        result = self.db.fetchone(query, (username,))
        return result['count'] > 0 if result else False
    
    def get_qualified_academic_developers(self, limit: int = 100) -> List[Dict]:
        """获取合格的学术人士列表"""
        query = """
            SELECT * FROM github_academic_developers 
            WHERE status = 'qualified'
            ORDER BY total_stars DESC, followers DESC
            LIMIT ?
        """
        return self.db.fetchall(query, (limit,))
    
    def get_academic_developers_paginated(self, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Dict:
        """分页获取学术人士列表"""
        offset = (page - 1) * page_size
        
        # 构建查询条件
        where_clause = ""
        params = []
        if status:
            where_clause = "WHERE status = ?"
            params.append(status)
        
        # 查询总数
        count_query = f"SELECT COUNT(*) as total FROM github_academic_developers {where_clause}"
        total_result = self.db.fetchone(count_query, tuple(params))
        total = total_result['total'] if total_result else 0
        
        # 查询数据
        data_query = f"""
            SELECT * FROM github_academic_developers 
            {where_clause}
            ORDER BY total_stars DESC, followers DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        items = self.db.fetchall(data_query, tuple(params))
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        stats = {}
        
        # 总学术人士数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM github_academic_developers")
        stats['total_academic_developers'] = result['count'] if result else 0
        
        # 合格学术人士数
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM github_academic_developers WHERE status = 'qualified'"
        )
        stats['qualified_academic_developers'] = result['count'] if result else 0
        
        # 待分析学术人士数
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM github_academic_developers WHERE status = 'pending'"
        )
        stats['pending_academic_developers'] = result['count'] if result else 0
        
        return stats
    
    def update_academic_developer_status(self, username: str, status: str) -> bool:
        """更新学术人士状态"""
        try:
            query = "UPDATE github_academic_developers SET status = ?, last_updated = datetime('now', '+8 hours') WHERE username = ?"
            self.db.execute(query, (status, username))
            return True
        except Exception as e:
            print(f"更新学术人士状态失败: {e}")
            return False
