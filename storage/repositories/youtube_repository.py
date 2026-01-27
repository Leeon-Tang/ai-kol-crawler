# -*- coding: utf-8 -*-
"""
YouTube KOL数据访问层 - CRUD操作
"""
from datetime import datetime
import json


class YouTubeRepository:
    """YouTube KOL数据仓库"""
    
    def __init__(self, db):
        self.db = db
    
    def add_kol(self, kol_data):
        """添加KOL"""
        query = """
            INSERT OR IGNORE INTO youtube_kols (
                channel_id, channel_name, channel_url, subscribers, total_videos, total_views,
                analyzed_videos, ai_videos, ai_ratio, avg_views, avg_likes, avg_comments, engagement_rate,
                last_video_date, days_since_last_video, contact_info, status, discovered_from
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            kol_data['channel_id'], kol_data['channel_name'], kol_data['channel_url'],
            kol_data['subscribers'], kol_data['total_videos'], kol_data['total_views'],
            kol_data['analyzed_videos'], kol_data['ai_videos'], kol_data['ai_ratio'],
            kol_data['avg_views'], kol_data['avg_likes'], kol_data.get('avg_comments', 0), kol_data['engagement_rate'],
            kol_data.get('last_video_date'), kol_data.get('days_since_last_video'),
            kol_data.get('contact_info'), kol_data['status'], kol_data['discovered_from']
        )
        
        self.db.execute(query, params)
    
    def update_kol(self, channel_id, update_data):
        """更新KOL信息"""
        from datetime import datetime, timedelta, timezone
        # 使用北京时间
        beijing_time = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()
        update_data['last_updated'] = beijing_time
        
        set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
        query = f"UPDATE youtube_kols SET {set_clause} WHERE channel_id = ?"
        params = list(update_data.values()) + [channel_id]
        
        self.db.execute(query, params)
    
    def get_kol_by_channel_id(self, channel_id):
        """根据频道ID获取KOL"""
        query = "SELECT * FROM youtube_kols WHERE channel_id = ?"
        return self.db.fetchone(query, (channel_id,))
    
    def get_qualified_kols(self, limit=None):
        """获取所有合格的KOL"""
        query = "SELECT * FROM youtube_kols WHERE status = 'qualified' ORDER BY ai_ratio DESC"
        if limit:
            query += f" LIMIT {limit}"
        return self.db.fetchall(query)
    
    def get_pending_kols(self):
        """获取待分析的KOL"""
        query = "SELECT * FROM youtube_kols WHERE status = 'pending'"
        return self.db.fetchall(query)
    
    def count_qualified_kols(self):
        """统计合格KOL数量"""
        query = "SELECT COUNT(*) as count FROM youtube_kols WHERE status = 'qualified'"
        result = self.db.fetchone(query)
        return result['count'] if result else 0
    
    def exists(self, channel_id):
        """检查KOL是否已存在"""
        query = "SELECT COUNT(*) as count FROM youtube_kols WHERE channel_id = ?"
        result = self.db.fetchone(query, (channel_id,))
        return result['count'] > 0 if result else False
    
    def add_video(self, video_data):
        """添加视频"""
        query = """
            INSERT OR IGNORE INTO youtube_videos (
                video_id, channel_id, title, description, published_at, duration,
                views, likes, comments, is_ai_related, matched_keywords, video_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            video_data['video_id'], video_data['channel_id'], video_data['title'],
            video_data['description'], video_data['published_at'], video_data['duration'],
            video_data['views'], video_data['likes'], video_data['comments'],
            1 if video_data['is_ai_related'] else 0,
            json.dumps(video_data['matched_keywords']),
            video_data['video_url']
        )
        self.db.execute(query, params)
    
    def get_videos_by_channel(self, channel_id, limit=None):
        """获取频道的视频"""
        query = "SELECT * FROM youtube_videos WHERE channel_id = ? ORDER BY published_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        return self.db.fetchall(query, (channel_id,))
    
    def add_to_expansion_queue(self, channel_id, priority=0):
        """添加到扩散队列"""
        query = """
            INSERT OR IGNORE INTO youtube_expansion_queue (channel_id, priority)
            VALUES (?, ?)
        """
        self.db.execute(query, (channel_id, priority))
    
    def get_expansion_queue(self, limit=10):
        """获取待扩散的KOL"""
        query = """
            SELECT * FROM youtube_expansion_queue 
            WHERE status = 'pending' 
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        """
        return self.db.fetchall(query, (limit,))
    
    def update_expansion_status(self, queue_id, status):
        """更新扩散队列状态"""
        query = """
            UPDATE youtube_expansion_queue 
            SET status = ?, processed_at = datetime('now', '+8 hours')
            WHERE id = ?
        """
        self.db.execute(query, (status, queue_id))
    
    def get_statistics(self):
        """获取统计信息"""
        stats = {}
        
        # 总KOL数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM youtube_kols")
        stats['total_kols'] = result['count'] if result else 0
        
        # 合格KOL数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM youtube_kols WHERE status = 'qualified'")
        stats['qualified_kols'] = result['count'] if result else 0
        
        # 待分析KOL数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM youtube_kols WHERE status = 'pending'")
        stats['pending_kols'] = result['count'] if result else 0
        
        # 总视频数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM youtube_videos")
        stats['total_videos'] = result['count'] if result else 0
        
        # 待扩散队列
        result = self.db.fetchone("SELECT COUNT(*) as count FROM youtube_expansion_queue WHERE status = 'pending'")
        stats['pending_expansions'] = result['count'] if result else 0
        
        return stats
