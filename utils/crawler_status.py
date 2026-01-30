# -*- coding: utf-8 -*-
"""
爬虫状态管理工具
"""
import os
import threading


# 全局停止标志
_stop_flag = threading.Event()


def request_stop():
    """请求停止爬虫"""
    _stop_flag.set()


def clear_stop_flag():
    """清除停止标志"""
    _stop_flag.clear()


def should_stop():
    """检查是否应该停止"""
    return _stop_flag.is_set()


def set_crawler_running(status, status_file, add_log_func):
    """设置爬虫运行状态"""
    try:
        status_dir = os.path.dirname(status_file)
        os.makedirs(status_dir, exist_ok=True)
        
        # 写入状态
        status_text = "running" if status else "stopped"
        with open(status_file, 'w', encoding='utf-8') as f:
            f.write(status_text)
        
        # 如果是启动爬虫，清除停止标志
        if status:
            clear_stop_flag()
        
        # 强制刷新到磁盘
        if hasattr(os, 'sync'):
            os.sync()
        
        # 验证写入
        with open(status_file, 'r', encoding='utf-8') as f:
            written_status = f.read().strip()
            if written_status != status_text:
                raise Exception(f"状态写入验证失败: 期望 {status_text}, 实际 {written_status}")
        
        add_log_func(f"爬虫状态已更新: {status_text}", "INFO")
        return True
    except Exception as e:
        add_log_func(f"设置爬虫状态失败: {str(e)}", "ERROR")
        return False


def is_crawler_running(status_file):
    """获取爬虫运行状态"""
    try:
        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as f:
                status = f.read().strip()
                return status == "running"
    except:
        pass
    return False


def check_and_fix_crawler_status(status_file, add_log_func):
    """检查并修复爬虫状态（如果线程已结束但状态还是运行中）"""
    try:
        if not is_crawler_running(status_file):
            return True
        
        # 检查是否有活跃的爬虫线程
        active_threads = threading.enumerate()
        crawler_thread_exists = any(
            'run_youtube_crawler_task' in str(t.name) or 
            'run_github_crawler_task' in str(t.name) or
            t.name.startswith('Thread-') and t.is_alive()
            for t in active_threads
        )
        
        # 如果状态是运行中，但没有活跃的爬虫线程，自动修复
        if not crawler_thread_exists:
            add_log_func("检测到爬虫状态异常（无活跃线程但状态为运行中），自动修复", "WARNING")
            set_crawler_running(False, status_file, add_log_func)
            return True
        
        return False
    except Exception as e:
        add_log_func(f"检查爬虫状态时出错: {str(e)}", "ERROR")
        return False
