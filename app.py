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
    from datetime import datetime, timedelta, timezone
    # 使用北京时间
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
    timestamp = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    log_queue.put(log_entry)
    log_list.append(log_entry)
    if len(log_list) > 1000:
        log_list.pop(0)
    
    # 写入文件
    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/{beijing_time.strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except:
        pass

def set_crawler_running(status):
    """设置爬虫运行状态"""
    try:
        status_dir = os.path.dirname(CRAWLER_STATUS_FILE)
        os.makedirs(status_dir, exist_ok=True)
        
        # 写入状态
        status_text = "running" if status else "stopped"
        with open(CRAWLER_STATUS_FILE, 'w', encoding='utf-8') as f:
            f.write(status_text)
        
        # 强制刷新到磁盘
        if hasattr(os, 'sync'):
            os.sync()
        
        # 验证写入
        with open(CRAWLER_STATUS_FILE, 'r', encoding='utf-8') as f:
            written_status = f.read().strip()
            if written_status != status_text:
                raise Exception(f"状态写入验证失败: 期望 {status_text}, 实际 {written_status}")
        
        add_log(f"爬虫状态已更新: {status_text}", "INFO")
        return True
    except Exception as e:
        add_log(f"设置爬虫状态失败: {str(e)}", "ERROR")
        return False

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

def check_and_fix_crawler_status():
    """检查并修复爬虫状态（如果线程已结束但状态还是运行中）"""
    try:
        if not is_crawler_running():
            return True
        
        # 检查是否有活跃的爬虫线程
        import threading
        active_threads = threading.enumerate()
        crawler_thread_exists = any(
            'run_youtube_crawler_task' in str(t.name) or 
            'run_github_crawler_task' in str(t.name) or
            t.name.startswith('Thread-') and t.is_alive()
            for t in active_threads
        )
        
        # 如果状态是运行中，但没有活跃的爬虫线程，自动修复
        if not crawler_thread_exists:
            add_log("检测到爬虫状态异常（无活跃线程但状态为运行中），自动修复", "WARNING")
            set_crawler_running(False)
            return True
        
        return False
    except Exception as e:
        add_log(f"检查爬虫状态时出错: {str(e)}", "ERROR")
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
    from datetime import datetime, timedelta, timezone
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
    log_file = os.path.join(LOG_DIR, f"{beijing_time.strftime('%Y%m%d')}.log")
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
    task = None
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
        add_log("正在更新爬虫状态...", "INFO")
        
    except KeyboardInterrupt:
        add_log("任务被用户中断", "WARNING")
    except Exception as e:
        add_log(f"任务执行失败: {str(e)}", "ERROR")
        add_log(traceback.format_exc(), "ERROR")
    finally:
        # 确保状态一定会被更新
        try:
            add_log("任务结束，正在停止爬虫...", "INFO")
            success = set_crawler_running(False)
            if success:
                add_log("爬虫已停止", "SUCCESS")
            else:
                add_log("警告：爬虫状态更新可能失败，请手动点击「标记为已完成」", "WARNING")
        except Exception as e:
            add_log(f"停止爬虫时出错: {str(e)}", "ERROR")
            # 强制写入
            try:
                with open(CRAWLER_STATUS_FILE, 'w', encoding='utf-8') as f:
                    f.write("stopped")
            except:
                pass

def run_github_crawler_task(task_type, repository, **kwargs):
    """运行GitHub爬虫任务"""
    task = None
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
        add_log("正在更新爬虫状态...", "INFO")
        
    except KeyboardInterrupt:
        add_log("任务被用户中断", "WARNING")
    except Exception as e:
        add_log(f"GitHub任务执行失败: {str(e)}", "ERROR")
        add_log(traceback.format_exc(), "ERROR")
    finally:
        # 确保状态一定会被更新
        try:
            add_log("任务结束，正在停止爬虫...", "INFO")
            success = set_crawler_running(False)
            if success:
                add_log("爬虫已停止", "SUCCESS")
            else:
                add_log("警告：爬虫状态更新可能失败，请手动点击「标记为已完成」", "WARNING")
        except Exception as e:
            add_log(f"停止爬虫时出错: {str(e)}", "ERROR")
            # 强制写入
            try:
                with open(CRAWLER_STATUS_FILE, 'w', encoding='utf-8') as f:
                    f.write("stopped")
            except:
                pass



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
    
    # 检查并修复状态
    check_and_fix_crawler_status()
    
    running = is_crawler_running()
    if running:
        st.warning("⚠️ 爬虫正在运行中，请等待任务完成...")
        st.info("💡 切换到「📝 日志查看」页面查看实时进度")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏹️ 标记为已完成", key="mark_complete", use_container_width=True):
                success = set_crawler_running(False)
                if success:
                    st.success("✅ 状态已重置")
                    time.sleep(0.5)
                else:
                    st.error("❌ 状态重置失败")
                st.rerun()
        
        with col2:
            if st.button("🔄 强制重置状态", key="force_reset", use_container_width=True):
                try:
                    # 强制写入
                    with open(CRAWLER_STATUS_FILE, 'w', encoding='utf-8') as f:
                        f.write("stopped")
                    st.success("✅ 已强制重置")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 强制重置失败: {e}")
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
    from ui.github import render_crawler
    render_crawler(
        is_crawler_running_func=is_crawler_running,
        check_and_fix_status_func=check_and_fix_crawler_status,
        set_crawler_running_func=set_crawler_running,
        clear_logs_func=clear_logs,
        add_log_func=add_log,
        run_crawler_task_func=run_github_crawler_task,
        session_state=st.session_state,
        crawler_status_file=CRAWLER_STATUS_FILE,
        time_module=time,
        threading_module=threading
    )

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
        
        # 时间格式化（数据库已存储北京时间，直接显示）
        def format_time(dt):
            if pd.isna(dt):
                return ""
            if isinstance(dt, str):
                try:
                    dt = pd.to_datetime(dt)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    return dt
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        display_df['爬取时间'] = display_df['爬取时间'].apply(format_time)
        
        table_height = min(max(len(display_df) * 35 + 50, 200), 800)
        st.dataframe(display_df, width='stretch', hide_index=True, height=table_height,
                    column_config={"频道链接": st.column_config.LinkColumn("频道链接", help="点击打开YouTube频道")})
        
        st.divider()
        
        # 导出按钮区域
        col1, col2 = st.columns(2)
        
        with col1:
            # 导出所有数据
            if st.button("📥 导出所有数据", key="export_yt_all_data", use_container_width=True):
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
                            key="download_yt_all_excel_file"
                        )
                        add_log(f"导出Excel成功: {filepath}", "SUCCESS")
                except Exception as e:
                    st.error(f"❌ 导出失败: {str(e)}")
                    add_log(f"导出Excel失败: {str(e)}", "ERROR")
        
        with col2:
            # 导出今日数据
            from datetime import datetime, timedelta, timezone
            beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
            today_str = beijing_time.strftime('%Y-%m-%d')
            
            if st.button(f"📅 导出今日数据 ({today_str})", key="export_yt_today_data", use_container_width=True):
                try:
                    from tasks.youtube.export import YouTubeExportTask
                    export_task = YouTubeExportTask(st.session_state.youtube_repository)
                    
                    # 计算今天的时间范围
                    today_start = beijing_time.replace(hour=0, minute=0, second=0, microsecond=0)
                    today_end = beijing_time.replace(hour=23, minute=59, second=59, microsecond=0)
                    
                    # 导出今日数据
                    filepath = export_task.run_today(today_start, today_end)
                    if filepath and os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            excel_data = f.read()
                        st.download_button(
                            label="💾 下载今日Excel文件",
                            data=excel_data,
                            file_name=os.path.basename(filepath),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="download_yt_today_excel_file"
                        )
                        add_log(f"导出今日Excel成功: {filepath}", "SUCCESS")
                    else:
                        st.warning("今天暂无数据")
                except Exception as e:
                    st.error(f"❌ 导出失败: {str(e)}")
                    add_log(f"导出今日Excel失败: {str(e)}", "ERROR")
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
        
        # 时间格式化（数据库已存储北京时间，直接显示）
        def format_time(dt):
            if pd.isna(dt):
                return ""
            if isinstance(dt, str):
                try:
                    dt = pd.to_datetime(dt)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    return dt
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        display_df['爬取时间'] = display_df['爬取时间'].apply(format_time)
        
        table_height = min(max(len(display_df) * 35 + 50, 200), 800)
        st.dataframe(display_df, width='stretch', hide_index=True, height=table_height,
                    column_config={"主页链接": st.column_config.LinkColumn("主页链接", help="点击打开GitHub主页")})
        
        st.divider()
        
        # 导出按钮区域
        col1, col2 = st.columns(2)
        
        with col1:
            # 导出所有数据
            if st.button("📥 导出所有数据", key="export_gh_all_data", use_container_width=True):
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
                            key="download_gh_all_excel_file"
                        )
                        add_log(f"导出Excel成功: {filepath}", "SUCCESS")
                except Exception as e:
                    st.error(f"❌ 导出失败: {str(e)}")
                    add_log(f"导出Excel失败: {str(e)}", "ERROR")
        
        with col2:
            # 导出今日数据
            from datetime import datetime, timedelta, timezone
            beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
            today_str = beijing_time.strftime('%Y-%m-%d')
            
            if st.button(f"📅 导出今日数据 ({today_str})", key="export_gh_today_data", use_container_width=True):
                try:
                    from tasks.github.export import GitHubExportTask
                    export_task = GitHubExportTask(st.session_state.github_repository)
                    
                    # 计算今天的时间范围
                    today_start = beijing_time.replace(hour=0, minute=0, second=0, microsecond=0)
                    today_end = beijing_time.replace(hour=23, minute=59, second=59, microsecond=0)
                    
                    # 导出今日数据
                    filepath = export_task.run_today(today_start, today_end)
                    if filepath and os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            excel_data = f.read()
                        st.download_button(
                            label="💾 下载今日Excel文件",
                            data=excel_data,
                            file_name=os.path.basename(filepath),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="download_gh_today_excel_file"
                        )
                        add_log(f"导出今日Excel成功: {filepath}", "SUCCESS")
                    else:
                        st.warning("今天暂无数据")
                except Exception as e:
                    st.error(f"❌ 导出失败: {str(e)}")
                    add_log(f"导出今日Excel失败: {str(e)}", "ERROR")
    else:
        st.info("📭 暂无数据")

def render_logs():
    """渲染日志查看页面"""
    st.markdown('<div class="main-header">📝 实时日志</div>', unsafe_allow_html=True)
    
    # 检查并修复状态
    check_and_fix_crawler_status()
    
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
    
    # 使用北京时间获取日志文件
    from datetime import datetime, timedelta, timezone
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
    log_file = os.path.join(LOG_DIR, f"{beijing_time.strftime('%Y%m%d')}.log")
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
    from ui.youtube import render_rules
    render_rules(PROJECT_ROOT, add_log)

def render_github_rules():
    """渲染GitHub规则配置页面"""
    from ui.github import render_rules
    render_rules(PROJECT_ROOT, add_log)

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
            from datetime import datetime, timedelta, timezone
            try:
                backup_dir = "backups"
                os.makedirs(backup_dir, exist_ok=True)
                beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
                backup_name = f"{backup_dir}/backup_{beijing_time.strftime('%Y%m%d_%H%M%S')}.db"
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
