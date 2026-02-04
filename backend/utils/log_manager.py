# -*- coding: utf-8 -*-
"""
日志管理工具
"""
import os
import queue
from datetime import datetime, timedelta, timezone

# 全局日志队列
log_queue = queue.Queue()
log_list = []


def add_log(message, level="INFO"):
    """添加日志"""
    # 使用北京时间
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
    timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    log_queue.put(log_entry)
    log_list.append(log_entry)
    if len(log_list) > 1000:
        log_list.pop(0)
    
    # 写入文件
    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/{beijing_time.strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except:
        pass


def clear_logs(log_dir="logs"):
    """清空日志"""
    global log_list
    log_list.clear()
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
    log_file = os.path.join(log_dir, f"{beijing_time.strftime('%Y%m%d')}.log")
    if os.path.exists(log_file):
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("")
            return True
        except:
            return False
    return True


def get_log_list():
    """获取日志列表"""
    return log_list


def get_recent_logs(log_dir="logs", lines=100):
    """获取最近的日志"""
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
    log_file = os.path.join(log_dir, f"{beijing_time.strftime('%Y%m%d')}.log")
    
    if not os.path.exists(log_file):
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:]]
    except:
        return []
