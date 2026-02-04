"""
数据库迁移和修复工具
- 查找所有数据库文件
- 选择最新的数据库
- 迁移到正确位置
- 检查表结构
- 修复问题
"""
import sys
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def find_all_databases():
    """查找所有数据库文件"""
    db_files = []
    
    # 搜索目录
    search_dirs = [
        os.path.join(PROJECT_ROOT, 'data'),
        os.path.join(PROJECT_ROOT, 'backend', 'data'),
        os.path.join(PROJECT_ROOT, 'backups'),
    ]
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.endswith('.db') and 'ai_kol_crawler' in file and 'backup' not in file:
                    filepath = os.path.join(root, file)
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    db_files.append({
                        'path': filepath,
                        'size': size,
                        'mtime': mtime,
                        'mtime_str': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
    
    return sorted(db_files, key=lambda x: x['mtime'], reverse=True)

def check_database_tables(db_path):
    """检查数据库表"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 统计每个表的记录数
        table_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_counts[table] = count
        
        conn.close()
        return tables, table_counts
    except Exception as e:
        return None, str(e)

def main():
    print("=" * 70)
    print("数据库迁移和修复工具")
    print("=" * 70)
    print()
    
    # 1. 查找所有数据库
    print("[步骤 1/5] 查找数据库文件...")
    db_files = find_all_databases()
    
    if not db_files:
        print("✗ 未找到任何数据库文件")
        return
    
    print(f"✓ 找到 {len(db_files)} 个数据库文件")
    print()
    
    # 显示数据库列表
    print("数据库文件列表:")
    print("-" * 70)
    for i, db in enumerate(db_files, 1):
        size_mb = db['size'] / (1024 * 1024)
        rel_path = os.path.relpath(db['path'], PROJECT_ROOT)
        print(f"{i}. {rel_path}")
        print(f"   大小: {size_mb:.2f} MB | 修改时间: {db['mtime_str']}")
    print("-" * 70)
    print()
    
    # 2. 选择最新的数据库
    print("[步骤 2/5] 选择数据库...")
    latest_db = db_files[0]
    print(f"✓ 自动选择最新的数据库:")
    print(f"  {os.path.relpath(latest_db['path'], PROJECT_ROOT)}")
    print()
    
    # 3. 检查表结构
    print("[步骤 3/5] 检查数据库表结构...")
    tables, table_counts = check_database_tables(latest_db['path'])
    
    if tables is None:
        print(f"✗ 数据库检查失败: {table_counts}")
        return
    
    print(f"✓ 数据库包含 {len(tables)} 个表:")
    print()
    
    # 按平台分组显示
    youtube_tables = [t for t in tables if 'youtube' in t or t in ['kols', 'videos', 'expansion_queue']]
    github_tables = [t for t in tables if 'github' in t]
    twitter_tables = [t for t in tables if 'twitter' in t]
    
    if youtube_tables:
        print("  YouTube 平台:")
        for table in youtube_tables:
            count = table_counts.get(table, 0)
            print(f"    - {table:30s} {count:6d} 条记录")
    
    if github_tables:
        print()
        print("  GitHub 平台:")
        for table in github_tables:
            count = table_counts.get(table, 0)
            print(f"    - {table:30s} {count:6d} 条记录")
    
    if twitter_tables:
        print()
        print("  Twitter 平台:")
        for table in twitter_tables:
            count = table_counts.get(table, 0)
            print(f"    - {table:30s} {count:6d} 条记录")
    
    print()
    
    # 4. 迁移到正确位置
    target_dir = os.path.join(PROJECT_ROOT, 'data')
    target_path = os.path.join(target_dir, 'ai_kol_crawler.db')
    
    print("[步骤 4/5] 迁移数据库到正确位置...")
    
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 如果源文件就是目标文件
    if os.path.abspath(latest_db['path']) == os.path.abspath(target_path):
        print("✓ 数据库已在正确位置，无需迁移")
    else:
        # 备份现有文件
        if os.path.exists(target_path):
            backup_path = target_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            shutil.copy2(target_path, backup_path)
            print(f"  已备份现有数据库到: {os.path.basename(backup_path)}")
        
        # 复制文件
        shutil.copy2(latest_db['path'], target_path)
        print(f"✓ 数据库已迁移到: data/ai_kol_crawler.db")
    
    print()
    
    # 5. 运行数据库迁移脚本
    print("[步骤 5/5] 执行数据库结构迁移...")
    try:
        from backend.storage.migrations.migration_v2 import migrate
        migrate()
        print("✓ 数据库结构检查完成")
    except Exception as e:
        print(f"⚠ 迁移检查警告: {e}")
    
    print()
    print("=" * 70)
    print("✓ 数据库迁移和修复完成！")
    print("=" * 70)
    print()
    print(f"数据库位置: data/ai_kol_crawler.db")
    print(f"数据库大小: {os.path.getsize(target_path) / (1024*1024):.2f} MB")
    print()
    
    # 清理建议
    if len(db_files) > 1:
        print("清理建议:")
        print("  以下旧数据库文件可以删除:")
        for db in db_files[1:]:
            if 'backend/data' in db['path']:
                rel_path = os.path.relpath(db['path'], PROJECT_ROOT)
                print(f"    - {rel_path}")
        print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
