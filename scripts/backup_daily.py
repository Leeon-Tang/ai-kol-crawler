"""
每日备份脚本 - 备份当天的数据和日志
运行位置：从项目根目录运行
"""
import sqlite3
import shutil
import os
import sys
from datetime import datetime, timedelta, timezone

# 确保从项目根目录运行
if os.path.basename(os.getcwd()) == 'scripts':
    os.chdir('..')

# 配置
MAIN_DB = 'data/ai_kol_crawler.db'
BACKUP_DIR = 'backups'
LOG_DIR = 'logs'

# 北京时间偏移（UTC+8）
BEIJING_OFFSET_HOURS = 8

def backup_daily():
    """执行每日备份"""
    # 使用北京时间
    beijing_now = datetime.now(timezone.utc) + timedelta(hours=BEIJING_OFFSET_HOURS)
    today = beijing_now.strftime('%Y%m%d')
    yesterday = (beijing_now - timedelta(days=1)).strftime('%Y%m%d')
    
    # 创建备份目录
    os.makedirs(BACKUP_DIR, exist_ok=True)
    daily_backup_dir = os.path.join(BACKUP_DIR, today)
    os.makedirs(daily_backup_dir, exist_ok=True)
    
    print(f"=" * 60)
    print(f"开始每日备份 - {today} (北京时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"=" * 60)
    
    # 1. 备份当天的数据（从主数据库提取）
    print("\n[1/3] 备份当天数据...")
    backup_today_data(daily_backup_dir, today, beijing_now)
    
    # 2. 备份日志文件
    print("\n[2/3] 备份日志文件...")
    backup_logs(daily_backup_dir, today, yesterday)
    
    # 3. 备份完整数据库（可选）
    print("\n[3/3] 备份完整数据库...")
    backup_full_db(daily_backup_dir)
    
    print(f"\n{'=' * 60}")
    print(f"备份完成！位置: {daily_backup_dir}")
    print(f"{'=' * 60}\n")


def backup_today_data(backup_dir, today, beijing_now):
    """提取并备份当天的数据（北京时间）"""
    if not os.path.exists(MAIN_DB):
        print("  主数据库不存在，跳过")
        return
    
    # 连接主数据库
    main_conn = sqlite3.connect(MAIN_DB)
    main_cursor = main_conn.cursor()
    
    # 创建当天的数据库（如果存在则删除重建）
    daily_db_path = os.path.join(backup_dir, f'daily_data_{today}.db')
    if os.path.exists(daily_db_path):
        os.remove(daily_db_path)
    
    daily_conn = sqlite3.connect(daily_db_path)
    daily_cursor = daily_conn.cursor()
    
    # 创建表结构（复制主数据库的表结构）
    tables = main_cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    
    for table_sql in tables:
        if table_sql[0]:
            daily_cursor.execute(table_sql[0])
    
    # 计算当天的UTC时间范围（数据库存储的是UTC时间）
    # 北京时间 00:00:00 对应 UTC 前一天 16:00:00
    # 北京时间 23:59:59 对应 UTC 当天 15:59:59
    utc_start = beijing_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=BEIJING_OFFSET_HOURS)
    utc_end = beijing_now.replace(hour=23, minute=59, second=59, microsecond=0) - timedelta(hours=BEIJING_OFFSET_HOURS)
    
    today_start_utc = utc_start.strftime('%Y-%m-%d %H:%M:%S')
    today_end_utc = utc_end.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"  备份时间范围（UTC）: {today_start_utc} ~ {today_end_utc}")
    print(f"  对应北京时间: {today[:4]}-{today[4:6]}-{today[6:8]} 00:00:00 ~ 23:59:59")
    
    total_records = 0
    
    # 1. 备份YouTube KOL数据
    try:
        youtube_kols = main_cursor.execute(
            "SELECT * FROM youtube_kols WHERE discovered_at >= ? AND discovered_at <= ?",
            (today_start_utc, today_end_utc)
        ).fetchall()
        
        if youtube_kols:
            columns = [desc[0] for desc in main_cursor.description]
            placeholders = ','.join(['?' for _ in columns])
            daily_cursor.executemany(
                f"INSERT INTO youtube_kols VALUES ({placeholders})",
                youtube_kols
            )
            
            # 提取这些KOL的视频数据
            channel_ids = [kol[1] for kol in youtube_kols]  # channel_id
            if channel_ids:
                placeholders_ids = ','.join(['?' for _ in channel_ids])
                videos = main_cursor.execute(
                    f"SELECT * FROM youtube_videos WHERE channel_id IN ({placeholders_ids})",
                    channel_ids
                ).fetchall()
                
                if videos:
                    video_columns = [desc[0] for desc in main_cursor.description]
                    video_placeholders = ','.join(['?' for _ in video_columns])
                    daily_cursor.executemany(
                        f"INSERT INTO youtube_videos VALUES ({video_placeholders})",
                        videos
                    )
            
            print(f"  ✓ YouTube: {len(youtube_kols)} 个KOL，{len(videos) if 'videos' in locals() and videos else 0} 个视频")
            total_records += len(youtube_kols)
    except Exception as e:
        print(f"  ! YouTube数据备份失败: {e}")
    
    # 2. 备份GitHub开发者数据
    try:
        github_devs = main_cursor.execute(
            "SELECT * FROM github_developers WHERE discovered_at >= ? AND discovered_at <= ?",
            (today_start_utc, today_end_utc)
        ).fetchall()
        
        if github_devs:
            columns = [desc[0] for desc in main_cursor.description]
            placeholders = ','.join(['?' for _ in columns])
            daily_cursor.executemany(
                f"INSERT INTO github_developers VALUES ({placeholders})",
                github_devs
            )
            
            # 提取这些开发者的仓库数据
            usernames = [dev[2] for dev in github_devs]  # username
            if usernames:
                placeholders_ids = ','.join(['?' for _ in usernames])
                repos = main_cursor.execute(
                    f"SELECT * FROM github_repositories WHERE username IN ({placeholders_ids})",
                    usernames
                ).fetchall()
                
                if repos:
                    repo_columns = [desc[0] for desc in main_cursor.description]
                    repo_placeholders = ','.join(['?' for _ in repo_columns])
                    daily_cursor.executemany(
                        f"INSERT INTO github_repositories VALUES ({repo_placeholders})",
                        repos
                    )
            
            print(f"  ✓ GitHub: {len(github_devs)} 个开发者，{len(repos) if 'repos' in locals() and repos else 0} 个仓库")
            total_records += len(github_devs)
    except Exception as e:
        print(f"  ! GitHub数据备份失败: {e}")
    
    if total_records == 0:
        print(f"  ! 今天没有新数据")
    
    daily_conn.commit()
    daily_conn.close()
    main_conn.close()


def backup_logs(backup_dir, today, yesterday):
    """备份日志文件"""
    if not os.path.exists(LOG_DIR):
        print("  日志目录不存在，跳过")
        return
    
    # 备份今天和昨天的日志
    log_files = [
        f"{today[:4]}{today[4:6]}{today[6:8]}.log",
        f"{yesterday[:4]}{yesterday[4:6]}{yesterday[6:8]}.log"
    ]
    
    copied = 0
    for log_file in log_files:
        src = os.path.join(LOG_DIR, log_file)
        if os.path.exists(src):
            dst = os.path.join(backup_dir, log_file)
            shutil.copy2(src, dst)
            copied += 1
            print(f"  ✓ 备份日志: {log_file}")
    
    if copied == 0:
        print("  ! 没有找到日志文件")


def backup_full_db(backup_dir):
    """备份完整数据库（可选）"""
    if not os.path.exists(MAIN_DB):
        print("  主数据库不存在，跳过")
        return
    
    dst = os.path.join(backup_dir, 'full_database_backup.db')
    shutil.copy2(MAIN_DB, dst)
    
    size_mb = os.path.getsize(dst) / (1024 * 1024)
    print(f"  ✓ 完整数据库备份完成 ({size_mb:.2f} MB)")


def cleanup_old_backups(days=7):
    """清理旧备份（保留最近N天）"""
    if not os.path.exists(BACKUP_DIR):
        return
    
    # 使用北京时间计算截止日期
    beijing_now = datetime.now(timezone.utc) + timedelta(hours=BEIJING_OFFSET_HOURS)
    cutoff_date = beijing_now - timedelta(days=days)
    
    cleaned = 0
    for folder in os.listdir(BACKUP_DIR):
        folder_path = os.path.join(BACKUP_DIR, folder)
        if os.path.isdir(folder_path) and len(folder) == 8 and folder.isdigit():
            try:
                folder_date = datetime.strptime(folder, '%Y%m%d')
                if folder_date < cutoff_date:
                    shutil.rmtree(folder_path)
                    print(f"  清理旧备份: {folder}")
                    cleaned += 1
            except:
                pass
    
    if cleaned == 0:
        print(f"  没有需要清理的旧备份（保留 {days} 天内的数据）")


if __name__ == '__main__':
    backup_daily()
    
    # 可选：清理7天前的备份
    print("\n检查旧备份...")
    cleanup_old_backups(days=7)
    print("完成！")
