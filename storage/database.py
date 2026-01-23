"""
数据库连接和表初始化 - 支持SQLite和PostgreSQL
"""
import json
import os
from utils.config_loader import get_absolute_path, get_project_root


class Database:
    """数据库管理类"""
    
    def __init__(self, config_path='config/config.json', use_sqlite=True):
        config_path = get_absolute_path(config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.use_sqlite = use_sqlite
        self.db_config = config.get('database', {})
        self.conn = None
        self.cursor = None
        self.project_root = get_project_root()
    
    def connect(self):
        """建立数据库连接"""
        if self.use_sqlite:
            # 使用SQLite - 使用绝对路径
            import sqlite3
            db_dir = os.path.join(self.project_root, 'data')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'ai_kol_crawler.db')
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        else:
            # 使用PostgreSQL
            import psycopg2
            from psycopg2.extras import RealDictCursor
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
    
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def init_tables(self):
        """初始化数据库表"""
        
        if self.use_sqlite:
            # SQLite版本
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS kols (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    channel_id TEXT UNIQUE NOT NULL,
                    channel_name TEXT,
                    channel_url TEXT,
                    subscribers INTEGER DEFAULT 0,
                    total_videos INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    
                    analyzed_videos INTEGER DEFAULT 0,
                    ai_videos INTEGER DEFAULT 0,
                    ai_ratio REAL DEFAULT 0,
                    
                    avg_views INTEGER DEFAULT 0,
                    avg_likes INTEGER DEFAULT 0,
                    avg_comments INTEGER DEFAULT 0,
                    engagement_rate REAL DEFAULT 0,
                    
                    last_video_date TEXT,
                    days_since_last_video INTEGER,
                    
                    contact_info TEXT,
                    status TEXT DEFAULT 'pending',
                    discovered_from TEXT,
                    discovered_at TEXT DEFAULT (datetime('now')),
                    last_updated TEXT DEFAULT (datetime('now')),
                    notes TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    video_id TEXT UNIQUE NOT NULL,
                    channel_id TEXT,
                    title TEXT,
                    description TEXT,
                    published_at TEXT,
                    duration INTEGER DEFAULT 0,
                    
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    
                    is_ai_related INTEGER DEFAULT 0,
                    matched_keywords TEXT,
                    scraped_at TEXT DEFAULT (datetime('now')),
                    video_url TEXT,
                    FOREIGN KEY (channel_id) REFERENCES kols(channel_id)
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS expansion_queue (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    channel_id TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT (datetime('now')),
                    processed_at TEXT
                )
            """)
            
            # 创建索引
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_kols_status ON kols(status)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_kols_ai_ratio ON kols(ai_ratio)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_expansion_status ON expansion_queue(status)")
            
        else:
            # PostgreSQL版本（原有代码）
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS kols (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    channel_id VARCHAR(255) UNIQUE NOT NULL,
                    channel_name VARCHAR(500),
                    channel_url TEXT,
                    subscribers INTEGER DEFAULT 0,
                    total_videos INTEGER DEFAULT 0,
                    total_views BIGINT DEFAULT 0,
                    
                    analyzed_videos INTEGER DEFAULT 0,
                    ai_videos INTEGER DEFAULT 0,
                    ai_ratio FLOAT DEFAULT 0,
                    
                    avg_views INTEGER DEFAULT 0,
                    avg_likes INTEGER DEFAULT 0,
                    avg_comments INTEGER DEFAULT 0,
                    engagement_rate FLOAT DEFAULT 0,
                    
                    last_video_date TIMESTAMP,
                    days_since_last_video INTEGER,
                    
                    contact_info TEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    discovered_from TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    video_id VARCHAR(255) UNIQUE NOT NULL,
                    channel_id VARCHAR(255) REFERENCES kols(channel_id),
                    title TEXT,
                    description TEXT,
                    published_at TIMESTAMP,
                    duration INTEGER DEFAULT 0,
                    
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    
                    is_ai_related BOOLEAN DEFAULT FALSE,
                    matched_keywords JSONB,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    video_url TEXT
                )
            """)
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS expansion_queue (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    channel_id VARCHAR(255) NOT NULL,
                    priority INTEGER DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            """)
            
            # 创建索引
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_kols_status ON kols(status)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_kols_ai_ratio ON kols(ai_ratio)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_expansion_status ON expansion_queue(status)")
        
        self.conn.commit()
    
    def execute(self, query, params=None):
        """执行SQL查询"""
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        self.conn.commit()
    
    def fetchone(self, query, params=None):
        """查询单条记录"""
        # 为每次查询创建新游标，避免递归使用
        if self.use_sqlite:
            cursor = self.conn.cursor()
        else:
            cursor = self.cursor
            
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchone()
        
        # SQLite 需要关闭游标
        if self.use_sqlite:
            cursor.close()
            
        if result and self.use_sqlite:
            return dict(result)
        return result
    
    def fetchall(self, query, params=None):
        """查询多条记录"""
        # 为每次查询创建新游标，避免递归使用
        if self.use_sqlite:
            cursor = self.conn.cursor()
        else:
            cursor = self.cursor
            
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        
        # SQLite 需要关闭游标
        if self.use_sqlite:
            cursor.close()
            
        if results and self.use_sqlite:
            return [dict(row) for row in results]
        return results
