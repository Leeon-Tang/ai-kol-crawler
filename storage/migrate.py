"""
数据库迁移模块 - 自动检测并执行必要的迁移
"""
import sqlite3
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger
from utils.config_loader import get_project_root

logger = setup_logger()


class DatabaseMigration:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.project_root = get_project_root()
        self.db_path = os.path.join(self.project_root, 'data', 'ai_kol_crawler.db')
    
    def check_and_migrate(self):
        """检查并执行必要的迁移"""
        if not os.path.exists(self.db_path):
            logger.info("数据库文件不存在，无需迁移")
            return True
        
        logger.info("检查数据库是否需要迁移...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取当前表结构
            cursor.execute("PRAGMA table_info(kols)")
            columns = [col[1] for col in cursor.fetchall()]
            
            migrations_needed = []
            
            # 检查需要的字段
            if 'avg_comments' not in columns:
                migrations_needed.append('avg_comments')
            
            if 'contact_info' not in columns:
                migrations_needed.append('contact_info')
            
            if not migrations_needed:
                logger.info("✓ 数据库结构已是最新，无需迁移")
                return True
            
            # 执行迁移
            logger.info(f"需要迁移的字段: {', '.join(migrations_needed)}")
            
            for field in migrations_needed:
                if field == 'avg_comments':
                    logger.info("  添加字段: avg_comments")
                    cursor.execute("ALTER TABLE kols ADD COLUMN avg_comments INTEGER DEFAULT 0")
                    logger.info("  ✓ avg_comments 字段添加成功")
                
                elif field == 'contact_info':
                    logger.info("  添加字段: contact_info")
                    cursor.execute("ALTER TABLE kols ADD COLUMN contact_info TEXT")
                    logger.info("  ✓ contact_info 字段添加成功")
            
            conn.commit()
            logger.info("✓ 数据库迁移完成！")
            return True
            
        except Exception as e:
            logger.error(f"✗ 迁移失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()


def run_migration():
    """运行迁移（供外部调用）"""
    migration = DatabaseMigration()
    return migration.check_and_migrate()


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
