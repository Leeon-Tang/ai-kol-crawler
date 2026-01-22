"""
配置文件加载器 - 统一管理配置文件路径
"""
import os
import json


def get_project_root():
    """获取项目根目录的绝对路径"""
    # 从当前文件向上两级找到项目根目录
    current_file = os.path.abspath(__file__)
    utils_dir = os.path.dirname(current_file)
    project_root = os.path.dirname(utils_dir)
    return project_root


def get_absolute_path(relative_path):
    """将相对路径转换为绝对路径"""
    if os.path.isabs(relative_path):
        return relative_path
    project_root = get_project_root()
    return os.path.join(project_root, relative_path)


def get_config_path():
    """获取配置文件的绝对路径"""
    return get_absolute_path('config/config.json')


def load_config():
    """加载配置文件"""
    config_path = get_config_path()
    
    if not os.path.exists(config_path):
        # 尝试从示例文件创建
        example_path = get_absolute_path('config/config.example.json')
        if os.path.exists(example_path):
            import shutil
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            shutil.copy(example_path, config_path)
        else:
            raise FileNotFoundError(
                f"配置文件不存在: {config_path}\n"
                f"请确保 config/config.json 文件存在，或从 config/config.example.json 复制一份"
            )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config):
    """保存配置文件"""
    config_path = get_config_path()
    
    # 确保 config 目录存在
    config_dir = os.path.dirname(config_path)
    os.makedirs(config_dir, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
