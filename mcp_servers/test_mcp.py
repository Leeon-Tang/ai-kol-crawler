#!/usr/bin/env python3
"""
测试 MCP Server 是否正常工作
"""
import asyncio
import sys
import os

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from mcp_servers.browser_manager import BrowserManager


async def test_browser_manager():
    """测试浏览器管理器"""
    print("=" * 60)
    print("测试浏览器管理器")
    print("=" * 60)
    
    manager = BrowserManager(PROJECT_ROOT)
    
    try:
        # 1. 启动 Streamlit
        print("\n[1/5] 启动 Streamlit...")
        success = await manager.start_streamlit()
        if success:
            print("✓ Streamlit 启动成功")
        else:
            print("✗ Streamlit 启动失败")
            return False
        
        # 2. 启动浏览器
        print("\n[2/5] 启动浏览器...")
        success = await manager.start_browser()
        if success:
            print("✓ 浏览器启动成功")
        else:
            print("✗ 浏览器启动失败")
            return False
        
        # 3. 截图
        print("\n[3/5] 测试截图...")
        filepath = await manager.screenshot("test_screenshot.png")
        print(f"✓ 截图保存到: {filepath}")
        
        # 4. 获取日志
        print("\n[4/5] 测试日志获取...")
        console_logs = manager.get_console_logs()
        print(f"✓ 控制台日志: {len(console_logs)} 条")
        
        errors = manager.get_errors()
        print(f"✓ 错误日志: {len(errors)} 条")
        
        network_logs = manager.get_network_logs()
        print(f"✓ 网络日志: {len(network_logs)} 条")
        
        # 5. 获取 Streamlit 状态
        print("\n[5/5] 测试 Streamlit 状态...")
        state = await manager.get_streamlit_state()
        print(f"✓ Streamlit 状态:")
        print(f"  - 错误: {len(state['errors'])} 个")
        print(f"  - 警告: {len(state['warnings'])} 个")
        print(f"  - 成功消息: {len(state['successes'])} 个")
        print(f"  - URL: {state['url']}")
        
        print("\n" + "=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理
        print("\n清理资源...")
        await manager.close()
        print("✓ 清理完成")


async def test_database():
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("测试数据库连接")
    print("=" * 60)
    
    try:
        from storage.database import Database
        
        db = Database()
        db.connect()
        db.init_tables()
        
        # 测试查询
        stats = db.fetchone("""
            SELECT 
                COUNT(*) as total_kols
            FROM youtube_kols
        """)
        
        print(f"✓ 数据库连接成功")
        print(f"✓ YouTube KOL 总数: {stats['total_kols']}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        return False


async def main():
    """运行所有测试"""
    print("\n开始测试 MCP Server 组件...\n")
    
    # 测试数据库
    db_ok = await test_database()
    
    # 测试浏览器
    browser_ok = await test_browser_manager()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"数据库: {'✓ 通过' if db_ok else '✗ 失败'}")
    print(f"浏览器: {'✓ 通过' if browser_ok else '✗ 失败'}")
    
    if db_ok and browser_ok:
        print("\n所有组件正常！可以使用 MCP Server 了。")
        print("\n下一步：")
        print("1. 配置 .kiro/settings/mcp.json")
        print("2. 重启 Kiro")
        print("3. 问 AI：'帮我截图看看前端界面'")
    else:
        print("\n有组件测试失败，请检查错误信息。")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
