"""
KOL数据访问层 - CRUD操作 - 支持SQLite和PostgreSQL
"""
from datetime import datetime
import json


class KOLRepository:
    """KOL数据仓库"""
    
    def __init__(self, db):
        self.db = db
        # 检测数据库类型
        self.use_sqlite = getattr(db, 'use_sqlite', False)
        self.placeholder = '?' if self.use_sqlite else '%s'
    
    def add_kol(self, kol_data):
        """添加KOL"""
        if self.use_sqlite:
            query = f"""
                INSERT OR IGNORE INTO kols (
                    channel_id, channel_name, channel_url, subscribers, total_videos, total_views,
                    analyzed_videos, ai_videos, ai_ratio, avg_views, avg_likes, avg_comments, engagement_rate,
                    last_video_date, days_since_last_video, contact_info, status, discovered_from
                ) VALUES ({','.join(['?']*18)})
            """
        else:
            query = f"""
                INSERT INTO kols (
                    channel_id, channel_name, channel_url, subscribers, total_videos, total_views,
                    analyzed_videos, ai_videos, ai_ratio, avg_views, avg_likes, avg_comments, engagement_rate,
                    last_video_date, days_since_last_video, contact_info, status, discovered_from
                ) VALUES ({','.join(['%s']*18)})
                ON CONFLICT (channel_id) DO NOTHING
                RETURNING id
            """
        
        params = (
            kol_data['channel_id'], kol_data['channel_name'], kol_data['channel_url'],
            kol_data['subscribers'], kol_data['total_videos'], kol_data['total_views'],
            kol_data['analyzed_videos'], kol_data['ai_videos'], kol_data['ai_ratio'],
            kol_data['avg_views'], kol_data['avg_likes'], kol_data.get('avg_comments', 0), kol_data['engagement_rate'],
            kol_data.get('last_video_date'), kol_data.get('days_since_last_video'),
            kol_data.get('contact_info'), kol_data['status'], kol_data['discovered_from']
        )
        
        if self.use_sqlite:
            self.db.execute(query, params)
            return None
        else:
            result = self.db.fetchone(query, params)
            return result['id'] if result else None
    
    def update_kol(self, channel_id, update_data):
        """更新KOL信息"""
        update_data['last_updated'] = datetime.now().isoformat() if self.use_sqlite else datetime.now()
        
        set_clause = ', '.join([f"{key} = {self.placeholder}" for key in update_data.keys()])
        query = f"UPDATE kols SET {set_clause} WHERE channel_id = {self.placeholder}"
        params = list(update_data.values()) + [channel_id]
        
        self.db.execute(query, params)
    
    def get_kol_by_channel_id(self, channel_id):
        """根据频道ID获取KOL"""
        query = f"SELECT * FROM kols WHERE channel_id = {self.placeholder}"
        return self.db.fetchone(query, (channel_id,))
    
    def get_qualified_kols(self, limit=None):
        """获取所有合格的KOL"""
        query = "SELECT * FROM kols WHERE status = 'qualified' ORDER BY ai_ratio DESC"
        if limit:
            query += f" LIMIT {limit}"
        return self.db.fetchall(query)
    
    def get_pending_kols(self):
        """获取待分析的KOL"""
        query = "SELECT * FROM kols WHERE status = 'pending'"
        return self.db.fetchall(query)
    
    def count_qualified_kols(self):
        """统计合格KOL数量"""
        query = "SELECT COUNT(*) as count FROM kols WHERE status = 'qualified'"
        result = self.db.fetchone(query)
        return result['count'] if result else 0
    
    def exists(self, channel_id):
        """检查KOL是否已存在"""
        if self.use_sqlite:
            query = f"SELECT COUNT(*) as count FROM kols WHERE channel_id = {self.placeholder}"
            result = self.db.fetchone(query, (channel_id,))
            return result['count'] > 0 if result else False
        else:
            query = f"SELECT EXISTS(SELECT 1 FROM kols WHERE channel_id = {self.placeholder})"
            result = self.db.fetchone(query, (channel_id,))
            return result['exists'] if result else False
    
    def add_video(self, video_data):
        """添加视频"""
        if self.use_sqlite:
            query = f"""
                INSERT OR IGNORE INTO videos (
                    video_id, channel_id, title, description, published_at, duration,
                    views, likes, comments, is_ai_related, matched_keywords, video_url
                ) VALUES ({','.join(['?']*12)})
            """
        else:
            query = f"""
                INSERT INTO videos (
                    video_id, channel_id, title, description, published_at, duration,
                    views, likes, comments, is_ai_related, matched_keywords, video_url
                ) VALUES ({','.join(['%s']*12)})
                ON CONFLICT (video_id) DO NOTHING
            """
        
        params = (
            video_data['video_id'], video_data['channel_id'], video_data['title'],
            video_data['description'], video_data['published_at'], video_data['duration'],
            video_data['views'], video_data['likes'], video_data['comments'],
            1 if video_data['is_ai_related'] else 0,  # SQLite uses INTEGER for boolean
            json.dumps(video_data['matched_keywords']),
            video_data['video_url']
        )
        self.db.execute(query, params)
    
    def get_videos_by_channel(self, channel_id, limit=None):
        """获取频道的视频"""
        query = f"SELECT * FROM videos WHERE channel_id = {self.placeholder} ORDER BY published_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        return self.db.fetchall(query, (channel_id,))
    
    def add_to_expansion_queue(self, channel_id, priority=0):
        """添加到扩散队列"""
        if self.use_sqlite:
            query = f"""
                INSERT OR IGNORE INTO expansion_queue (channel_id, priority)
                VALUES ({self.placeholder}, {self.placeholder})
            """
        else:
            query = f"""
                INSERT INTO expansion_queue (channel_id, priority)
                VALUES ({self.placeholder}, {self.placeholder})
                ON CONFLICT DO NOTHING
            """
        self.db.execute(query, (channel_id, priority))
    
    def get_expansion_queue(self, limit=10):
        """获取待扩散的KOL"""
        query = f"""
            SELECT * FROM expansion_queue 
            WHERE status = 'pending' 
            ORDER BY priority DESC, created_at ASC
            LIMIT {self.placeholder}
        """
        return self.db.fetchall(query, (limit,))
    
    def update_expansion_status(self, queue_id, status):
        """更新扩散队列状态"""
        if self.use_sqlite:
            query = f"""
                UPDATE expansion_queue 
                SET status = {self.placeholder}, processed_at = datetime('now')
                WHERE id = {self.placeholder}
            """
        else:
            query = f"""
                UPDATE expansion_queue 
                SET status = {self.placeholder}, processed_at = CURRENT_TIMESTAMP 
                WHERE id = {self.placeholder}
            """
        self.db.execute(query, (status, queue_id))
    
    def get_statistics(self):
        """获取统计信息"""
        stats = {}
        
        # 总KOL数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM kols")
        stats['total_kols'] = result['count'] if result else 0
        
        # 合格KOL数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM kols WHERE status = 'qualified'")
        stats['qualified_kols'] = result['count'] if result else 0
        
        # 待分析KOL数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM kols WHERE status = 'pending'")
        stats['pending_kols'] = result['count'] if result else 0
        
        # 总视频数
        result = self.db.fetchone("SELECT COUNT(*) as count FROM videos")
        stats['total_videos'] = result['count'] if result else 0
        
        # 待扩散队列
        result = self.db.fetchone("SELECT COUNT(*) as count FROM expansion_queue WHERE status = 'pending'")
        stats['pending_expansions'] = result['count'] if result else 0
        
        return stats
