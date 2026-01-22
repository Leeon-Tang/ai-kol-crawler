"""
日志系统 - 带颜色输出
"""
import logging
from datetime import datetime
import os
import sys


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # 格式化时间
        record.asctime = self.formatTime(record, self.datefmt)
        
        # 整行都使用相同颜色
        levelname = f"{self.BOLD}{record.levelname}{self.RESET}"
        log_message = f"{color}{record.asctime} - {levelname} - {record.getMessage()}{self.RESET}"
        
        return log_message


def setup_logger(name='ai_kol_crawler', log_dir='logs'):
    """设置日志器"""
    
    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 文件handler（无颜色）
    log_file = os.path.join(log_dir, f'{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 文件格式化器（无颜色）
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 控制台handler（带颜色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 控制台格式化器（带颜色）
    console_formatter = ColoredFormatter(datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(console_formatter)
    
    # 添加handler
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
