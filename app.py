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

# 加载自定义CSS
def load_css():
    css_file = os.path.join(PROJECT_ROOT, "static", "style.css")
    if os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning("CSS文件未找到")

load_css()

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
    st.markdown('<div class="main-header">📊 YouTube 数据概览</div>', unsafe_allow_html=True)
    
    stats = get_statistics('youtube')
    
    # 第一行：主要指标（大卡片）
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">总KOL数</div>
            <div class="metric-value">{stats.get('total_kols', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="big-metric-card highlight">
            <div class="metric-label">合格KOL</div>
            <div class="metric-value">{stats.get('qualified_kols', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">待分析</div>
            <div class="metric-value">{stats.get('pending_kols', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 第二行：次要指标（中等卡片）
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">总视频数</div>
            <div class="metric-value-medium">{stats.get('total_videos', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">待扩散队列</div>
            <div class="metric-value-medium">{stats.get('pending_expansions', 0)}</div>
        </div>
        """, unsafe_allow_html=True)

def render_github_dashboard():
    """渲染GitHub仪表盘"""
    st.markdown('<div class="main-header">📊 GitHub 数据概览</div>', unsafe_allow_html=True)
    
    stats = get_statistics('github')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">总开发者数</div>
            <div class="metric-value">{stats.get('total_developers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="big-metric-card highlight">
            <div class="metric-label">合格开发者</div>
            <div class="metric-value">{stats.get('qualified_developers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">待分析</div>
            <div class="metric-value">{stats.get('pending_developers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">总仓库数</div>
            <div class="metric-value-medium">{stats.get('total_repositories', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        qualified = stats.get('qualified_developers', 0)
        total = max(stats.get('total_developers', 1), 1)
        rate = (qualified / total * 100)
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">合格率</div>
            <div class="metric-value-medium">{rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        repos = stats.get('total_repositories', 0)
        devs = max(stats.get('total_developers', 1), 1)
        avg = repos / devs
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">平均仓库数</div>
            <div class="metric-value-medium">{avg:.1f}</div>
        </div>
        """, unsafe_allow_html=True)

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
        sort_by = st.selectbox("排序方式", ["爬取时间", "AI占比", "订阅数", "平均观看"], index=0, key="yt_sort")
    with col3:
        limit = st.number_input("显示数量", min_value=10, max_value=1000, value=50, step=10, key="yt_limit")
    
    status_map = {"全部": None, "合格": "qualified", "待分析": "pending", "已拒绝": "rejected"}
    sort_map = {"爬取时间": "discovered_at DESC", "AI占比": "ai_ratio DESC", "订阅数": "subscribers DESC", "平均观看": "avg_views DESC"}
    
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
        
        # 导出按钮 - 合并为一个
        if st.button("📥 导出数据", key="export_yt_data", use_container_width=True):
            try:
                from tasks.youtube.export import YouTubeExportTask
                export_task = YouTubeExportTask(st.session_state.youtube_repository)
                filepath = export_task.run()
                if filepath and os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        excel_data = f.read()
                    st.download_button(
                        label="💾 下载Excel文件",
                        data=excel_data,
                        file_name=os.path.basename(filepath),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_yt_excel_file"
                    )
                    add_log(f"导出Excel成功: {filepath}", "SUCCESS")
            except Exception as e:
                st.error(f"❌ 导出失败: {str(e)}")
                add_log(f"导出Excel失败: {str(e)}", "ERROR")
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
        sort_by = st.selectbox("排序方式", ["爬取时间", "总Stars", "Followers", "仓库数"], index=0, key="gh_sort")
    with col3:
        limit = st.number_input("显示数量", min_value=10, max_value=1000, value=50, step=10, key="gh_limit")
    
    status_map = {"全部": None, "合格": "qualified", "待分析": "pending", "已拒绝": "rejected"}
    sort_map = {"爬取时间": "discovered_at DESC", "总Stars": "total_stars DESC", "Followers": "followers DESC", "仓库数": "public_repos DESC"}
    
    query = "SELECT * FROM github_developers"
    if status_filter != "全部":
        query += f" WHERE status = '{status_map[status_filter]}'"
    query += f" ORDER BY {sort_map[sort_by]} LIMIT {limit}"
    
    devs = st.session_state.db.fetchall(query)
    
    if devs:
        df = pd.DataFrame(devs)
        display_columns = ['username', 'name', 'profile_url', 'followers', 'public_repos', 'total_stars', 'contact_info', 'status', 'discovered_at']
        display_df = df[display_columns].copy()
        display_df.columns = ['用户名', '姓名', '主页链接', 'Followers', '仓库数', '总Stars', '联系方式', '状态', '爬取时间']
        
        display_df['Followers'] = display_df['Followers'].apply(lambda x: f"{x:,}")
        display_df['仓库数'] = display_df['仓库数'].apply(lambda x: f"{x:,}")
        display_df['总Stars'] = display_df['总Stars'].apply(lambda x: f"{x:,}")
        display_df['联系方式'] = display_df['联系方式'].fillna('')
        
        table_height = min(max(len(display_df) * 35 + 50, 200), 800)
        st.dataframe(display_df, width='stretch', hide_index=True, height=table_height,
                    column_config={"主页链接": st.column_config.LinkColumn("主页链接", help="点击打开GitHub主页")})
        
        st.divider()
        
        # 导出按钮 - 合并为一个
        if st.button("📥 导出数据", key="export_gh_data", use_container_width=True):
            try:
                from tasks.github.export import GitHubExportTask
                export_task = GitHubExportTask(st.session_state.github_repository)
                filepath = export_task.run()
                if filepath and os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        excel_data = f.read()
                    st.download_button(
                        label="💾 下载Excel文件",
                        data=excel_data,
                        file_name=os.path.basename(filepath),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_gh_excel_file"
                    )
                    add_log(f"导出Excel成功: {filepath}", "SUCCESS")
            except Exception as e:
                st.error(f"❌ 导出失败: {str(e)}")
                add_log(f"导出Excel失败: {str(e)}", "ERROR")
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
    """渲染YouTube AI规则配置页面"""
    st.markdown('<div class="main-header">🎯 YouTube AI过滤规则</div>', unsafe_allow_html=True)
    
    st.info("💡 配置AI内容识别规则，调整关键词和筛选条件")
    
    config_path = os.path.join(PROJECT_ROOT, 'config', 'config.json')
    config_example_path = os.path.join(PROJECT_ROOT, 'config', 'config.example.json')
    
    if not os.path.exists(config_path):
        if os.path.exists(config_example_path):
            import shutil
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            shutil.copy(config_example_path, config_path)
            st.success("✅ 已自动创建配置文件")
        else:
            st.error("❌ 配置文件不存在")
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
        ai_ratio_percentage = st.slider("AI占比阈值", min_value=0, max_value=100,
                                       value=int(config['crawler']['ai_ratio_threshold'] * 100),
                                       step=5, format="%d%%")
        ai_ratio_threshold = ai_ratio_percentage / 100.0
    
    with col2:
        sample_video_count = st.number_input("分析视频数", min_value=5, max_value=50,
                                            value=config['crawler']['sample_video_count'], step=5)
    
    with col3:
        active_days_threshold = st.number_input("活跃度阈值(天)", min_value=30, max_value=365,
                                               value=config['crawler']['active_days_threshold'], step=30)
    
    st.divider()
    
    st.subheader("🔑 AI关键词库")
    tab1, tab2, tab3 = st.tabs(["🔥 高优先级", "⭐ 中优先级", "📌 低优先级"])
    
    with tab1:
        high_keywords = st.text_area("高优先级关键词（每行一个）",
                                    value="\n".join(config['keywords']['priority_high']),
                                    height=200)
    
    with tab2:
        medium_keywords = st.text_area("中优先级关键词（每行一个）",
                                      value="\n".join(config['keywords']['priority_medium']),
                                      height=200)
    
    with tab3:
        low_keywords = st.text_area("低优先级关键词（每行一个）",
                                   value="\n".join(config['keywords']['priority_low']),
                                   height=200)
    
    st.divider()
    
    st.subheader("🚫 排除规则")
    all_exclusion_keywords = []
    all_exclusion_keywords.extend(config['exclusion_rules'].get('course_keywords', []))
    all_exclusion_keywords.extend(config['exclusion_rules'].get('academic_keywords', []))
    all_exclusion_keywords.extend(config['exclusion_rules'].get('news_keywords', []))
    
    exclusion_keywords = st.text_area("排除关键词（每行一个）", value="\n".join(all_exclusion_keywords),
                                     height=200)
    
    if st.button("💾 保存配置", type="primary", use_container_width=True):
        config['crawler']['ai_ratio_threshold'] = ai_ratio_threshold
        config['crawler']['sample_video_count'] = sample_video_count
        config['crawler']['active_days_threshold'] = active_days_threshold
        
        config['keywords']['priority_high'] = [k.strip() for k in high_keywords.split('\n') if k.strip()]
        config['keywords']['priority_medium'] = [k.strip() for k in medium_keywords.split('\n') if k.strip()]
        config['keywords']['priority_low'] = [k.strip() for k in low_keywords.split('\n') if k.strip()]
        
        exclusion_list = [k.strip() for k in exclusion_keywords.split('\n') if k.strip()]
        config['exclusion_rules']['course_keywords'] = exclusion_list
        config['exclusion_rules']['academic_keywords'] = []
        config['exclusion_rules']['news_keywords'] = []
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            st.success("✅ 配置已保存！")
            add_log("YouTube AI规则配置已更新", "INFO")
        except Exception as e:
            st.error(f"❌ 保存失败: {e}")

def render_github_rules():
    """渲染GitHub规则配置页面"""
    st.markdown('<div class="main-header">🎯 GitHub 筛选规则</div>', unsafe_allow_html=True)
    
    st.info("💡 配置GitHub独立开发者筛选规则")
    
    config_path = os.path.join(PROJECT_ROOT, 'config', 'config.json')
    
    if not os.path.exists(config_path):
        st.error("❌ 配置文件不存在")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        st.error(f"❌ 读取配置文件失败: {e}")
        return
    
    # 如果配置中没有github部分，创建默认配置
    if 'github' not in config:
        config['github'] = {
            'min_followers': 100,
            'min_stars': 500,
            'min_repos': 3,
            'keywords': ['AI', 'machine learning', 'deep learning', 'stable diffusion', 'LLM', 'GPT'],
            'exclusion_companies': [
                'Google', 'Microsoft', 'Meta', 'Facebook', 'Amazon', 'Apple',
                'Alibaba', 'Tencent', 'ByteDance', 'Baidu', 'Huawei', 'OpenAI',
                'Stability AI', 'Midjourney', 'Runway', 'Anthropic', 'Cohere',
                'AWS', 'Azure', 'GCP', 'Cloudflare', 'Vercel'
            ],
            'exclusion_projects': ['ComfyUI', 'Automatic1111', 'Stable Diffusion WebUI', 'LangChain']
        }
    
    st.subheader("📊 独立开发者判断标准")
    
    with st.expander("ℹ️ 什么是独立开发者？", expanded=True):
        st.markdown("""
        **独立开发者必须同时满足以下条件：**
        
        1. **不属于大公司** - 不在Google、Microsoft、Meta等大公司工作
        2. **不是项目成员** - 不是ComfyUI、Automatic1111等知名项目的团队成员
        3. **有原创项目** - 至少有3个非fork的原创仓库
        4. **有影响力** - Followers ≥ 100 或 总Stars ≥ 500
        5. **有AI项目** - 至少有1个AI相关的原创项目
        6. **主要是创作者** - fork项目的stars占比不超过70%（避免纯贡献者）
        
        **排除规则：**
        - Bio或Company中标注为某项目成员（如"ComfyUI team member"）
        - 主要贡献集中在fork的项目上
        """)
    
    st.divider()
    
    st.subheader("🎯 筛选参数")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_followers = st.number_input(
            "最小Followers数", 
            min_value=0, max_value=10000,
            value=config['github'].get('min_followers', 100), 
            step=50,
            help="开发者的最小粉丝数量"
        )
    
    with col2:
        min_stars = st.number_input(
            "最小总Stars数", 
            min_value=0, max_value=50000,
            value=config['github'].get('min_stars', 500), 
            step=100,
            help="所有原创仓库的总stars数"
        )
    
    with col3:
        min_repos = st.number_input(
            "最小原创仓库数", 
            min_value=1, max_value=100,
            value=config['github'].get('min_repos', 3), 
            step=1,
            help="非fork的原创仓库数量"
        )
    
    st.divider()
    
    st.subheader("🔑 AI相关关键词")
    st.caption("用于搜索和识别AI相关项目的关键词")
    
    github_keywords = st.text_area(
        "关键词（每行一个）",
        value="\n".join(config['github'].get('keywords', [])),
        height=150,
        help="这些关键词用于搜索GitHub仓库和判断项目是否与AI相关"
    )
    
    st.divider()
    
    st.subheader("🏢 排除的公司/组织")
    st.caption("在这些公司工作的开发者将被排除")
    
    exclusion_companies = st.text_area(
        "公司名称（每行一个）",
        value="\n".join(config['github'].get('exclusion_companies', [])),
        height=200,
        help="Company字段包含这些名称的开发者将被过滤"
    )
    
    st.divider()
    
    st.subheader("🚫 排除的项目团队")
    st.caption("这些项目的团队成员将被排除")
    
    exclusion_projects = st.text_area(
        "项目名称（每行一个）",
        value="\n".join(config['github'].get('exclusion_projects', [])),
        height=150,
        help="Bio或Company中标注为这些项目成员的开发者将被过滤"
    )
    
    st.divider()
    
    if st.button("💾 保存配置", type="primary", use_container_width=True):
        config['github']['min_followers'] = min_followers
        config['github']['min_stars'] = min_stars
        config['github']['min_repos'] = min_repos
        config['github']['keywords'] = [k.strip() for k in github_keywords.split('\n') if k.strip()]
        config['github']['exclusion_companies'] = [k.strip() for k in exclusion_companies.split('\n') if k.strip()]
        config['github']['exclusion_projects'] = [k.strip() for k in exclusion_projects.split('\n') if k.strip()]
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            st.success("✅ 配置已保存！新配置将在下次爬虫任务时生效")
            add_log("GitHub筛选规则配置已更新", "INFO")
        except Exception as e:
            st.error(f"❌ 保存失败: {e}")

def render_settings():
    """渲染设置页面"""
    st.markdown('<div class="main-header">⚙️ 系统设置</div>', unsafe_allow_html=True)
    
    st.subheader("🗄️ 数据库信息")
    st.info("💡 当前使用SQLite数据库，数据保存在 data/ai_kol_crawler.db")
    
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
    
    st.divider()
    
    st.subheader("ℹ️ 系统信息")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**版本信息**")
        st.write("- 系统版本: v2.0")
        st.write("- 数据库: SQLite")
        st.write("- Python:", sys.version.split()[0])
    
    with col2:
        st.write("**统计信息**")
        youtube_stats = get_statistics('youtube')
        github_stats = get_statistics('github')
        st.write(f"- YouTube KOL: {youtube_stats.get('qualified_kols', 0)}")
        st.write(f"- GitHub开发者: {github_stats.get('qualified_developers', 0)}")


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
            st.markdown("**🎥 YouTube**")
            st.markdown(f"<div class='stat-number'>{youtube_stats.get('qualified_kols', 0)}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("**💻 GitHub**")
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
            "github_crawler": "🚀 爬虫",
            "github_rules": "🎯 规则"
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
    elif page == "github_rules":
        render_github_rules()
    elif page == "data_browser":
        render_data_browser()
    elif page == "logs":
        render_logs()
    elif page == "settings":
        render_settings()
    else:
        render_youtube_dashboard()
