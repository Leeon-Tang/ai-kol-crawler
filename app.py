# -*- coding: utf-8 -*-
"""
多平台爬虫系统 - Streamlit Web界面
支持YouTube、GitHub等多个平台
"""
import streamlit as st
import pandas as pd
import time
import threading
import queue
from datetime import datetime
import json
import os
import sys
import traceback

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# 状态文件和日志目录路径
CRAWLER_STATUS_FILE = os.path.join(PROJECT_ROOT, "data", "crawler_status.txt")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# 页面配置
st.set_page_config(
    page_title="多平台爬虫系统",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 侧边栏容器 - 最小化间距 */
    section[data-testid="stSidebar"] {
        padding-top: 0.3rem !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-left: 0.3rem !important;
        padding-right: 0.3rem !important;
    }
    
    /* 主标题样式 */
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 0.5rem 0;
        margin-bottom: 1rem;
    }
    
    /* 侧边栏所有按钮 - 完全透明无背景 */
    section[data-testid="stSidebar"] button[kind="secondary"],
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: transparent !important;
        background-image: none !important;
        border: none !important;
        box-shadow: none !important;
        color: #d0d0d0 !important;
        font-weight: 400 !important;
        font-size: 0.85rem !important;
        padding: 0.3rem 0.5rem !important;
        text-align: left !important;
        border-radius: 6px !important;
    }
    
    /* 侧边栏按钮悬停 */
    section[data-testid="stSidebar"] button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
    }
    
    /* 侧边栏激活按钮 */
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: rgba(31, 119, 180, 0.15) !important;
        color: #4da3ff !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: rgba(31, 119, 180, 0.25) !important;
    }
    
    /* 顶级按钮（数据浏览、日志、设置）- 加粗突出 */
    section[data-testid="stSidebar"] button[key*="data_browser"],
    section[data-testid="stSidebar"] button[key*="logs"],
    section[data-testid="stSidebar"] button[key*="settings"] {
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* 主内容区按钮保持原样（有背景色） */
    section[data-testid="stMain"] button {
        background-color: #1f77b4 !important;
        color: white !important;
        border: 1px solid #1f77b4 !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
    }
    section[data-testid="stMain"] button:hover {
        background-color: #1565c0 !important;
        border-color: #1565c0 !important;
    }
    
    /* 减小侧边栏元素间距 */
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        gap: 0.05rem !important;
    }
    
    /* 侧边栏分类标题 */
    section[data-testid="stSidebar"] h3 {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: #888 !important;
        margin-top: 0.3rem !important;
        margin-bottom: 0.2rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* 侧边栏统计数字 */
    .stat-number {
        font-size: 1.5rem;
        font-weight: 700;
        color: #4da3ff;
        margin: 0.1rem 0;
        line-height: 1;
    }
    
    /* 侧边栏caption */
    section[data-testid="stSidebar"] p[class*="caption"] {
        font-size: 0.7rem !important;
        color: #888 !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* 分割线 */
    section[data-testid="stSidebar"] hr {
        margin: 0.3rem 0 !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* 侧边栏标题 */
    section[data-testid="stSidebar"] h1 {
        margin-bottom: 0.1rem !important;
        padding-bottom: 0 !important;
        font-size: 1rem !important;
    }
    
    /* 导出按钮样式 */
    .export-buttons {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    
    /* 数据表样式 */
    .dataframe {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# 全局日志队列
log_queue = queue.Queue()
log_list = []

def add_log(message, level="INFO"):
    """添加日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    log_queue.put(log_entry)
    log_list.append(log_entry)
    if len(log_list) > 1000:
        log_list.pop(0)
    
    # 写入文件
    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except:
        pass

def set_crawler_running(status):
    """设置爬虫运行状态"""
    try:
        status_dir = os.path.dirname(CRAWLER_STATUS_FILE)
        os.makedirs(status_dir, exist_ok=True)
        with open(CRAWLER_STATUS_FILE, 'w', encoding='utf-8') as f:
            f.write("running" if status else "stopped")
    except:
        pass

def is_crawler_running():
    """获取爬虫运行状态"""
    try:
        if os.path.exists(CRAWLER_STATUS_FILE):
            with open(CRAWLER_STATUS_FILE, 'r', encoding='utf-8') as f:
                status = f.read().strip()
                return status == "running"
    except:
        pass
    return False

def init_session_state():
    """初始化会话状态"""
    if 'db' not in st.session_state:
        st.session_state.db = None
    if 'youtube_repository' not in st.session_state:
        st.session_state.youtube_repository = None
    if 'github_repository' not in st.session_state:
        st.session_state.github_repository = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "youtube_dashboard"
    if 'jump_to_logs' not in st.session_state:
        st.session_state.jump_to_logs = False
    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = True

def connect_database():
    """连接数据库"""
    try:
        if st.session_state.db is None:
            from storage.database import Database
            from storage.repositories.youtube_repository import YouTubeRepository
            from storage.repositories.github_repository import GitHubRepository
            
            db = Database()
            db.connect()
            db.init_tables()
            
            # 尝试迁移旧数据
            try:
                from storage.migrations.migration_v2 import MigrationV2
                migration = MigrationV2()
                if migration.check_old_tables_exist():
                    add_log("检测到旧版数据，正在迁移...", "INFO")
                    migration.migrate()
                    add_log("数据迁移完成", "INFO")
            except Exception as e:
                add_log(f"数据迁移检查: {e}", "WARNING")
            
            st.session_state.db = db
            st.session_state.youtube_repository = YouTubeRepository(db)
            st.session_state.github_repository = GitHubRepository(db)
            return True
    except Exception as e:
        st.error(f"数据库连接失败: {str(e)}")
        return False
    return True

def get_statistics(platform='youtube'):
    """获取统计数据"""
    if platform == 'youtube' and st.session_state.youtube_repository:
        try:
            return st.session_state.youtube_repository.get_statistics()
        except:
            return {'total_kols': 0, 'qualified_kols': 0, 'pending_kols': 0, 'total_videos': 0, 'pending_expansions': 0}
    elif platform == 'github' and st.session_state.github_repository:
        try:
            return st.session_state.github_repository.get_statistics()
        except:
            return {'total_developers': 0, 'qualified_developers': 0, 'pending_developers': 0, 'total_repositories': 0}
    return {}

def clear_logs():
    """清空日志"""
    global log_list
    log_list.clear()
    log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")
    if os.path.exists(log_file):
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("")
            return True
        except:
            return False
    return True

def run_youtube_crawler_task(task_type, repository, **kwargs):
    """运行YouTube爬虫任务"""
    try:
        from platforms.youtube.scraper import YouTubeScraper
        from platforms.youtube.searcher import KeywordSearcher
        from platforms.youtube.analyzer import KOLAnalyzer
        from platforms.youtube.expander import KOLExpander
        from platforms.youtube.filter import KOLFilter
        from tasks.youtube.discovery import YouTubeDiscoveryTask
        from tasks.youtube.expand import YouTubeExpandTask
        
        set_crawler_running(True)
        add_log(f"开始执行任务: {task_type}", "INFO")
        
        scraper = YouTubeScraper()
        searcher = KeywordSearcher(scraper)
        analyzer = KOLAnalyzer(scraper)
        expander = KOLExpander(scraper)
        filter_obj = KOLFilter(repository)
        
        if task_type == "discovery":
            task = YouTubeDiscoveryTask(searcher, analyzer, filter_obj, repository)
            keyword_limit = kwargs.get('keyword_limit', 30)
            add_log(f"使用 {keyword_limit} 个关键词进行搜索", "INFO")
            task.run(keyword_limit)
        elif task_type == "expand":
            task = YouTubeExpandTask(expander, analyzer, filter_obj, repository)
            add_log("开始扩散任务", "INFO")
            task.run()
        
        add_log(f"任务完成: {task_type}", "SUCCESS")
    except Exception as e:
        add_log(f"任务执行失败: {str(e)}", "ERROR")
        add_log(traceback.format_exc(), "ERROR")
    finally:
        set_crawler_running(False)

def run_github_crawler_task(task_type, repository, **kwargs):
    """运行GitHub爬虫任务"""
    try:
        from platforms.github.scraper import GitHubScraper
        from platforms.github.searcher import GitHubSearcher
        from platforms.github.analyzer import GitHubAnalyzer
        from tasks.github.discovery import GitHubDiscoveryTask
        
        set_crawler_running(True)
        add_log(f"开始执行GitHub任务: {task_type}", "INFO")
        
        scraper = GitHubScraper()
        searcher = GitHubSearcher(scraper, repository)  # 传入repository用于去重
        analyzer = GitHubAnalyzer(scraper)
        
        if task_type == "discovery":
            task = GitHubDiscoveryTask(searcher, analyzer, repository)
            max_developers = kwargs.get('max_developers', 50)
            strategy = kwargs.get('strategy', 'comprehensive')
            task.run(max_developers=max_developers, strategy=strategy)
        
        add_log(f"GitHub任务完成: {task_type}", "SUCCESS")
    except Exception as e:
        add_log(f"GitHub任务执行失败: {str(e)}", "ERROR")
        add_log(traceback.format_exc(), "ERROR")
    finally:
        set_crawler_running(False)



def render_youtube_dashboard():
    """渲染YouTube仪表盘"""
    st.markdown('<div class="main-header">📊 YouTube 数据仪表盘</div>', unsafe_allow_html=True)
    
    stats = get_statistics('youtube')
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("总KOL数", stats.get('total_kols', 0))
    with col2:
        st.metric("合格KOL", stats.get('qualified_kols', 0))
    with col3:
        st.metric("待分析", stats.get('pending_kols', 0))
    with col4:
        st.metric("总视频数", stats.get('total_videos', 0))
    with col5:
        st.metric("待扩散", stats.get('pending_expansions', 0))
    
    st.divider()
    st.subheader("🌟 最近发现的合格KOL")
    
    if st.session_state.youtube_repository:
        recent_kols = st.session_state.youtube_repository.get_qualified_kols(limit=10)
        if recent_kols:
            df = pd.DataFrame(recent_kols)
            display_df = df[['channel_name', 'subscribers', 'ai_ratio', 'avg_views', 'avg_comments', 'engagement_rate', 'discovered_at']].copy()
            display_df.columns = ['频道名称', '订阅数', 'AI占比', '平均观看', '平均评论', '互动率', '爬取时间']
            display_df['AI占比'] = display_df['AI占比'].apply(lambda x: f"{x*100:.1f}%")
            display_df['互动率'] = display_df['互动率'].apply(lambda x: f"{x:.2f}%")
            display_df['订阅数'] = display_df['订阅数'].apply(lambda x: f"{x:,}")
            display_df['平均观看'] = display_df['平均观看'].apply(lambda x: f"{x:,}")
            display_df['平均评论'] = display_df['平均评论'].apply(lambda x: f"{x:,}")
            st.dataframe(display_df, width='stretch', hide_index=True)
        else:
            st.info("📭 暂无数据，请先运行爬虫任务")
    
    if st.button("🔄 刷新数据", key="refresh_youtube_dashboard"):
        st.rerun()

def render_github_dashboard():
    """渲染GitHub仪表盘"""
    st.markdown('<div class="main-header">📊 GitHub 数据仪表盘</div>', unsafe_allow_html=True)
    
    stats = get_statistics('github')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总开发者数", stats.get('total_developers', 0))
    with col2:
        st.metric("合格开发者", stats.get('qualified_developers', 0))
    with col3:
        st.metric("待分析", stats.get('pending_developers', 0))
    with col4:
        st.metric("总仓库数", stats.get('total_repositories', 0))
    
    st.divider()
    st.subheader("🌟 最近发现的独立开发者")
    
    if st.session_state.github_repository:
        recent_devs = st.session_state.github_repository.get_qualified_developers(limit=10)
        if recent_devs:
            df = pd.DataFrame(recent_devs)
            display_df = df[['username', 'name', 'followers', 'total_stars', 'discovered_at']].copy()
            display_df.columns = ['用户名', '姓名', 'Followers', '总Stars', '发现时间']
            display_df['Followers'] = display_df['Followers'].apply(lambda x: f"{x:,}")
            display_df['总Stars'] = display_df['总Stars'].apply(lambda x: f"{x:,}")
            st.dataframe(display_df, width='stretch', hide_index=True)
        else:
            st.info("📭 暂无数据，请先运行爬虫任务")
    
    if st.button("🔄 刷新数据", key="refresh_github_dashboard"):
        st.rerun()

def render_youtube_crawler():
    """渲染YouTube爬虫控制"""
    st.markdown('<div class="main-header">🚀 YouTube 爬虫控制</div>', unsafe_allow_html=True)
    
    running = is_crawler_running()
    if running:
        st.warning("⚠️ 爬虫正在运行中，请等待任务完成...")
        st.info("💡 切换到「📝 日志查看」页面查看实时进度")
        if st.button("⏹️ 标记为已完成", key="mark_complete"):
            set_crawler_running(False)
            st.rerun()
    else:
        st.success("✅ 爬虫空闲，可以启动新任务")
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔍 初始发现任务")
        st.write("通过关键词搜索YouTube，发现新的AI KOL")
        
        keyword_limit = st.slider(
            "使用关键词数量",
            min_value=1,
            max_value=50,
            value=5,
            step=1,
            help="选择要使用的关键词数量，数量越多发现的KOL越多，但耗时也越长"
        )
        
        st.info(f"预计搜索 {keyword_limit * 5} 个频道，耗时约 {keyword_limit * 2} 分钟")
        
        if st.button("▶️ 开始初始发现", disabled=running, key="start_youtube_discovery"):
                if not st.session_state.youtube_repository:
                    st.error("数据库未连接，无法启动任务")
                else:
                    clear_logs()
                    add_log("=" * 60, "INFO")
                    add_log("开始新的爬虫任务 - YouTube初始发现", "INFO")
                    add_log("=" * 60, "INFO")
                    add_log(f"用户启动初始发现任务，关键词数量: {keyword_limit}", "INFO")
                    
                    thread = threading.Thread(
                        target=run_youtube_crawler_task,
                        args=("discovery", st.session_state.youtube_repository),
                        kwargs={'keyword_limit': keyword_limit}
                    )
                    thread.daemon = True
                    thread.start()
                    set_crawler_running(True)
                    st.session_state.jump_to_logs = True
                    st.session_state.auto_refresh_enabled = True
                    time.sleep(0.5)
                    st.rerun()
    
    with col2:
        st.subheader("🌐 扩散发现任务")
        st.write("从已有KOL的推荐列表中发现新KOL")
        
        stats = get_statistics('youtube')
        st.info(f"当前待扩散队列: {stats.get('pending_expansions', 0)} 个KOL")
        
        if stats.get('pending_expansions', 0) == 0:
            st.warning("扩散队列为空，请先运行初始发现任务")
        
        if st.button("▶️ 开始扩散发现", disabled=running or stats.get('pending_expansions', 0) == 0, key="start_youtube_expand"):
                if not st.session_state.youtube_repository:
                    st.error("数据库未连接，无法启动任务")
                else:
                    clear_logs()
                    add_log("=" * 60, "INFO")
                    add_log("开始新的爬虫任务 - YouTube扩散发现", "INFO")
                    add_log("=" * 60, "INFO")
                    add_log("用户启动扩散发现任务", "INFO")
                    
                    thread = threading.Thread(
                        target=run_youtube_crawler_task,
                        args=("expand", st.session_state.youtube_repository)
                    )
                    thread.daemon = True
                    thread.start()
                    set_crawler_running(True)
                    st.session_state.jump_to_logs = True
                    st.session_state.auto_refresh_enabled = True
                    time.sleep(0.5)
                    st.rerun()
    
    st.divider()
    
    with st.expander("⚙️ 高级配置", expanded=False):
        st.subheader("爬虫参数设置")
        col1, col2 = st.columns(2)
        with col1:
            ai_threshold = st.slider("AI内容占比阈值", min_value=0.1, max_value=0.9, value=0.3, step=0.05, format="%.0f%%")
            sample_videos = st.number_input("每个频道分析视频数", min_value=5, max_value=50, value=10, step=5)
        with col2:
            rate_limit = st.number_input("请求间隔(秒)", min_value=1, max_value=10, value=2, step=1)
            max_kols = st.number_input("最大KOL数量", min_value=100, max_value=10000, value=1000, step=100)
        if st.button("💾 保存配置"):
            st.success("配置已保存！")

def render_github_crawler():
    """渲染GitHub爬虫控制"""
    st.markdown('<div class="main-header">🚀 GitHub 爬虫控制</div>', unsafe_allow_html=True)
    
    running = is_crawler_running()
    if running:
        st.warning("⚠️ 爬虫正在运行中，请等待任务完成...")
        st.info("💡 切换到「📝 日志查看」页面查看实时进度")
        if st.button("⏹️ 标记为已完成", key="mark_complete_github"):
            set_crawler_running(False)
            st.rerun()
    else:
        st.success("✅ 爬虫空闲，可以启动新任务")
    
    st.divider()
    
    st.subheader("🔍 GitHub开发者发现")
    st.write("使用网页爬虫（无API限制）搜索GitHub，发现独立AI开发者")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        max_developers = st.slider(
            "最大爬取开发者数量",
            min_value=1,
            max_value=400,
            value=50,
            step=1,
            help="限制本次任务最多爬取的开发者数量"
        )
    
    with col2:
        strategy = st.selectbox(
            "搜索策略",
            ["quality_projects", "comprehensive", "keywords", "topics", "awesome", "explore", "indie"],
            index=0,
            format_func=lambda x: {
                "quality_projects": "🎯 优质项目贡献者（推荐）",
                "comprehensive": "📦 综合策略",
                "keywords": "🔑 仅关键词",
                "topics": "🏷️ 仅Topics",
                "awesome": "⭐ 仅Awesome列表",
                "explore": "🔭 仅Explore",
                "indie": "👤 仅独立开发者"
            }[x],
            help="优质项目策略：从Stable Diffusion、ComfyUI等优质AI项目中找贡献者（最精准）"
        )
    
    # 策略说明
    strategy_info = {
        "quality_projects": "从Stable Diffusion、ComfyUI等优质AI项目（100+ stars）中找贡献者，筛选有影响力的开发者（最精准，推荐）",
        "comprehensive": "智能组合多种策略，小数量时只用最快的方法，大数量时全策略覆盖",
        "keywords": "通过AI相关关键词搜索仓库，提取owner（快速，适合小数量）",
        "topics": "通过GitHub Topics标签搜索（中等速度，质量较高）",
        "awesome": "从Awesome列表提取贡献者（慢但质量高）",
        "explore": "搜索trending项目（覆盖面广）",
        "indie": "专门搜索独立开发者关键词（精准但数量少）"
    }
    
    st.info(f"💡 {strategy_info[strategy]}")
    
    # 预估时间
    if max_developers <= 10:
        estimated_time = "约1-2分钟"
    elif max_developers <= 50:
        estimated_time = "约3-5分钟"
    elif max_developers <= 100:
        estimated_time = "约8-12分钟"
    else:
        estimated_time = "约15-25分钟"
    
    st.caption(f"⏱️ 预计耗时：{estimated_time}（使用网页爬虫，无API限制）")
    
    if st.button("▶️ 开始GitHub发现", disabled=running, key="start_github_discovery"):
        if not st.session_state.github_repository:
            st.error("数据库未连接，无法启动任务")
        else:
            clear_logs()
            add_log("=" * 60, "INFO")
            add_log("开始新的爬虫任务 - GitHub开发者发现", "INFO")
            add_log("=" * 60, "INFO")
            add_log(f"用户启动GitHub发现任务", "INFO")
            add_log(f"  - 最大数量: {max_developers}", "INFO")
            add_log(f"  - 搜索策略: {strategy}", "INFO")
            add_log(f"  - 使用网页爬虫（无API限制）", "INFO")
            
            thread = threading.Thread(
                target=run_github_crawler_task,
                args=("discovery", st.session_state.github_repository),
                kwargs={"max_developers": max_developers, "strategy": strategy}
            )
            thread.daemon = True
            thread.start()
            set_crawler_running(True)
            st.session_state.jump_to_logs = True
            st.session_state.auto_refresh_enabled = True
            time.sleep(0.5)
            st.rerun()

def render_data_browser():
    """渲染统一的数据浏览页面"""
    st.markdown('<div class="main-header">📋 数据浏览</div>', unsafe_allow_html=True)
    
    # 初始化平台选择
    if 'data_browser_platform' not in st.session_state:
        st.session_state.data_browser_platform = "YouTube"
    
    # 平台选择 - 使用按钮组
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎥 YouTube", key="btn_yt_data", use_container_width=True, 
                    type="primary" if st.session_state.data_browser_platform == "YouTube" else "secondary"):
            st.session_state.data_browser_platform = "YouTube"
            st.rerun()
    with col2:
        if st.button("💻 GitHub", key="btn_gh_data", use_container_width=True,
                    type="primary" if st.session_state.data_browser_platform == "GitHub" else "secondary"):
            st.session_state.data_browser_platform = "GitHub"
            st.rerun()
    
    st.divider()
    
    if st.session_state.data_browser_platform == "YouTube":
        render_youtube_data_content()
    else:
        render_github_data_content()

def render_youtube_data_content():
    """渲染YouTube数据内容"""
    if not st.session_state.youtube_repository:
        st.warning("请先连接数据库")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("状态筛选", ["全部", "合格", "待分析", "已拒绝"], index=1, key="yt_status")
    with col2:
        sort_by = st.selectbox("排序方式", ["AI占比", "订阅数", "平均观看", "爬取时间"], index=0, key="yt_sort")
    with col3:
        limit = st.number_input("显示数量", min_value=10, max_value=1000, value=50, step=10, key="yt_limit")
    
    status_map = {"全部": None, "合格": "qualified", "待分析": "pending", "已拒绝": "rejected"}
    sort_map = {"AI占比": "ai_ratio DESC", "订阅数": "subscribers DESC", "平均观看": "avg_views DESC", "爬取时间": "discovered_at DESC"}
    
    query = "SELECT * FROM youtube_kols"
    if status_filter != "全部":
        query += f" WHERE status = '{status_map[status_filter]}'"
    query += f" ORDER BY {sort_map[sort_by]} LIMIT {limit}"
    
    kols = st.session_state.db.fetchall(query)
    
    if kols:
        df = pd.DataFrame(kols)
        display_columns = ['channel_name', 'channel_url', 'subscribers', 'total_videos', 'ai_ratio',
                         'avg_views', 'avg_likes', 'avg_comments', 'engagement_rate', 'contact_info', 'status', 'discovered_at']
        display_df = df[display_columns].copy()
        display_df.columns = ['频道名称', '频道链接', '订阅数', '总视频', 'AI占比', '平均观看', '平均点赞', '平均评论', '互动率', '联系方式', '状态', '爬取时间']
        
        display_df['总视频'] = display_df['总视频'].apply(lambda x: str(int(x)))
        display_df['AI占比'] = display_df['AI占比'].apply(lambda x: f"{x*100:.1f}%")
        display_df['互动率'] = display_df['互动率'].apply(lambda x: f"{x:.2f}%")
        display_df['订阅数'] = display_df['订阅数'].apply(lambda x: f"{x:,}")
        display_df['平均观看'] = display_df['平均观看'].apply(lambda x: f"{x:,}")
        display_df['平均点赞'] = display_df['平均点赞'].apply(lambda x: f"{x:,}")
        display_df['平均评论'] = display_df['平均评论'].apply(lambda x: f"{x:,}")
        display_df['联系方式'] = display_df['联系方式'].fillna('')
        
        def format_time(dt):
            if pd.isna(dt):
                return ""
            if isinstance(dt, str):
                dt = pd.to_datetime(dt)
            dt_beijing = dt + pd.Timedelta(hours=8)
            return dt_beijing.strftime('%Y-%m-%d %H:%M:%S')
        
        display_df['爬取时间'] = display_df['爬取时间'].apply(format_time)
        
        table_height = min(max(len(display_df) * 35 + 50, 200), 800)
        st.dataframe(display_df, width='stretch', hide_index=True, height=table_height,
                    column_config={"频道链接": st.column_config.LinkColumn("频道链接", help="点击打开YouTube频道")})
        
        st.divider()
        
        # 导出按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 导出Excel", key="export_yt_excel", use_container_width=True):
                from tasks.youtube.export import YouTubeExportTask
                export_task = YouTubeExportTask(st.session_state.youtube_repository)
                filepath = export_task.run()
                if filepath:
                    add_log(f"导出Excel: {filepath}", "SUCCESS")
        with col2:
            csv = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下载CSV", 
                data=csv,
                file_name=f"youtube_kol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("📭 暂无数据")

def render_github_data_content():
    """渲染GitHub数据内容"""
    if not st.session_state.github_repository:
        st.warning("请先连接数据库")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("状态筛选", ["全部", "合格", "待分析", "已拒绝"], index=1, key="gh_status")
    with col2:
        sort_by = st.selectbox("排序方式", ["总Stars", "Followers", "仓库数", "发现时间"], index=0, key="gh_sort")
    with col3:
        limit = st.number_input("显示数量", min_value=10, max_value=1000, value=50, step=10, key="gh_limit")
    
    status_map = {"全部": None, "合格": "qualified", "待分析": "pending", "已拒绝": "rejected"}
    sort_map = {"总Stars": "total_stars DESC", "Followers": "followers DESC", "仓库数": "public_repos DESC", "发现时间": "discovered_at DESC"}
    
    query = "SELECT * FROM github_developers"
    if status_filter != "全部":
        query += f" WHERE status = '{status_map[status_filter]}'"
    query += f" ORDER BY {sort_map[sort_by]} LIMIT {limit}"
    
    devs = st.session_state.db.fetchall(query)
    
    if devs:
        df = pd.DataFrame(devs)
        display_columns = ['username', 'name', 'profile_url', 'followers', 'public_repos', 'total_stars', 'contact_info', 'status', 'discovered_at']
        display_df = df[display_columns].copy()
        display_df.columns = ['用户名', '姓名', '主页链接', 'Followers', '仓库数', '总Stars', '联系方式', '状态', '发现时间']
        
        display_df['Followers'] = display_df['Followers'].apply(lambda x: f"{x:,}")
        display_df['仓库数'] = display_df['仓库数'].apply(lambda x: f"{x:,}")
        display_df['总Stars'] = display_df['总Stars'].apply(lambda x: f"{x:,}")
        display_df['联系方式'] = display_df['联系方式'].fillna('')
        
        table_height = min(max(len(display_df) * 35 + 50, 200), 800)
        st.dataframe(display_df, width='stretch', hide_index=True, height=table_height,
                    column_config={"主页链接": st.column_config.LinkColumn("主页链接", help="点击打开GitHub主页")})
        
        st.divider()
        
        # 导出按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 导出Excel", key="export_gh_excel", use_container_width=True):
                from tasks.github.export import GitHubExportTask
                export_task = GitHubExportTask(st.session_state.github_repository)
                filepath = export_task.run()
                if filepath:
                    add_log(f"导出Excel: {filepath}", "SUCCESS")
        with col2:
            csv = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下载CSV", 
                data=csv,
                file_name=f"github_devs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("📭 暂无数据")

def render_logs():
    """渲染日志查看页面"""
    st.markdown('<div class="main-header">📝 实时日志</div>', unsafe_allow_html=True)
    
    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = True
    
    crawler_is_running = is_crawler_running()
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 刷新日志", key="refresh_logs_btn"):
            st.rerun()
    with col2:
        if st.button("🗑️ 清空日志", key="clear_logs_btn"):
            if clear_logs():
                st.success("✅ 日志已清空")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ 清空日志失败")
    with col3:
        auto_refresh = st.checkbox("自动刷新 (每3秒)", value=st.session_state.auto_refresh_enabled,
                                   key="auto_refresh_checkbox_unique", help="爬虫运行时自动刷新日志")
        if auto_refresh != st.session_state.auto_refresh_enabled:
            st.session_state.auto_refresh_enabled = auto_refresh
    
    st.divider()
    
    log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")
    all_logs = []
    
    if os.path.exists(log_file):
        try:
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            for encoding in encodings:
                try:
                    with open(log_file, 'r', encoding=encoding) as f:
                        file_logs = f.readlines()
                        all_logs = [line.strip() for line in file_logs if line.strip()]
                    break
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            st.error(f"读取日志文件失败: {e}")
    
    log_count = len(all_logs)
    display_count = min(log_count, 200)
    
    if crawler_is_running:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); 
                    padding: 15px; border-radius: 10px; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background: #22c55e; 
                                border-radius: 50%; margin-right: 10px;"></div>
                    <span style="color: white; font-size: 18px; font-weight: bold;">
                        🔄 爬虫运行中...
                    </span>
                </div>
                <span style="color: #e0e7ff; font-size: 14px;">
                    共 {log_count} 条日志 | 显示最近 {display_count} 条
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #065f46 0%, #10b981 100%); 
                    padding: 15px; border-radius: 10px; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center;">
                    <span style="color: white; font-size: 18px; font-weight: bold;">
                        ✅ 爬虫已停止
                    </span>
                </div>
                <span style="color: #d1fae5; font-size: 14px;">
                    共 {log_count} 条日志 | 显示最近 {display_count} 条
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if all_logs:
        logs_text = "\n".join(all_logs[-200:])
        
        st.markdown("""
        <style>
        .log-container {
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            padding: 15px;
            border-radius: 5px;
            height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .log-container::-webkit-scrollbar {
            width: 10px;
        }
        .log-container::-webkit-scrollbar-track {
            background: #2d2d2d;
        }
        .log-container::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 5px;
        }
        .log-container::-webkit-scrollbar-thumb:hover {
            background: #777;
        }
        </style>
        """, unsafe_allow_html=True)
        
        log_container_id = f"log_container_{int(time.time() * 1000)}"
        import html
        logs_html = html.escape(logs_text)
        
        st.markdown(f'<div class="log-container" id="{log_container_id}">{logs_html}</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <script>
        setTimeout(function() {{
            var container = document.getElementById('{log_container_id}');
            if (container) {{
                container.scrollTop = container.scrollHeight;
            }}
        }}, 100);
        </script>
        """, unsafe_allow_html=True)
    else:
        st.info("暂无日志记录")
    
    if st.session_state.auto_refresh_enabled and crawler_is_running:
        time.sleep(3)
        st.rerun()

def render_ai_rules():
    """渲染AI规则配置页面 - 仅适用于YouTube"""
    st.markdown('<div class="main-header">🎯 AI过滤规则配置</div>', unsafe_allow_html=True)
    
    st.info("💡 配置AI内容识别规则，调整关键词和筛选条件（仅适用于YouTube平台）")
    
    config_path = os.path.join(PROJECT_ROOT, 'config', 'config.json')
    config_example_path = os.path.join(PROJECT_ROOT, 'config', 'config.example.json')
    
    if not os.path.exists(config_path):
        if os.path.exists(config_example_path):
            import shutil
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            shutil.copy(config_example_path, config_path)
            st.success("✅ 已自动创建配置文件")
        else:
            st.error("❌ 配置文件不存在，且未找到示例文件 config/config.example.json")
            return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        st.error(f"❌ 读取配置文件失败: {e}")
        return
    
    st.subheader("📊 基础筛选参数")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**AI内容占比阈值**")
        ai_ratio_percentage = st.slider("AI占比", min_value=0, max_value=100,
                                       value=int(config['crawler']['ai_ratio_threshold'] * 100),
                                       step=5, format="%d%%",
                                       help="只有AI内容占比超过此阈值的频道才会被标记为合格",
                                       label_visibility="collapsed")
        ai_ratio_threshold = ai_ratio_percentage / 100.0
    
    with col2:
        sample_video_count = st.number_input("每个频道分析视频数", min_value=5, max_value=50,
                                            value=config['crawler']['sample_video_count'], step=5,
                                            help="分析每个频道时抓取的视频数量，越多越准确但越慢")
    
    with col3:
        active_days_threshold = st.number_input("活跃度阈值(天)", min_value=30, max_value=365,
                                               value=config['crawler']['active_days_threshold'], step=30,
                                               help="最后一次发布视频距今的天数，超过此值视为不活跃")
    
    st.divider()
    
    st.subheader("🔑 AI关键词库")
    st.markdown("""
    **关键词匹配规则**：
    - ✅ **不区分大小写**：'AI' 和 'ai' 效果相同
    - ✅ **部分匹配**：'AI' 可以匹配 'AI video'、'using AI' 等
    - ✅ **双重检查**：同时检查视频标题和描述
    - ✅ **宽松匹配**：只要匹配任意一个关键词就判定为AI相关
    - ✅ **优先级说明**：高/中/低优先级仅用于组织管理，匹配权重相同
    """)
    
    tab1, tab2, tab3 = st.tabs(["🔥 高优先级", "⭐ 中优先级", "📌 低优先级"])
    
    with tab1:
        st.caption("💡 最新AI工具和热门话题（如：Sora, Kling, Runway等）")
        high_keywords = st.text_area("高优先级关键词（每行一个）",
                                    value="\n".join(config['keywords']['priority_high']),
                                    height=200, help="输入最新、最热门的AI工具名称")
        newline = '\n'
        st.caption(f"✅ 当前数量: {len([k for k in high_keywords.split(newline) if k.strip()])} 个")
    
    with tab2:
        st.caption("💡 主流AI工具和常见术语（如：ChatGPT, Midjourney, Claude等）")
        medium_keywords = st.text_area("中优先级关键词（每行一个）",
                                      value="\n".join(config['keywords']['priority_medium']),
                                      height=200, help="输入主流、常用的AI工具和术语")
        st.caption(f"✅ 当前数量: {len([k for k in medium_keywords.split(newline) if k.strip()])} 个")
    
    with tab3:
        st.caption("💡 技术术语和专业词汇（如：LLM, Diffusion Model, AI workflow等）")
        low_keywords = st.text_area("低优先级关键词（每行一个）",
                                   value="\n".join(config['keywords']['priority_low']),
                                   height=200, help="输入技术性较强的专业术语")
        st.caption(f"✅ 当前数量: {len([k for k in low_keywords.split(newline) if k.strip()])} 个")
    
    st.divider()
    
    st.subheader("🚫 排除规则")
    st.markdown("""
    **排除规则说明**：
    - ⚠️ **匹配方式**：频道名称或视频标题中包含这些关键词将被自动排除
    - 💡 **常见类型**：课程/教学（课、讲、课）、学术机构（大学、研究所）、新闻媒体（news、新闻）等
    - ✏️ **完全自定义**：你可以添加任何想要排除的关键词，不限于上述分类
    - 🎯 **目的**：过滤掉非目标KOL，聚焦于AI内容创作者
    """)
    
    all_exclusion_keywords = []
    all_exclusion_keywords.extend(config['exclusion_rules'].get('course_keywords', []))
    all_exclusion_keywords.extend(config['exclusion_rules'].get('academic_keywords', []))
    all_exclusion_keywords.extend(config['exclusion_rules'].get('news_keywords', []))
    
    exclusion_keywords = st.text_area("排除关键词（每行一个）", value="\n".join(all_exclusion_keywords),
                                     height=300, help="输入任何你想排除的关键词，如：课程、大学、新闻、tutorial、university等")
    
    keyword_count = len([k for k in exclusion_keywords.split(newline) if k.strip()])
    st.caption(f"✅ 当前共 {keyword_count} 个排除关键词")
    
    with st.expander("💡 常用排除关键词参考", expanded=False):
        st.markdown("""
        **课程/教学类**：课、讲、课、lesson、lecture、tutorial、教程、教学、系列课
        
        **学术机构类**：university、大学、college、学院、institute、研究所、实验室
        
        **新闻媒体类**：news、新闻、media、媒体、报导、报道、频道
        
        **其他类型**：你可以根据实际需求添加任何关键词
        """)
    
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            config['crawler']['ai_ratio_threshold'] = ai_ratio_threshold
            config['crawler']['sample_video_count'] = sample_video_count
            config['crawler']['active_days_threshold'] = active_days_threshold
            
            config['keywords']['priority_high'] = [k.strip() for k in high_keywords.split(newline) if k.strip()]
            config['keywords']['priority_medium'] = [k.strip() for k in medium_keywords.split(newline) if k.strip()]
            config['keywords']['priority_low'] = [k.strip() for k in low_keywords.split(newline) if k.strip()]
            
            exclusion_list = [k.strip() for k in exclusion_keywords.split(newline) if k.strip()]
            config['exclusion_rules']['course_keywords'] = exclusion_list
            config['exclusion_rules']['academic_keywords'] = []
            config['exclusion_rules']['news_keywords'] = []
            
            try:
                config_path = os.path.join(PROJECT_ROOT, 'config', 'config.json')
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                st.success("✅ 配置已保存！新配置将在下次爬虫任务时生效")
                add_log("AI规则配置已更新", "INFO")
            except Exception as e:
                st.error(f"❌ 保存失败: {e}")
    
    with col2:
        if st.button("🔄 重置为默认", use_container_width=True):
            st.warning("⚠️ 此操作将恢复默认配置，确定要继续吗？")
            if st.button("确认重置"):
                st.info("请手动编辑 config/config.json 文件恢复默认值")
    
    st.divider()
    st.subheader("📋 当前配置摘要")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    with summary_col1:
        st.metric("AI占比阈值", f"{ai_ratio_threshold*100:.0f}%")
        st.metric("分析视频数", f"{sample_video_count} 个")
    with summary_col2:
        total_keywords = len([k for k in high_keywords.split(newline) if k.strip()]) + \
                        len([k for k in medium_keywords.split(newline) if k.strip()]) + \
                        len([k for k in low_keywords.split(newline) if k.strip()])
        st.metric("总关键词数", f"{total_keywords} 个")
        st.metric("活跃度阈值", f"{active_days_threshold} 天")
    with summary_col3:
        total_exclusions = len([k for k in exclusion_keywords.split(newline) if k.strip()])
        st.metric("排除规则数", f"{total_exclusions} 个")

def render_settings():
    """渲染设置页面"""
    st.markdown('<div class="main-header">⚙️ 系统设置</div>', unsafe_allow_html=True)
    
    st.subheader("🗄️ 数据库配置")
    st.info("💡 当前使用SQLite数据库，数据保存在 data/ai_kol_crawler.db")
    
    config_path = os.path.join(PROJECT_ROOT, 'config', 'config.json')
    config_example_path = os.path.join(PROJECT_ROOT, 'config', 'config.example.json')
    
    if not os.path.exists(config_path):
        if os.path.exists(config_example_path):
            import shutil
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            shutil.copy(config_example_path, config_path)
            st.success("✅ 已自动创建配置文件")
        else:
            st.error("❌ 配置文件不存在，且未找到示例文件 config/config.example.json")
            return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        st.error(f"❌ 读取配置文件失败: {e}")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        db_host = st.text_input("数据库地址", value=config['database'].get('host', 'localhost'), disabled=True)
        db_port = st.number_input("端口", value=config['database'].get('port', 5432), disabled=True)
    with col2:
        db_name = st.text_input("数据库名", value=config['database'].get('database', 'ai_kol_crawler'), disabled=True)
        db_user = st.text_input("用户名", value=config['database'].get('user', 'postgres'), disabled=True)
    
    st.caption("💡 提示: SQLite数据库无需配置，如需使用PostgreSQL请修改 config/config.json")
    
    st.divider()
    
    st.subheader("📤 导出设置")
    col1, col2 = st.columns(2)
    with col1:
        output_dir = st.text_input("导出目录", value=config['export']['output_dir'])
    with col2:
        sort_by = st.selectbox("默认排序", ["ai_ratio", "subscribers", "avg_views"],
                              index=["ai_ratio", "subscribers", "avg_views"].index(config['export']['sort_by']))
    
    st.divider()
    
    st.subheader("🗂️ 数据库管理")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 查看数据库大小", use_container_width=True):
            db_path = 'data/ai_kol_crawler.db'
            if os.path.exists(db_path):
                size = os.path.getsize(db_path) / 1024 / 1024
                st.info(f"数据库大小: {size:.2f} MB")
            else:
                st.warning("数据库文件不存在")
    
    with col2:
        if st.button("💾 备份数据库", use_container_width=True):
            import shutil
            try:
                backup_dir = "backups"
                os.makedirs(backup_dir, exist_ok=True)
                backup_name = f"{backup_dir}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy('data/ai_kol_crawler.db', backup_name)
                st.success(f"✅ 备份成功: {backup_name}")
            except Exception as e:
                st.error(f"❌ 备份失败: {e}")
    
    with col3:
        if st.button("🗑️ 清空数据库", use_container_width=True):
            st.warning("⚠️ 此操作将删除所有数据，无法恢复！")
            confirm = st.checkbox("我确认要清空数据库")
            if confirm and st.button("确认清空"):
                try:
                    if st.session_state.db:
                        st.session_state.db.execute("DELETE FROM youtube_videos")
                        st.session_state.db.execute("DELETE FROM youtube_expansion_queue")
                        st.session_state.db.execute("DELETE FROM youtube_kols")
                        st.session_state.db.execute("DELETE FROM github_repositories")
                        st.session_state.db.execute("DELETE FROM github_developers")
                        st.success("✅ 数据库已清空")
                except Exception as e:
                    st.error(f"❌ 清空失败: {e}")
    
    st.divider()
    
    st.subheader("ℹ️ 系统信息")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**版本信息**")
        st.write("- 系统版本: v2.0 (多平台)")
        st.write("- 数据库: SQLite")
        st.write("- Python版本:", sys.version.split()[0])
    
    with col2:
        st.write("**统计信息**")
        youtube_stats = get_statistics('youtube')
        github_stats = get_statistics('github')
        st.write(f"- YouTube KOL数: {youtube_stats.get('qualified_kols', 0)}")
        st.write(f"- GitHub开发者数: {github_stats.get('qualified_developers', 0)}")
        st.write(f"- 总视频数: {youtube_stats.get('total_videos', 0)}")

if __name__ == "__main__":
    """主程序"""
    init_session_state()
    
    with st.sidebar:
        st.markdown("### 🤖 多平台爬虫")
        
        if connect_database():
            st.success("✅ 已连接")
        else:
            st.error("❌ 未连接")
        
        # 快速统计 - 更紧凑
        youtube_stats = get_statistics('youtube')
        github_stats = get_statistics('github')
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🎥 YT**")
            st.markdown(f"<div class='stat-number'>{youtube_stats.get('qualified_kols', 0)}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("**💻 GH**")
            st.markdown(f"<div class='stat-number'>{github_stats.get('qualified_developers', 0)}</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # 数据浏览（最前面）
        is_active = st.session_state.current_page == "data_browser"
        if st.button(
            "📊 数据浏览", 
            key="btn_data_browser", 
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.current_page = "data_browser"
            st.rerun()
        
        # YouTube分类
        st.markdown("### 🎥 YouTube")
        youtube_pages = {
            "youtube_dashboard": "📊 仪表盘",
            "youtube_crawler": "🚀 爬虫",
            "youtube_ai_rules": "🎯 规则"
        }
        
        for page_key, page_name in youtube_pages.items():
            is_active = st.session_state.current_page == page_key
            if st.button(
                page_name, 
                key=f"btn_{page_key}", 
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
        
        # GitHub分类
        st.markdown("### 💻 GitHub")
        github_pages = {
            "github_dashboard": "📊 仪表盘",
            "github_crawler": "🚀 爬虫"
        }
        
        for page_key, page_name in github_pages.items():
            is_active = st.session_state.current_page == page_key
            if st.button(
                page_name, 
                key=f"btn_{page_key}", 
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.divider()
        
        # 日志查看和设置（最后面）
        system_pages = {
            "logs": "📝 日志查看",
            "settings": "⚙️ 设置"
        }
        
        for page_key, page_name in system_pages.items():
            is_active = st.session_state.current_page == page_key
            if st.button(
                page_name, 
                key=f"btn_{page_key}", 
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.divider()
        
        if is_crawler_running():
            st.warning("⚙️ 爬虫运行中...")
        
        st.caption("多平台爬虫系统 v2.0")
        st.caption("© 2026 All Rights Reserved")
    
    # 处理跳转到日志
    if st.session_state.jump_to_logs:
        st.session_state.current_page = "logs"
        st.session_state.jump_to_logs = False
    
    # 主内容区
    page = st.session_state.current_page
    
    if page == "youtube_dashboard":
        render_youtube_dashboard()
    elif page == "youtube_crawler":
        render_youtube_crawler()
    elif page == "youtube_ai_rules":
        render_ai_rules()
    elif page == "github_dashboard":
        render_github_dashboard()
    elif page == "github_crawler":
        render_github_crawler()
    elif page == "data_browser":
        render_data_browser()
    elif page == "logs":
        render_logs()
    elif page == "settings":
        render_settings()
    else:
        render_youtube_dashboard()
