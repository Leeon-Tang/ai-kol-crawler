# -*- coding: utf-8 -*-
"""
数据库修复工具
用于诊断和修复SQLite数据库的I/O错误
"""
import sqlite3
import os
import shutil
from datetime import datetime

def check_database(db_path):
    """检查数据库状态"""
    print(f"检查数据库: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    # 检查文件大小
    size = os.path.getsize(db_path) / 1024 / 1024
    print(f"✓ 数据库大小: {size:.2f} MB")
    
    # 检查文件权限
    if os.access(db_path, os.R_OK):
        print("✓ 文件可读")
    else:
        print("❌ 文件不可读")
        return False
    
    if os.access(db_path, os.W_OK):
        print("✓ 文件可写")
    else:
        print("❌ 文件不可写")
        return False
    
    return True

def test_connection(db_path):
    """测试数据库连接"""
    print("\n测试数据库连接...")
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # 测试简单查询
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✓ 找到 {len(tables)} 个表")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def check_integrity(db_path):
    """检查数据库完整性"""
    print("\n检查数据库完整性...")
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == 'ok':
            print("✓ 数据库完整性检查通过")
            cursor.close()
            conn.close()
            return True
        else:
            print(f"❌ 数据库损坏: {result[0]}")
            cursor.close()
            conn.close()
            return False
    except Exception as e:
        print(f"❌ 完整性检查失败: {e}")
        return False

def repair_database(db_path):
    """修复数据库"""
    print("\n开始修复数据库...")
    
    # 创建备份
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✓ 已创建备份: {backup_path}")
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False
    
    try:
        # 尝试修复
        conn = sqlite3.connect(db_path, timeout=30.0)
        
        # 启用WAL模式
        conn.execute("PRAGMA journal_mode=WAL")
        print("✓ 已启用WAL模式")
        
        # 执行VACUUM清理
        conn.execute("VACUUM")
        print("✓ 已执行VACUUM清理")
        
        # 重新检查完整性
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result[0] == 'ok':
            print("✓ 数据库修复成功")
            return True
        else:
            print(f"❌ 修复后仍有问题: {result[0]}")
            return False
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def export_and_recreate(db_path):
    """导出数据并重建数据库"""
    print("\n尝试导出数据并重建数据库...")
    
    temp_path = f"{db_path}.temp"
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # 备份原数据库
        shutil.copy2(db_path, backup_path)
        print(f"✓ 已创建备份: {backup_path}")
        
        # 连接到原数据库
        old_conn = sqlite3.connect(db_path, timeout=30.0)
        
        # 创建新数据库
        new_conn = sqlite3.connect(temp_path)
        
        # 复制数据
        for line in old_conn.iterdump():
            if line not in ('BEGIN;', 'COMMIT;'):
                new_conn.execute(line)
        
        new_conn.commit()
        new_conn.close()
        old_conn.close()
        
        # 替换原数据库
        os.remove(db_path)
        shutil.move(temp_path, db_path)
        
        print("✓ 数据库重建成功")
        return True
        
    except Exception as e:
        print(f"❌ 重建失败: {e}")
        # 恢复备份
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, db_path)
                print("✓ 已恢复备份")
            except:
                pass
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("SQLite 数据库修复工具")
    print("=" * 60)
    
    # 数据库路径
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ai_kol_crawler.db')
    
    # 1. 检查数据库
    if not check_database(db_path):
        print("\n数据库文件检查失败，无法继续")
        return
    
    # 2. 测试连接
    if not test_connection(db_path):
        print("\n数据库连接失败")
        print("建议：检查是否有其他程序正在使用数据库")
        return
    
    # 3. 检查完整性
    if check_integrity(db_path):
        print("\n数据库状态良好，无需修复")
        return
    
    # 4. 尝试修复
    print("\n检测到数据库问题，开始修复...")
    if repair_database(db_path):
        print("\n✓ 修复完成")
        return
    
    # 5. 如果修复失败，尝试重建
    print("\n常规修复失败，尝试重建数据库...")
    if export_and_recreate(db_path):
        print("\n✓ 重建完成")
    else:
        print("\n❌ 所有修复尝试均失败")
        print(f"请手动检查数据库文件: {db_path}")
        print(f"备份文件位于同一目录下")

if __name__ == "__main__":
    main()
