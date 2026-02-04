"""
日志系统 - 带颜色输出（自动检测终端支持）
"""
import logging
from datetime import datetime
import os
import sys
import platform


# 检测是否支持ANSI颜色
def supports_color():
    """检测终端是否支持ANSI颜色"""
    # Windows 10以下的CMD不支持ANSI
    if platform.system() == 'Windows':
        # 检查是否在Windows Terminal或支持ANSI的终端中
        if os.environ.get('WT_SESSION') or os.environ.get('TERM_PROGRAM'):
            return True
        # Windows 10 1511以上支持ANSI，但CMD默认不启用
        return False
    # Linux/Mac通常支持
    return True


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器（自动检测终端支持）"""
    
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
    
    def __init__(self, *args, use_colors=None, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果未指定，自动检测
        if use_colors is None:
            self.use_colors = supports_color()
        else:
            self.use_colors = use_colors
    
    def format(self, record):
        # 格式化时间
        record.asctime = self.formatTime(record, self.datefmt)
        
        if self.use_colors:
            # 获取颜色
            color = self.COLORS.get(record.levelname, self.RESET)
            # 整行都使用相同颜色
            levelname = f"{self.BOLD}{record.levelname}{self.RESET}"
            log_message = f"{color}{record.asctime} - {levelname} - {record.getMessage()}{self.RESET}"
        else:
            # 无颜色版本
            log_message = f"{record.asctime} - {record.levelname} - {record.getMessage()}"
        
        return log_message


def setup_logger(name='ai_kol_crawler', log_dir='logs', use_colors=None):
    """
    设置日志器
    
    Args:
        name: 日志器名称
        log_dir: 日志目录
        use_colors: 是否使用颜色（None=自动检测，True=强制启用，False=强制禁用）
    """
    
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
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 控制台格式化器（自动检测颜色支持）
    console_formatter = ColoredFormatter(
        datefmt='%Y-%m-%d %H:%M:%S',
        use_colors=use_colors
    )
    console_handler.setFormatter(console_formatter)
    
    # 添加handler
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
