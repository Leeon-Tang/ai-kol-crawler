# -*- coding: utf-8 -*-
"""
运行所有测试的主文件
"""
import sys
import os
import pytest

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行测试套件")
    print("=" * 60)
    
    # 配置pytest参数
    args = [
        "-v",  # 详细输出
        "-s",  # 显示print输出
        "--tb=short",  # 简短的traceback
        "--color=yes",  # 彩色输出
        os.path.dirname(__file__)  # 测试目录
    ]
    
    # 运行测试
    exit_code = pytest.main(args)
    
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("所有测试通过!")
    else:
        print("部分测试失败")
    print("=" * 60)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
