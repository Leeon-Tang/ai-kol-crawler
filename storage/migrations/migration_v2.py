# -*- coding: utf-8 -*-
"""
数据迁移 v1 -> v2
从单平台(kols表)迁移到多平台(youtube_kols表)
"""
import sqlite3
import os
from utils.config_loader import get_project_root


class MigrationV2:
    """数据迁移 v1 到 v2"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            project_root = get_project_root()
            db_path = os.path.join(project_root, 'data', 'ai_kol_crawler.db')
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def check_old_tables_exist(self):
        """检查旧表是否存在"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kols'")
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    
    def check_new_tables_exist(self):
        """检查新表是否存在"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='youtube_kols'")
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    
    def check_and_add_fields(self):
        """检查并添加缺失的字段"""
        cursor = self.conn.cursor()
        
        # 定义需要检查的表和字段
        tables_fields = {
            'youtube_kols': ['avg_comments', 'contact_info'],
            'kols': ['avg_comments', 'contact_info']  # 兼容旧表
        }
        
        for table_name, required_fields in tables_fields.items():
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                continue
            
            # 获取当前表的字段
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            # 检查并添加缺失的字段
            for field in required_fields:
                if field not in existing_columns:
                    print(f"   添加字段 {table_name}.{field}")
                    try:
                        if field == 'avg_comments':
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN avg_comments INTEGER DEFAULT 0")
                        elif field == 'contact_info':
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN contact_info TEXT")
                        print(f"   ✓ {field} 字段添加成功")
                    except Exception as e:
                        print(f"   ✗ 添加字段失败: {e}")
        
        self.conn.commit()
        cursor.close()
    
    def migrate(self):
        """执行迁移"""
        self.connect()
        
        try:
            # 步骤1: 检查并添加缺失的字段
            print("步骤 1: 检查并添加缺失的字段")
            self.check_and_add_fields()
            
            # 步骤2: 检查是否需要数据迁移
            if not self.check_old_tables_exist():
                print("\n✓ 未发现旧表，无需数据迁移")
                print("✓ 字段检查完成")
                return True
            
            if not self.check_new_tables_exist():
                print("\n✗ 新表不存在，请先初始化数据库")
                return False
            
            print("\n步骤 2: 开始数据迁移...")
            
            # 迁移 kols -> youtube_kols
            print("   2.1 迁移 kols -> youtube_kols")
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO youtube_kols 
                SELECT * FROM kols
            """)
            migrated_kols = cursor.rowcount
            print(f"       迁移了 {migrated_kols} 条KOL记录")
            
            # 迁移 videos -> youtube_videos
            print("   2.2 迁移 videos -> youtube_videos")
            cursor.execute("""
                INSERT OR IGNORE INTO youtube_videos 
                SELECT * FROM videos
            """)
            migrated_videos = cursor.rowcount
            print(f"       迁移了 {migrated_videos} 条视频记录")
            
            # 迁移 expansion_queue -> youtube_expansion_queue
            print("   2.3 迁移 expansion_queue -> youtube_expansion_queue")
            cursor.execute("""
                INSERT OR IGNORE INTO youtube_expansion_queue 
                SELECT * FROM expansion_queue
            """)
            migrated_queue = cursor.rowcount
            print(f"       迁移了 {migrated_queue} 条队列记录")
            
            self.conn.commit()
            cursor.close()
            
            print("\n✓ 数据迁移完成！")
            print(f"  - KOL: {migrated_kols}")
            print(f"  - 视频: {migrated_videos}")
            print(f"  - 队列: {migrated_queue}")
            
            # 询问是否删除旧表
            print("\n旧表已保留，如需删除请手动执行：")
            print("  DROP TABLE kols;")
            print("  DROP TABLE videos;")
            print("  DROP TABLE expansion_queue;")
            
            return True
            
        except Exception as e:
            print(f"✗ 迁移失败: {e}")
            self.conn.rollback()
            return False
        
        finally:
            self.close()
    
    def backup_before_migrate(self):
        """迁移前备份"""
        import shutil
        from datetime import datetime
        
        backup_name = self.db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy(self.db_path, backup_name)
        print(f"✓ 已备份数据库到: {backup_name}")
        return backup_name


def migrate():
    """快速迁移（供启动脚本调用）"""
    migration = MigrationV2()
    try:
        return migration.migrate()
    except Exception as e:
        print(f"迁移检查失败: {e}")
        return True  # 返回True让系统继续运行


def run_migration():
    """完整迁移（带备份）"""
    print("=" * 60)
    print("数据迁移工具 v1 -> v2")
    print("=" * 60)
    
    migration = MigrationV2()
    
    # 备份
    print("\n准备: 备份数据库")
    try:
        backup_path = migration.backup_before_migrate()
    except Exception as e:
        print(f"✗ 备份失败: {e}")
        return False
    
    # 迁移
    print("\n执行迁移:")
    success = migration.migrate()
    
    if success:
        print("\n" + "=" * 60)
        print("迁移成功！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("迁移失败，请检查错误信息")
        print(f"可以从备份恢复: {backup_path}")
        print("=" * 60)
    
    return success


if __name__ == "__main__":
    run_migration()
