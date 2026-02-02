#!/usr/bin/env python3
"""
爬虫项目的完整 MCP Server
功能：
1. 数据库查询和操作
2. 浏览器控制和监控
3. 前端调试（截图、日志、网络）
4. UI 自动化测试
"""
import asyncio
import json
import sys
import os
from typing import Any, Optional
import base64
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from storage.database import Database
from storage.repositories.github_repository import GitHubRepository
from utils.config_loader import load_config
from mcp_servers.browser_manager import BrowserManager

# 创建 MCP Server
app = Server("ai-kol-crawler")

# 全局变量
db = None
github_repo = None
config = None
browser_manager = None


def init_database():
    """初始化数据库"""
    global db, github_repo, config
    
    if not db:
        db = Database()
        db.connect()
        db.init_tables()
    
    if not github_repo:
        github_repo = GitHubRepository(db)
    
    if not config:
        config = load_config()


async def init_browser():
    """初始化浏览器"""
    global browser_manager
    
    if not browser_manager:
        browser_manager = BrowserManager(PROJECT_ROOT)
        # 启动 Streamlit
        await browser_manager.start_streamlit()
        # 启动浏览器
        await browser_manager.start_browser()


@app.list_resources()
async def list_resources() -> list[Resource]:
    """列出可用的资源"""
    return [
        # 数据资源
        Resource(
            uri="crawler://stats/youtube",
            name="YouTube 统计数据",
            mimeType="application/json",
            description="YouTube KOL 的统计信息"
        ),
        Resource(
            uri="crawler://stats/github",
            name="GitHub 统计数据",
            mimeType="application/json",
            description="GitHub 开发者的统计信息"
        ),
        Resource(
            uri="crawler://config",
            name="爬虫配置",
            mimeType="application/json",
            description="当前的爬虫配置参数"
        ),
        # 浏览器资源
        Resource(
            uri="browser://screenshot/latest",
            name="最新截图",
            mimeType="image/png",
            description="浏览器的最新截图"
        ),
        Resource(
            uri="browser://logs/console",
            name="控制台日志",
            mimeType="application/json",
            description="浏览器控制台的最新日志"
        ),
        Resource(
            uri="browser://logs/errors",
            name="错误日志",
            mimeType="application/json",
            description="浏览器的错误日志"
        ),
        Resource(
            uri="browser://logs/network",
            name="网络日志",
            mimeType="application/json",
            description="网络请求和响应日志"
        ),
        Resource(
            uri="browser://state",
            name="Streamlit 状态",
            mimeType="application/json",
            description="Streamlit 应用的当前状态"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    
    # 数据库资源
    if uri.startswith("crawler://"):
        init_database()
        
        if uri == "crawler://stats/youtube":
            stats = db.fetchone("""
                SELECT 
                    COUNT(*) as total_kols,
                    COUNT(CASE WHEN status = 'qualified' THEN 1 END) as qualified_kols,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_kols,
                    AVG(ai_ratio) as avg_ai_ratio,
                    AVG(subscribers) as avg_subscribers
                FROM youtube_kols
            """)
            return json.dumps(stats, indent=2, ensure_ascii=False)
        
        elif uri == "crawler://stats/github":
            stats = github_repo.get_statistics()
            return json.dumps(stats, indent=2, ensure_ascii=False)
        
        elif uri == "crawler://config":
            return json.dumps(config, indent=2, ensure_ascii=False)
    
    # 浏览器资源
    elif uri.startswith("browser://"):
        await init_browser()
        
        if uri == "browser://screenshot/latest":
            # 返回 base64 编码的图片
            screenshot_base64 = await browser_manager.get_screenshot_base64()
            return screenshot_base64
        
        elif uri == "browser://logs/console":
            logs = browser_manager.get_console_logs()
            return json.dumps(logs, indent=2, ensure_ascii=False)
        
        elif uri == "browser://logs/errors":
            errors = browser_manager.get_errors()
            return json.dumps(errors, indent=2, ensure_ascii=False)
        
        elif uri == "browser://logs/network":
            network = browser_manager.get_network_logs()
            return json.dumps(network, indent=2, ensure_ascii=False)
        
        elif uri == "browser://state":
            state = await browser_manager.get_streamlit_state()
            return json.dumps(state, indent=2, ensure_ascii=False)
    
    raise ValueError(f"未知资源: {uri}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        # ========== 数据库工具 ==========
        Tool(
            name="query_database",
            description="执行 SQL 查询获取爬虫数据（只支持 SELECT）",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL 查询语句"
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="get_kol_details",
            description="获取指定 YouTube KOL 的详细信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "YouTube 频道 ID"
                    }
                },
                "required": ["channel_id"]
            }
        ),
        Tool(
            name="search_kols",
            description="搜索 YouTube KOL",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "min_subscribers": {
                        "type": "integer",
                        "description": "最小订阅数",
                        "default": 0
                    }
                },
                "required": ["keyword"]
            }
        ),
        
        # ========== 浏览器工具 ==========
        Tool(
            name="browser_screenshot",
            description="对当前浏览器页面截图，返回图片的 base64 编码",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "截图文件名（可选）"
                    }
                }
            }
        ),
        Tool(
            name="browser_get_console_logs",
            description="获取浏览器控制台日志，包括 log、warn、error 等",
            inputSchema={
                "type": "object",
                "properties": {
                    "last_n": {
                        "type": "integer",
                        "description": "获取最近 N 条日志",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="browser_get_errors",
            description="获取浏览器的 JavaScript 错误",
            inputSchema={
                "type": "object",
                "properties": {
                    "last_n": {
                        "type": "integer",
                        "description": "获取最近 N 条错误",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="browser_get_network_logs",
            description="获取网络请求和响应日志",
            inputSchema={
                "type": "object",
                "properties": {
                    "last_n": {
                        "type": "integer",
                        "description": "获取最近 N 条日志",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="browser_click_element",
            description="点击页面上的元素（用于测试 UI）",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS 选择器，如 'button[key=\"start_crawler\"]' 或 'text=开始爬虫'"
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="browser_get_element_info",
            description="获取页面元素的信息（位置、文本、可见性等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS 选择器"
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="browser_execute_js",
            description="在浏览器中执行 JavaScript 代码",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的 JavaScript 代码"
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="browser_get_streamlit_state",
            description="获取 Streamlit 应用的当前状态（错误、警告、成功消息等）",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="browser_reload",
            description="刷新浏览器页面",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="browser_clear_logs",
            description="清空浏览器日志（控制台、网络、错误）",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        # ========== 配置工具 ==========
        Tool(
            name="update_config",
            description="更新爬虫配置",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "配置节（如 crawler, github）"
                    },
                    "key": {
                        "type": "string",
                        "description": "配置键"
                    },
                    "value": {
                        "description": "新值"
                    }
                },
                "required": ["section", "key", "value"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent]:
    """调用工具"""
    
    # ========== 数据库工具 ==========
    if name == "query_database":
        init_database()
        sql = arguments["sql"]
        
        if not sql.strip().upper().startswith("SELECT"):
            return [TextContent(type="text", text="错误：只支持 SELECT 查询")]
        
        try:
            results = db.fetchall(sql)
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2, ensure_ascii=False)
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"查询失败: {str(e)}")]
    
    elif name == "get_kol_details":
        init_database()
        channel_id = arguments["channel_id"]
        
        kol = db.fetchone("SELECT * FROM youtube_kols WHERE channel_id = ?", (channel_id,))
        if not kol:
            return [TextContent(type="text", text=f"未找到频道: {channel_id}")]
        
        videos = db.fetchall(
            "SELECT * FROM youtube_videos WHERE channel_id = ? ORDER BY views DESC LIMIT 10",
            (channel_id,)
        )
        
        result = {"kol": kol, "top_videos": videos}
        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
    
    elif name == "search_kols":
        init_database()
        keyword = arguments["keyword"]
        min_subscribers = arguments.get("min_subscribers", 0)
        
        sql = """
            SELECT channel_name, channel_url, subscribers, ai_ratio, avg_views
            FROM youtube_kols
            WHERE (channel_name LIKE ? OR bio LIKE ?)
              AND subscribers >= ?
              AND status = 'qualified'
            ORDER BY subscribers DESC
            LIMIT 20
        """
        
        results = db.fetchall(sql, (f"%{keyword}%", f"%{keyword}%", min_subscribers))
        return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]
    
    # ========== 浏览器工具 ==========
    elif name == "browser_screenshot":
        await init_browser()
        filename = arguments.get("filename")
        
        try:
            filepath = await browser_manager.screenshot(filename)
            
            # 读取图片并返回 base64
            with open(filepath, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            return [
                TextContent(type="text", text=f"截图已保存: {filepath}"),
                ImageContent(type="image", data=image_data, mimeType="image/png")
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"截图失败: {str(e)}")]
    
    elif name == "browser_get_console_logs":
        await init_browser()
        last_n = arguments.get("last_n", 20)
        
        logs = browser_manager.get_console_logs(last_n)
        return [TextContent(type="text", text=json.dumps(logs, indent=2, ensure_ascii=False))]
    
    elif name == "browser_get_errors":
        await init_browser()
        last_n = arguments.get("last_n", 10)
        
        errors = browser_manager.get_errors(last_n)
        return [TextContent(type="text", text=json.dumps(errors, indent=2, ensure_ascii=False))]
    
    elif name == "browser_get_network_logs":
        await init_browser()
        last_n = arguments.get("last_n", 20)
        
        network = browser_manager.get_network_logs(last_n)
        return [TextContent(type="text", text=json.dumps(network, indent=2, ensure_ascii=False))]
    
    elif name == "browser_click_element":
        await init_browser()
        selector = arguments["selector"]
        
        try:
            success = await browser_manager.click_element(selector)
            if success:
                return [TextContent(type="text", text=f"已点击元素: {selector}")]
            else:
                return [TextContent(type="text", text=f"点击失败: 未找到元素 {selector}")]
        except Exception as e:
            return [TextContent(type="text", text=f"点击失败: {str(e)}")]
    
    elif name == "browser_get_element_info":
        await init_browser()
        selector = arguments["selector"]
        
        info = await browser_manager.get_element_info(selector)
        if info:
            return [TextContent(type="text", text=json.dumps(info, indent=2, ensure_ascii=False))]
        else:
            return [TextContent(type="text", text=f"未找到元素: {selector}")]
    
    elif name == "browser_execute_js":
        await init_browser()
        code = arguments["code"]
        
        try:
            result = await browser_manager.execute_javascript(code)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        except Exception as e:
            return [TextContent(type="text", text=f"执行失败: {str(e)}")]
    
    elif name == "browser_get_streamlit_state":
        await init_browser()
        
        state = await browser_manager.get_streamlit_state()
        return [TextContent(type="text", text=json.dumps(state, indent=2, ensure_ascii=False))]
    
    elif name == "browser_reload":
        await init_browser()
        
        try:
            await browser_manager.page.reload(wait_until="networkidle")
            return [TextContent(type="text", text="页面已刷新")]
        except Exception as e:
            return [TextContent(type="text", text=f"刷新失败: {str(e)}")]
    
    elif name == "browser_clear_logs":
        await init_browser()
        browser_manager.clear_logs()
        return [TextContent(type="text", text="日志已清空")]
    
    # ========== 配置工具 ==========
    elif name == "update_config":
        from utils.config_loader import save_config
        init_database()
        
        section = arguments["section"]
        key = arguments["key"]
        value = arguments["value"]
        
        try:
            if section not in config:
                config[section] = {}
            
            config[section][key] = value
            save_config(config)
            
            return [TextContent(type="text", text=f"配置已更新: {section}.{key} = {value}")]
        except Exception as e:
            return [TextContent(type="text", text=f"更新失败: {str(e)}")]
    
    else:
        return [TextContent(type="text", text=f"未知工具: {name}")]


async def main():
    """运行 MCP Server"""
    from mcp.server.stdio import stdio_server
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    finally:
        # 清理资源
        if browser_manager:
            await browser_manager.close()
        if db:
            db.close()


if __name__ == "__main__":
    asyncio.run(main())
