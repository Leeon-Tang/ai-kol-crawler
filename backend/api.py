"""
FastAPI 后端入口
多平台爬虫系统 API
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
import asyncio
import json
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 导入后端模块（使用 backend. 前缀）
from backend.utils.log_manager import add_log, get_recent_logs
from backend.utils.crawler_status import set_crawler_running, is_crawler_running, should_stop
from backend.utils.config_loader import load_config
from backend.storage.database import Database

# 创建 FastAPI 应用
app = FastAPI(
    title="多平台爬虫系统 API",
    description="支持 YouTube、GitHub、Twitter 等多平台的爬虫系统",
    version="2.0.0"
)

# CORS 配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
CRAWLER_STATUS_FILE = os.path.join(PROJECT_ROOT, "data", "crawler_status.txt")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# ============================================
# Pydantic 模型
# ============================================

class CrawlerTaskRequest(BaseModel):
    platform: str  # youtube, github, twitter
    task_type: str  # discovery, expand, etc.
    params: Optional[Dict[str, Any]] = {}

class ExportRequest(BaseModel):
    platform: str
    format: str = "xlsx"  # xlsx, csv

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]

# ============================================
# API 路由
# ============================================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "多平台爬虫系统 API",
        "version": "2.0.0",
        "frontend": "http://localhost:3000",
        "docs": "/docs"
    }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "crawler_running": is_crawler_running(CRAWLER_STATUS_FILE),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/statistics/{platform}")
async def get_statistics(platform: str):
    """获取平台统计数据"""
    db = None
    try:
        db = Database()
        db.connect()
        
        if platform == "youtube":
            from backend.storage.repositories.youtube_repository import YouTubeRepository
            repo = YouTubeRepository(db)
            stats = repo.get_statistics()
        elif platform == "github":
            from backend.storage.repositories.github_repository import GitHubRepository
            repo = GitHubRepository(db)
            stats = repo.get_statistics()
        elif platform == "github_academic":
            from backend.storage.repositories.github_academic_repository import GitHubAcademicRepository
            repo = GitHubAcademicRepository(db)
            stats = repo.get_statistics()
        elif platform == "twitter":
            from backend.storage.repositories.twitter_repository import TwitterRepository
            repo = TwitterRepository(db)
            stats = repo.get_statistics()
        else:
            raise HTTPException(status_code=400, detail="不支持的平台")
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()

@app.get("/api/data/{platform}")
async def get_platform_data(
    platform: str,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None
):
    """获取平台数据列表"""
    db = None
    try:
        db = Database()
        db.connect()
        
        if platform == "youtube":
            from backend.storage.repositories.youtube_repository import YouTubeRepository
            repo = YouTubeRepository(db)
            data = repo.get_kols_paginated(page, page_size, status)
        elif platform == "github":
            from backend.storage.repositories.github_repository import GitHubRepository
            repo = GitHubRepository(db)
            data = repo.get_developers_paginated(page, page_size, status)
        elif platform == "github_academic":
            from backend.storage.repositories.github_academic_repository import GitHubAcademicRepository
            repo = GitHubAcademicRepository(db)
            # 需要添加分页方法
            data = repo.get_academic_developers_paginated(page, page_size, status)
        elif platform == "twitter":
            from backend.storage.repositories.twitter_repository import TwitterRepository
            repo = TwitterRepository(db)
            data = repo.get_users_paginated(page, page_size, status)
        else:
            raise HTTPException(status_code=400, detail="不支持的平台")
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()

@app.post("/api/crawler/start")
async def start_crawler(request: CrawlerTaskRequest, background_tasks: BackgroundTasks):
    """启动爬虫任务"""
    if is_crawler_running(CRAWLER_STATUS_FILE):
        raise HTTPException(status_code=400, detail="爬虫正在运行中")
    
    try:
        # 在后台运行爬虫任务
        background_tasks.add_task(
            run_crawler_task,
            request.platform,
            request.task_type,
            request.params
        )
        
        return {
            "status": "started",
            "platform": request.platform,
            "task_type": request.task_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawler/stop")
async def stop_crawler():
    """停止爬虫任务"""
    try:
        set_crawler_running(False, CRAWLER_STATUS_FILE, add_log)
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """获取日志"""
    try:
        logs = get_recent_logs(LOG_DIR, lines)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket 实时日志推送"""
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接，等待客户端消息
            data = await websocket.receive_text()
            # 这里可以处理客户端发来的消息
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/config")
async def get_config():
    """获取配置"""
    try:
        config = load_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def update_config(request: ConfigUpdateRequest):
    """更新配置"""
    try:
        config_path = os.path.join(PROJECT_ROOT, "config", "config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(request.config, f, indent=2, ensure_ascii=False)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/{platform}")
async def export_data(platform: str, format: str = "xlsx"):
    """导出数据"""
    try:
        if platform == "youtube":
            from backend.tasks.youtube.export import export_kol_report
            file_path = export_kol_report(format)
        elif platform == "github":
            from backend.tasks.github.export import export_developers
            file_path = export_developers(format)
        elif platform == "github_academic":
            from backend.tasks.github.export_academic import GitHubAcademicExportTask
            db = Database()
            db.connect()
            from backend.storage.repositories.github_academic_repository import GitHubAcademicRepository
            repo = GitHubAcademicRepository(db)
            task = GitHubAcademicExportTask(repo)
            file_path = task.export_all_academic_developers()
            db.close()
        elif platform == "twitter":
            from backend.tasks.twitter.export import export_users
            file_path = export_users(format)
        else:
            raise HTTPException(status_code=400, detail="不支持的平台")
        
        return FileResponse(
            file_path,
            filename=os.path.basename(file_path),
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# 后台任务函数
# ============================================

async def run_crawler_task(platform: str, task_type: str, params: dict):
    """运行爬虫任务"""
    db = None
    try:
        set_crawler_running(True, CRAWLER_STATUS_FILE, add_log)
        add_log(f"开始执行任务: {platform} - {task_type}", "INFO")
        
        # 广播任务开始
        await manager.broadcast({
            "type": "task_start",
            "platform": platform,
            "task_type": task_type
        })
        
        db = Database()
        db.connect()
        
        if platform == "youtube":
            from backend.storage.repositories.youtube_repository import YouTubeRepository
            from backend.storage.repositories.github_repository import GitHubRepository
            from backend.storage.repositories.github_academic_repository import GitHubAcademicRepository
            repo = YouTubeRepository(db)
            await run_youtube_task(task_type, repo, params)
        elif platform == "github":
            from backend.storage.repositories.github_repository import GitHubRepository
            from backend.storage.repositories.github_academic_repository import GitHubAcademicRepository
            repo = GitHubRepository(db)
            academic_repo = GitHubAcademicRepository(db)
            await run_github_task(task_type, repo, academic_repo, params)
        elif platform == "twitter":
            from backend.storage.repositories.twitter_repository import TwitterRepository
            repo = TwitterRepository(db)
            await run_twitter_task(task_type, repo, params)
        
        add_log(f"任务完成: {platform} - {task_type}", "SUCCESS")
        
        # 广播任务完成
        await manager.broadcast({
            "type": "task_complete",
            "platform": platform,
            "task_type": task_type
        })
        
    except Exception as e:
        add_log(f"任务失败: {str(e)}", "ERROR")
        await manager.broadcast({
            "type": "task_error",
            "error": str(e)
        })
    finally:
        if db:
            db.close()
        set_crawler_running(False, CRAWLER_STATUS_FILE, add_log)

async def run_youtube_task(task_type: str, repository, params: dict):
    """运行 YouTube 任务"""
    from backend.platforms.youtube.scraper import YouTubeScraper
    from backend.platforms.youtube.searcher import KeywordSearcher
    from backend.platforms.youtube.analyzer import KOLAnalyzer
    from backend.platforms.youtube.expander import KOLExpander
    from backend.platforms.youtube.filter import KOLFilter
    from backend.tasks.youtube.discovery import YouTubeDiscoveryTask
    from backend.tasks.youtube.expand import YouTubeExpandTask
    
    scraper = YouTubeScraper()
    searcher = KeywordSearcher(scraper)
    analyzer = KOLAnalyzer(scraper)
    expander = KOLExpander(scraper)
    filter_obj = KOLFilter(repository)
    
    if task_type == "discovery":
        task = YouTubeDiscoveryTask(searcher, analyzer, filter_obj, repository)
        keyword_limit = params.get('keyword_limit', 5)
        task.run(keyword_limit)
    elif task_type == "expand":
        task = YouTubeExpandTask(expander, analyzer, filter_obj, repository)
        task.run()

async def run_github_task(task_type: str, repository, academic_repository, params: dict):
    """运行 GitHub 任务"""
    from backend.platforms.github.scraper import GitHubScraper
    from backend.platforms.github.searcher import GitHubSearcher
    from backend.platforms.github.analyzer import GitHubAnalyzer
    from backend.tasks.github.discovery import GitHubDiscoveryTask
    
    scraper = GitHubScraper()
    searcher = GitHubSearcher(scraper, repository)
    analyzer = GitHubAnalyzer(scraper)
    
    if task_type == "discovery":
        task = GitHubDiscoveryTask(searcher, analyzer, repository, academic_repository)
        max_developers = params.get('max_developers', 50)
        task.run(max_developers=max_developers)

async def run_twitter_task(task_type: str, repository, params: dict):
    """运行 Twitter 任务"""
    from backend.tasks.twitter.discovery import TwitterDiscoveryTask
    
    task = TwitterDiscoveryTask()
    
    if task_type == "keyword_discovery":
        keywords = params.get('keywords', [])
        max_results = params.get('max_results', 10)
        task.discover_by_keywords(keywords, max_results_per_keyword=max_results)
    elif task_type == "hashtag_discovery":
        hashtags = params.get('hashtags', [])
        max_results = params.get('max_results', 20)
        task.discover_by_hashtags(hashtags, max_results=max_results)


if __name__ == "__main__":
    import uvicorn
    # 禁用颜色输出，避免Windows CMD显示ANSI代码乱码
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8501,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "access": {
                    "format": "%(asctime)s - %(levelname)s - %(client_addr)s - %(request_line)s - %(status_code)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout"
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout"
                }
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False}
            }
        }
    )

