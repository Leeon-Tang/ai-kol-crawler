# -*- coding: utf-8 -*-
"""
数据迁移 v1 -> v2
从单平台(kols表)迁移到多平台(youtube_kols表)
"""
import sqlite3
import os
from backend.utils.config_loader import get_project_root
from backend.utils.logger import setup_logger

logger = setup_logger()


class MigrationV2:
    """数据迁移 v1 到 v2"""
    
    def __init__(self, db_path=None, silent=True):
        if db_path is None:
            project_root = get_project_root()
            db_path = os.path.join(project_root, 'data', 'ai_kol_crawler.db')
        self.db_path = db_path
        self.conn = None
        self.silent = silent  # 静默模式，不输出日志
        self.migration_flag_file = db_path.replace('.db', '_migrated.flag')
    
    def _log(self, message, level='info'):
        """统一的日志输出"""
        if not self.silent:
            if level == 'info':
                logger.info(message)
            elif level == 'warning':
                logger.warning(message)
            elif level == 'error':
                logger.error(message)
            print(message)  # 只在非静默模式下print
    
    def is_migration_completed(self):
        """检查迁移是否已完成（通过标记文件）"""
        return os.path.exists(self.migration_flag_file)
    
    def mark_migration_completed(self):
        """标记迁移已完成"""
        try:
            with open(self.migration_flag_file, 'w') as f:
                from datetime import datetime
                f.write(f"Migration completed at {datetime.now().isoformat()}\n")
        except Exception as e:
            logger.warning(f"无法创建迁移标记文件: {e}")
    
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
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kols'")
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    
    def check_new_tables_exist(self):
        """检查新表是否存在"""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='youtube_kols'")
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    
    def check_and_add_fields(self):
        """检查并添加缺失的字段"""
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor()
        
        # 定义需要检查的表和字段
        tables_fields = {
            'youtube_kols': ['avg_comments', 'contact_info'],
            'kols': ['avg_comments', 'contact_info']  # 兼容旧表
        }
        
        fields_added = False
        
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
                    fields_added = True
                    self._log(f"   添加字段 {table_name}.{field}")
                    try:
                        if field == 'avg_comments':
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN avg_comments INTEGER DEFAULT 0")
                        elif field == 'contact_info':
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN contact_info TEXT")
                        self._log(f"   ✓ {field} 字段添加成功")
                    except Exception as e:
                        self._log(f"   ✗ 添加字段失败: {e}", 'error')
        
        self.conn.commit()
        cursor.close()
        
        return fields_added
    
    def migrate(self):
        """执行迁移"""
        if not self.conn:
            self.connect()
        
        try:
            # 如果已经迁移过，直接返回（静默）
            if self.is_migration_completed():
                return True
            
            # 步骤1: 检查并添加缺失的字段
            self._log("步骤 1: 检查并添加缺失的字段")
            fields_added = self.check_and_add_fields()
            
            if fields_added:
                self._log("✓ 字段检查完成，已添加缺失字段")
            
            # 步骤2: 检查是否需要数据迁移
            if not self.check_old_tables_exist():
                self._log("[OK] 未发现旧表，无需数据迁移")
                self.mark_migration_completed()
                return True
            
            if not self.check_new_tables_exist():
                self._log("[错误] 新表不存在，请先初始化数据库", 'error')
                return False
            
            # 检查旧表是否有数据
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM kols")
            old_kol_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM youtube_kols")
            new_kol_count = cursor.fetchone()[0]
            
            # 如果旧表有数据且新表为空，才执行迁移
            if old_kol_count == 0:
                self._log("[OK] 旧表无数据，无需迁移")
                cursor.close()
                self.mark_migration_completed()
                return True
            
            if new_kol_count > 0:
                self._log("[OK] 数据已迁移，跳过")
                cursor.close()
                self.mark_migration_completed()
                return True
            
            # 只有真正需要迁移时才输出详细日志
            self._log("\n步骤 2: 开始数据迁移...")
            
            # 迁移 kols -> youtube_kols
            self._log("   2.1 迁移 kols -> youtube_kols")
            cursor.execute("""
                INSERT OR IGNORE INTO youtube_kols 
                SELECT * FROM kols
            """)
            migrated_kols = cursor.rowcount
            self._log(f"       迁移了 {migrated_kols} 条KOL记录")
            
            # 迁移 videos -> youtube_videos
            self._log("   2.2 迁移 videos -> youtube_videos")
            cursor.execute("""
                INSERT OR IGNORE INTO youtube_videos 
                SELECT * FROM videos
            """)
            migrated_videos = cursor.rowcount
            self._log(f"       迁移了 {migrated_videos} 条视频记录")
            
            # 迁移 expansion_queue -> youtube_expansion_queue
            self._log("   2.3 迁移 expansion_queue -> youtube_expansion_queue")
            cursor.execute("""
                INSERT OR IGNORE INTO youtube_expansion_queue 
                SELECT * FROM expansion_queue
            """)
            migrated_queue = cursor.rowcount
            self._log(f"       迁移了 {migrated_queue} 条队列记录")
            
            self.conn.commit()
            cursor.close()
            
            self._log("\n[OK] 数据迁移完成！")
            self._log(f"  - KOL: {migrated_kols}")
            self._log(f"  - 视频: {migrated_videos}")
            self._log(f"  - 队列: {migrated_queue}")
            
            # 询问是否删除旧表
            self._log("\n旧表已保留，如需删除请手动执行：")
            self._log("  DROP TABLE kols;")
            self._log("  DROP TABLE videos;")
            self._log("  DROP TABLE expansion_queue;")
            
            # 标记迁移完成
            self.mark_migration_completed()
            
            return True
            
        except Exception as e:
            self._log(f"[错误] 迁移失败: {e}", 'error')
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
    """快速迁移（供启动脚本调用）- 静默模式"""
    migration = MigrationV2(silent=True)  # 默认静默
    try:
        return migration.migrate()
    except Exception as e:
        logger.error(f"迁移检查失败: {e}")
        return True  # 返回True让系统继续运行


def run_migration():
    """完整迁移（带备份）- 详细日志模式"""
    print("=" * 60)
    print("数据迁移工具 v1 -> v2")
    print("=" * 60)
    
    migration = MigrationV2(silent=False)  # 详细模式
    
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
