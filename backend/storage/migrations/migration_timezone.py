# -*- coding: utf-8 -*-
"""
时区迁移脚本 - 将UTC时间转换为北京时间（UTC+8）
"""
import sqlite3
import os
from datetime import datetime, timedelta, timezone


class TimezoneMigration:
    """时区迁移"""
    
    def __init__(self, db_path='data/ai_kol_crawler.db'):
        self.db_path = db_path
        self.beijing_offset = timedelta(hours=8)
    
    def needs_migration(self):
        """检查是否需要迁移"""
        if not os.path.exists(self.db_path):
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查是否有数据
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('youtube_kols', 'github_developers')")
            tables = cursor.fetchall()
            
            if not tables:
                return False
            
            # 检查最新一条记录的时间戳
            # 如果时间戳看起来像UTC（比当前北京时间小约8小时），则需要迁移
            beijing_now = datetime.now(timezone.utc) + self.beijing_offset
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT discovered_at FROM {table_name} ORDER BY discovered_at DESC LIMIT 1")
                row = cursor.fetchone()
                
                if row and row[0]:
                    try:
                        # 解析数据库时间（假设是UTC或北京时间）
                        db_time_naive = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                        # 假设数据库时间是naive的，我们需要判断它是UTC还是北京时间
                        # 如果是UTC，加8小时后应该接近当前北京时间
                        # 如果已经是北京时间，应该就是当前北京时间
                        
                        # 计算时间差（假设db_time是UTC）
                        time_diff_minutes = (beijing_now.replace(tzinfo=None) - db_time_naive).total_seconds() / 60
                        
                        # 如果时差在6-10小时之间（360-600分钟），说明是UTC时间，需要迁移
                        if 360 <= time_diff_minutes <= 600:
                            return True
                    except:
                        pass
            
            return False
            
        except Exception as e:
            print(f"检查迁移需求时出错: {e}")
            return False
        finally:
            conn.close()
    
    def migrate(self, silent=False):
        """执行迁移"""
        if not silent:
            print("=" * 60)
            print("开始时区迁移：UTC -> 北京时间（UTC+8）")
            print("=" * 60)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. 迁移 youtube_kols 表
            if not silent:
                print("\n[1/4] 迁移 youtube_kols 表...")
            self._migrate_table(cursor, 'youtube_kols', ['discovered_at', 'last_updated'], silent)
            
            # 2. 迁移 youtube_videos 表
            if not silent:
                print("\n[2/4] 迁移 youtube_videos 表...")
            self._migrate_table(cursor, 'youtube_videos', ['scraped_at'], silent)
            
            # 3. 迁移 github_developers 表
            if not silent:
                print("\n[3/4] 迁移 github_developers 表...")
            self._migrate_table(cursor, 'github_developers', ['discovered_at', 'last_updated'], silent)
            
            # 4. 迁移 github_repositories 表
            if not silent:
                print("\n[4/4] 迁移 github_repositories 表...")
            self._migrate_table(cursor, 'github_repositories', ['scraped_at'], silent)
            
            conn.commit()
            if not silent:
                print("\n" + "=" * 60)
                print("时区迁移完成！")
                print("=" * 60)
            return True
            
        except Exception as e:
            conn.rollback()
            if not silent:
                print(f"\n迁移失败: {e}")
            return False
        finally:
            conn.close()
    
    def _migrate_table(self, cursor, table_name, time_columns, silent=False):
        """迁移单个表的时间字段"""
        try:
            # 检查表是否存在
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if not cursor.fetchone():
                if not silent:
                    print(f"  表 {table_name} 不存在，跳过")
                return
            
            # 获取所有记录
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                if not silent:
                    print(f"  表 {table_name} 无数据，跳过")
                return
            
            # 获取列名
            column_names = [desc[0] for desc in cursor.description]
            
            # 找到时间列的索引
            time_column_indices = {}
            for col in time_columns:
                if col in column_names:
                    time_column_indices[col] = column_names.index(col)
            
            if not time_column_indices:
                if not silent:
                    print(f"  表 {table_name} 没有需要迁移的时间列，跳过")
                return
            
            # 找到主键列（通常是第一列的id）
            pk_column = column_names[0]
            pk_index = 0
            
            updated_count = 0
            
            # 更新每一行
            for row in rows:
                row_list = list(row)
                pk_value = row_list[pk_index]
                
                # 转换时间列
                updates = {}
                for col_name, col_index in time_column_indices.items():
                    time_str = row_list[col_index]
                    if time_str:
                        try:
                            # 解析UTC时间
                            utc_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                            # 转换为北京时间
                            beijing_time = utc_time + self.beijing_offset
                            updates[col_name] = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            # 如果解析失败，保持原值
                            pass
                
                # 执行更新
                if updates:
                    set_clause = ', '.join([f"{col} = ?" for col in updates.keys()])
                    values = list(updates.values()) + [pk_value]
                    cursor.execute(
                        f"UPDATE {table_name} SET {set_clause} WHERE {pk_column} = ?",
                        values
                    )
                    updated_count += 1
            
            if not silent:
                print(f"  ✓ 表 {table_name}: 更新了 {updated_count} 条记录")
            
        except Exception as e:
            if not silent:
                print(f"  ✗ 表 {table_name} 迁移失败: {e}")
            raise


def check_and_migrate_if_needed(silent=True):
    """检查并在需要时自动迁移"""
    import os
    
    # 确保从项目根目录运行
    if os.path.basename(os.getcwd()) == 'migrations':
        os.chdir('../..')
    elif os.path.basename(os.getcwd()) == 'storage':
        os.chdir('..')
    
    migration = TimezoneMigration()
    
    if migration.needs_migration():
        if not silent:
            print("\n检测到数据库需要时区迁移（UTC -> 北京时间）")
            print("正在自动迁移...")
        
        success = migration.migrate(silent=silent)
        
        if success and not silent:
            print("✓ 时区迁移完成")
        
        return success
    
    return False


if __name__ == '__main__':
    import os
    import sys
    
    # 确保从项目根目录运行
    if os.path.basename(os.getcwd()) == 'migrations':
        os.chdir('../..')
    elif os.path.basename(os.getcwd()) == 'storage':
        os.chdir('..')
    
    migration = TimezoneMigration()
    
    # 检查是否需要迁移
    if not migration.needs_migration():
        print("\n✓ 数据库时区已是北京时间，无需迁移")
        sys.exit(0)
    
    # 直接执行迁移，不需要用户确认
    print("\n检测到数据库需要时区迁移（UTC -> 北京时间）")
    print("正在自动迁移...\n")
    
    success = migration.migrate(silent=False)
    
    if success:
        print("\n✓ 时区迁移完成！")
    else:
        print("\n✗ 时区迁移失败")
        sys.exit(1)
