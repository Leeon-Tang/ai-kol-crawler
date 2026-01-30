# -*- coding: utf-8 -*-
"""
统一数据库管理 - 支持多平台
"""
import sqlite3
import os
import json
from utils.config_loader import get_project_root


class Database:
    """统一数据库管理类"""
    
    def __init__(self):
        self.project_root = get_project_root()
        db_dir = os.path.join(self.project_root, 'data')
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, 'ai_kol_crawler.db')
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """建立数据库连接"""
        try:
            # 添加超时和其他参数以避免I/O错误
            self.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0,  # 增加超时时间
                isolation_level=None  # 自动提交模式，减少锁定
            )
            self.conn.row_factory = sqlite3.Row
            # 启用WAL模式以提高并发性能
            self.conn.execute('PRAGMA journal_mode=WAL')
            # 设置同步模式为NORMAL以提高性能
            self.conn.execute('PRAGMA synchronous=NORMAL')
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def check_integrity(self):
        """检查数据库完整性"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            cursor.close()
            return result[0] == 'ok'
        except Exception as e:
            print(f"数据库完整性检查失败: {e}")
            return False
    
    def repair_database(self):
        """尝试修复数据库"""
        try:
            # 关闭当前连接
            self.close()
            
            # 创建备份
            import shutil
            from datetime import datetime
            backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_path, backup_path)
            print(f"数据库已备份到: {backup_path}")
            
            # 重新连接并尝试修复
            self.connect()
            self.conn.execute("VACUUM")
            self.conn.commit()
            
            return True
        except Exception as e:
            print(f"数据库修复失败: {e}")
            return False
    
    def init_tables(self):
        """初始化所有平台的数据库表"""
        self._init_youtube_tables()
        self._init_github_tables()
        self._init_twitter_tables()
        self.conn.commit()
    
    def _init_youtube_tables(self):
        """初始化YouTube表"""
        # YouTube KOL表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_kols (
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
                discovered_at TEXT DEFAULT (datetime('now', '+8 hours')),
                last_updated TEXT DEFAULT (datetime('now', '+8 hours')),
                notes TEXT
            )
        """)
        
        # YouTube视频表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_videos (
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
                scraped_at TEXT DEFAULT (datetime('now', '+8 hours')),
                video_url TEXT,
                FOREIGN KEY (channel_id) REFERENCES youtube_kols(channel_id)
            )
        """)
        
        # YouTube扩散队列
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_expansion_queue (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                channel_id TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now', '+8 hours')),
                processed_at TEXT
            )
        """)
        
        # 创建索引
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_youtube_kols_status ON youtube_kols(status)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_youtube_kols_ai_ratio ON youtube_kols(ai_ratio)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_youtube_videos_channel ON youtube_videos(channel_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_youtube_expansion_status ON youtube_expansion_queue(status)")
    
    def _init_github_tables(self):
        """初始化GitHub表"""
        # GitHub开发者表（商业/独立开发者）
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_developers (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                name TEXT,
                profile_url TEXT,
                avatar_url TEXT,
                bio TEXT,
                company TEXT,
                location TEXT,
                blog TEXT,
                twitter TEXT,
                email TEXT,
                contact_info TEXT,
                
                public_repos INTEGER DEFAULT 0,
                followers INTEGER DEFAULT 0,
                following INTEGER DEFAULT 0,
                
                analyzed_repos INTEGER DEFAULT 0,
                total_stars INTEGER DEFAULT 0,
                total_forks INTEGER DEFAULT 0,
                avg_stars INTEGER DEFAULT 0,
                avg_forks INTEGER DEFAULT 0,
                top_languages TEXT,
                original_repos INTEGER DEFAULT 0,
                
                is_indie_developer INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                discovered_from TEXT,
                discovered_at TEXT DEFAULT (datetime('now', '+8 hours')),
                last_updated TEXT DEFAULT (datetime('now', '+8 hours')),
                notes TEXT
            )
        """)
        
        # GitHub学术人士表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_academic_developers (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                name TEXT,
                profile_url TEXT,
                avatar_url TEXT,
                bio TEXT,
                company TEXT,
                location TEXT,
                blog TEXT,
                twitter TEXT,
                email TEXT,
                contact_info TEXT,
                
                public_repos INTEGER DEFAULT 0,
                followers INTEGER DEFAULT 0,
                following INTEGER DEFAULT 0,
                
                analyzed_repos INTEGER DEFAULT 0,
                total_stars INTEGER DEFAULT 0,
                total_forks INTEGER DEFAULT 0,
                avg_stars INTEGER DEFAULT 0,
                avg_forks INTEGER DEFAULT 0,
                top_languages TEXT,
                original_repos INTEGER DEFAULT 0,
                
                academic_indicators TEXT,
                research_areas TEXT,
                status TEXT DEFAULT 'pending',
                discovered_from TEXT,
                discovered_at TEXT DEFAULT (datetime('now', '+8 hours')),
                last_updated TEXT DEFAULT (datetime('now', '+8 hours')),
                notes TEXT
            )
        """)
        
        # GitHub仓库表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS github_repositories (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                repo_id INTEGER UNIQUE NOT NULL,
                repo_name TEXT NOT NULL,
                repo_url TEXT,
                username TEXT,
                description TEXT,
                stars INTEGER DEFAULT 0,
                forks INTEGER DEFAULT 0,
                language TEXT,
                is_fork INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                scraped_at TEXT DEFAULT (datetime('now', '+8 hours')),
                FOREIGN KEY (username) REFERENCES github_developers(username)
            )
        """)
        
        # 创建索引
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_developers_status ON github_developers(status)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_developers_indie ON github_developers(is_indie_developer)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_academic_status ON github_academic_developers(status)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_github_repos_username ON github_repositories(username)")
    
    def _init_twitter_tables(self):
        """初始化Twitter表"""
        # Twitter用户表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS twitter_users (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                name TEXT,
                bio TEXT,
                location TEXT,
                website TEXT,
                profile_url TEXT,
                avatar_url TEXT,
                banner_url TEXT,
                
                followers_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                tweet_count INTEGER DEFAULT 0,
                verified INTEGER DEFAULT 0,
                is_blue_verified INTEGER DEFAULT 0,
                created_at TEXT,
                
                analyzed_tweets INTEGER DEFAULT 0,
                ai_tweets INTEGER DEFAULT 0,
                ai_ratio REAL DEFAULT 0,
                avg_engagement REAL DEFAULT 0,
                original_tweets INTEGER DEFAULT 0,
                original_ratio REAL DEFAULT 0,
                quality_score REAL DEFAULT 0,
                matched_keywords TEXT,
                
                contact_info TEXT,
                status TEXT DEFAULT 'pending',
                discovered_from TEXT,
                discovered_at TEXT DEFAULT (datetime('now', '+8 hours')),
                last_updated TEXT DEFAULT (datetime('now', '+8 hours')),
                notes TEXT
            )
        """)
        
        # Twitter推文表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS twitter_tweets (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                tweet_id TEXT UNIQUE NOT NULL,
                username TEXT,
                text TEXT,
                created_at TEXT,
                
                retweet_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                quote_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                
                is_retweet INTEGER DEFAULT 0,
                is_quote INTEGER DEFAULT 0,
                is_ai_related INTEGER DEFAULT 0,
                language TEXT,
                tweet_url TEXT,
                scraped_at TEXT DEFAULT (datetime('now', '+8 hours')),
                FOREIGN KEY (username) REFERENCES twitter_users(username)
            )
        """)
        
        # 创建索引
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_twitter_users_status ON twitter_users(status)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_twitter_users_quality ON twitter_users(quality_score)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_twitter_tweets_username ON twitter_tweets(username)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_twitter_tweets_ai ON twitter_tweets(is_ai_related)")
    
    def execute(self, query, params=None):
        """执行SQL查询"""
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        self.conn.commit()
    
    def fetchone(self, query, params=None):
        """查询单条记录"""
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                result = cursor.fetchone()
                cursor.close()
                
                if result:
                    return dict(result)
                return result
            except sqlite3.OperationalError as e:
                if attempt < max_retries - 1 and ('locked' in str(e).lower() or 'I/O' in str(e)):
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                    continue
                else:
                    raise
    
    def fetchall(self, query, params=None):
        """查询多条记录"""
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                results = cursor.fetchall()
                cursor.close()
                
                if results:
                    return [dict(row) for row in results]
                return results
            except sqlite3.OperationalError as e:
                if attempt < max_retries - 1 and ('locked' in str(e).lower() or 'I/O' in str(e)):
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                    continue
                else:
                    raise
