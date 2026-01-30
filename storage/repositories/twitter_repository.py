# -*- coding: utf-8 -*-
"""
Twitter用户数据访问层
"""
from typing import List, Dict, Optional
from datetime import datetime
import json


class TwitterRepository:
    """Twitter用户仓库"""
    
    def __init__(self, db):
        self.db = db
    
    def save_user(self, user_data: Dict) -> bool:
        """保存用户信息"""
        try:
            # 转换matched_keywords为JSON字符串
            matched_keywords = json.dumps(user_data.get('matched_keywords', []))
            
            query = """
                INSERT OR REPLACE INTO twitter_users (
                    user_id, username, name, bio, location, website,
                    profile_url, avatar_url, banner_url,
                    followers_count, following_count, tweet_count,
                    verified, is_blue_verified, created_at,
                    analyzed_tweets, ai_tweets, ai_ratio,
                    avg_engagement, original_tweets, original_ratio,
                    quality_score, matched_keywords,
                    contact_info, status, discovered_from, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+8 hours'))
            """
            
            params = (
                user_data.get('user_id'),
                user_data.get('username'),
                user_data.get('name', ''),
                user_data.get('bio', ''),
                user_data.get('location', ''),
                user_data.get('website', ''),
                user_data.get('profile_url', ''),
                user_data.get('avatar_url', ''),
                user_data.get('banner_url', ''),
                user_data.get('followers_count', 0),
                user_data.get('following_count', 0),
                user_data.get('tweet_count', 0),
                1 if user_data.get('verified') else 0,
                1 if user_data.get('is_blue_verified') else 0,
                user_data.get('created_at', ''),
                user_data.get('analyzed_tweets', 0),
                user_data.get('ai_tweets', 0),
                user_data.get('ai_ratio', 0.0),
                user_data.get('avg_engagement', 0.0),
                user_data.get('original_tweets', 0),
                user_data.get('original_ratio', 0.0),
                user_data.get('quality_score', 0.0),
                matched_keywords,
                user_data.get('contact_info', ''),
                user_data.get('status', 'pending'),
                user_data.get('discovered_from', '')
            )
            
            self.db.execute(query, params)
            return True
            
        except Exception as e:
            print(f"保存用户失败: {e}")
            return False
    
    def save_tweet(self, tweet_data: Dict) -> bool:
        """保存推文信息"""
        try:
            query = """
                INSERT OR REPLACE INTO twitter_tweets (
                    tweet_id, username, text, created_at,
                    retweet_count, like_count, reply_count, quote_count, view_count,
                    is_retweet, is_quote, is_ai_related, language, tweet_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                tweet_data.get('tweet_id'),
                tweet_data.get('username'),
                tweet_data.get('text', ''),
                tweet_data.get('created_at', ''),
                tweet_data.get('retweet_count', 0),
                tweet_data.get('like_count', 0),
                tweet_data.get('reply_count', 0),
                tweet_data.get('quote_count', 0),
                tweet_data.get('view_count', 0),
                1 if tweet_data.get('is_retweet') else 0,
                1 if tweet_data.get('is_quote') else 0,
                1 if tweet_data.get('is_ai_related') else 0,
                tweet_data.get('language', ''),
                tweet_data.get('tweet_url', '')
            )
            
            self.db.execute(query, params)
            return True
            
        except Exception as e:
            print(f"保存推文失败: {e}")
            return False
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        query = "SELECT * FROM twitter_users WHERE username = ?"
        return self.db.fetchone(query, (username,))
    
    def user_exists(self, username: str) -> bool:
        """检查用户是否已存在"""
        query = "SELECT COUNT(*) as count FROM twitter_users WHERE username = ?"
        result = self.db.fetchone(query, (username,))
        return result['count'] > 0 if result else False
    
    def get_qualified_users(self, limit: int = 100) -> List[Dict]:
        """获取合格的用户列表"""
        query = """
            SELECT * FROM twitter_users 
            WHERE status = 'qualified'
            ORDER BY quality_score DESC, followers_count DESC
            LIMIT ?
        """
        return self.db.fetchall(query, (limit,))
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        stats = {}
        
        # 总用户数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM twitter_users")
        stats['total_users'] = result['count'] if result else 0
        
        # 合格用户数
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM twitter_users WHERE status = 'qualified'"
        )
        stats['qualified_users'] = result['count'] if result else 0
        
        # 待分析用户数
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM twitter_users WHERE status = 'pending'"
        )
        stats['pending_users'] = result['count'] if result else 0
        
        # 总推文数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM twitter_tweets")
        stats['total_tweets'] = result['count'] if result else 0
        
        # AI相关推文数
        result = self.db.fetchone(
            "SELECT COUNT(*) as count FROM twitter_tweets WHERE is_ai_related = 1"
        )
        stats['ai_tweets'] = result['count'] if result else 0
        
        return stats
    
    def update_user_status(self, username: str, status: str) -> bool:
        """更新用户状态"""
        try:
            query = "UPDATE twitter_users SET status = ?, last_updated = datetime('now', '+8 hours') WHERE username = ?"
            self.db.execute(query, (status, username))
            return True
        except Exception as e:
            print(f"更新用户状态失败: {e}")
            return False
    
    def get_recent_users(self, limit: int = 10) -> List[Dict]:
        """获取最近发现的用户"""
        query = """
            SELECT * FROM twitter_users 
            ORDER BY discovered_at DESC 
            LIMIT ?
        """
        return self.db.fetchall(query, (limit,))
