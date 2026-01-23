"""
数据模型定义
"""
from datetime import datetime
from enum import Enum


class KOLStatus(Enum):
    """KOL状态枚举"""
    PENDING = "pending"
    QUALIFIED = "qualified"
    REJECTED = "rejected"


class ExpansionStatus(Enum):
    """扩散队列状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"


class KOL:
    """KOL数据模型"""
    def __init__(self):
        self.id = None
        self.channel_id = None
        self.channel_name = None
        self.channel_url = None
        self.subscribers = 0
        self.total_videos = 0
        self.total_views = 0
        
        self.analyzed_videos = 0
        self.ai_videos = 0
        self.ai_ratio = 0.0
        
        self.avg_views = 0
        self.avg_likes = 0
        self.avg_comments = 0
        self.engagement_rate = 0.0
        
        self.last_video_date = None
        self.days_since_last_video = None
        
        self.contact_info = None
        
        self.status = KOLStatus.PENDING
        self.discovered_from = None
        self.discovered_at = datetime.now()
        self.last_updated = datetime.now()
        self.notes = None


class Video:
    """视频数据模型"""
    def __init__(self):
        self.id = None
        self.video_id = None
        self.channel_id = None
        self.title = None
        self.description = None
        self.published_at = None
        self.duration = 0
        
        self.views = 0
        self.likes = 0
        self.comments = 0
        
        self.is_ai_related = False
        self.matched_keywords = []
        self.scraped_at = datetime.now()
        self.video_url = None


class ExpansionQueue:
    """扩散队列数据模型"""
    def __init__(self):
        self.id = None
        self.channel_id = None
        self.priority = 0
        self.status = ExpansionStatus.PENDING
        self.created_at = datetime.now()
        self.processed_at = None
