# -*- coding: utf-8 -*-
"""
AI KOL爬虫系统 - Streamlit可视化界面
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

# 确保工作目录是项目根目录
os.chdir(PROJECT_ROOT)

# 状态文件和日志目录路径
CRAWLER_STATUS_FILE = os.path.join(PROJECT_ROOT, "data", "crawler_status.txt")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# 延迟导入，避免启动时出错
def lazy_import():
    """延迟导入模块"""
    try:
        from storage.database import Database
        from storage.kol_repository import KOLRepository
        from core.scraper import YouTubeScraper
        from core.searcher import KeywordSearcher
        from core.analyzer import KOLAnalyzer
        from core.expander import KOLExpander
        from core.filter import KOLFilter
        from tasks.discovery_task import DiscoveryTask
        from tasks.expand_task import ExpandTask
        from tasks.export_task import ExportTask
        return True
    except Exception as e:
        st.error(f"模块导入失败: {str(e)}")
        st.error(traceback.format_exc())
        return False


# 页面配置
st.set_page_config(
    page_title="AI KOL爬虫系统",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #155a8a;
    }
</style>
""", unsafe_allow_html=True)


# 全局日志队列（线程安全）
log_queue = queue.Queue()
log_list = []

def set_crawler_running(status):
    """设置爬虫运行状态（使用文件标记）"""
    try:
        status_dir = os.path.dirname(CRAWLER_STATUS_FILE)
        os.makedirs(status_dir, exist_ok=True)
        with open(CRAWLER_STATUS_FILE, 'w', encoding='utf-8') as f:
            f.write("running" if status else "stopped")
    except Exception as e:
        pass

def is_crawler_running():
    """获取爬虫运行状态（从文件读取）"""
    try:
        if os.path.exists(CRAWLER_STATUS_FILE):
            with open(CRAWLER_STATUS_FILE, 'r', encoding='utf-8') as f:
                status = f.read().strip()
                return status == "running"
    except Exception as e:
        pass
    return False

# 初始化Session State
def init_session_state():
    """初始化会话状态"""
    if 'db' not in st.session_state:
        st.session_state.db = None
    if 'repository' not in st.session_state:
        st.session_state.repository = None


def connect_database():
    """连接数据库"""
    try:
        if st.session_state.db is None:
            from storage.database import Database
            from storage.kol_repository import KOLRepository
            
            # 默认使用SQLite（无需Docker）
            db = Database(use_sqlite=True)
            db.connect()
            db.init_tables()
            st.session_state.db = db
            st.session_state.repository = KOLRepository(db)
            return True
    except Exception as e:
        st.error(f"数据库连接失败: {str(e)}")
        st.info("💡 提示: 程序使用SQLite数据库，数据保存在 data/ai_kol_crawler.db")
        return False
    return True


def get_statistics():
    """获取统计数据"""
    if st.session_state.repository:
        try:
            return st.session_state.repository.get_statistics()
        except Exception as e:
            add_log(f"获取统计数据失败: {e}", "ERROR")
            return {
                'total_kols': 0,
                'qualified_kols': 0,
                'pending_kols': 0,
                'total_videos': 0,
                'pending_expansions': 0
            }
    return {
        'total_kols': 0,
        'qualified_kols': 0,
        'pending_kols': 0,
        'total_videos': 0,
        'pending_expansions': 0
    }


def add_log(message, level="INFO"):
    """添加日志（线程安全）- 同时写入内存和文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # 添加到内存队列
    log_queue.put(log_entry)
    log_list.append(log_entry)
    
    # 只保留最近1000条日志
    if len(log_list) > 1000:
        log_list.pop(0)
    
    # 同时写入日志文件
    try:
        import os
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = f"{log_dir}/{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except Exception as e:
        # 写入文件失败不影响程序运行
        pass


def run_crawler_task(task_type, repository, **kwargs):
    """在后台线程运行爬虫任务"""
    try:
        from core.scraper import YouTubeScraper
        from core.searcher import KeywordSearcher
        from core.analyzer import KOLAnalyzer
        from core.expander import KOLExpander
        from core.filter import KOLFilter
        from tasks.discovery_task import DiscoveryTask
        from tasks.expand_task import ExpandTask
        
        set_crawler_running(True)
        add_log(f"开始执行任务: {task_type}", "INFO")
        
        # 初始化组件
        scraper = YouTubeScraper()
        searcher = KeywordSearcher(scraper)
        analyzer = KOLAnalyzer(scraper)
        expander = KOLExpander(scraper)
        filter_obj = KOLFilter(repository)
        
        if task_type == "discovery":
            task = DiscoveryTask(searcher, analyzer, filter_obj, repository)
            keyword_limit = kwargs.get('keyword_limit', 30)
            add_log(f"使用 {keyword_limit} 个关键词进行搜索", "INFO")
            task.run(keyword_limit)
            
        elif task_type == "expand":
            task = ExpandTask(expander, analyzer, filter_obj, repository)
            add_log("开始扩散任务", "INFO")
            task.run()
            
        add_log(f"任务完成: {task_type}", "SUCCESS")
        
    except Exception as e:
        add_log(f"任务执行失败: {str(e)}", "ERROR")
        import traceback
        add_log(traceback.format_exc(), "ERROR")
    finally:
        set_crawler_running(False)


# ==================== 页面组件 ====================

def render_dashboard():
    """渲染仪表盘页面"""
    st.markdown('<div class="main-header">📊 数据仪表盘</div>', unsafe_allow_html=True)
    
    # 获取统计数据
    stats = get_statistics()
    
    # 显示关键指标
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="总KOL数",
            value=stats['total_kols'],
            delta=None
        )
    
    with col2:
        st.metric(
            label="合格KOL",
            value=stats['qualified_kols'],
            delta=None
        )
    
    with col3:
        st.metric(
            label="待分析",
            value=stats['pending_kols'],
            delta=None
        )
    
    with col4:
        st.metric(
            label="总视频数",
            value=stats['total_videos'],
            delta=None
        )
    
    with col5:
        st.metric(
            label="待扩散",
            value=stats['pending_expansions'],
            delta=None
        )
    
    st.divider()
    
    # 显示最近发现的KOL
    st.subheader("🌟 最近发现的合格KOL")
    
    if st.session_state.repository:
        recent_kols = st.session_state.repository.get_qualified_kols(limit=10)
        
        if recent_kols:
            df = pd.DataFrame(recent_kols)
            display_df = df[[
                'channel_name', 'subscribers', 'ai_ratio', 
                'avg_views', 'engagement_rate', 'discovered_at'
            ]].copy()
            
            display_df.columns = ['频道名称', '订阅数', 'AI占比', '平均观看', '互动率', '发现时间']
            display_df['AI占比'] = display_df['AI占比'].apply(lambda x: f"{x*100:.1f}%")
            display_df['互动率'] = display_df['互动率'].apply(lambda x: f"{x:.2f}%")
            display_df['订阅数'] = display_df['订阅数'].apply(lambda x: f"{x:,}")
            display_df['平均观看'] = display_df['平均观看'].apply(lambda x: f"{x:,}")
            
            st.dataframe(display_df, width='stretch', hide_index=True)
        else:
            st.info("暂无数据，请先运行爬虫任务")
    
    # 刷新按钮
    if st.button("🔄 刷新数据", key="refresh_dashboard"):
        st.rerun()


def render_crawler_control():
    """渲染爬虫控制页面"""
    st.markdown('<div class="main-header">🚀 爬虫控制中心</div>', unsafe_allow_html=True)
    
    # 显示运行状态
    running = is_crawler_running()
    if running:
        st.warning("⚠️ 爬虫正在运行中，请等待任务完成...")
        st.info("💡 切换到「📝 日志查看」页面查看实时进度")
        
        # 添加停止按钮
        if st.button("⏹️ 标记为已完成", key="mark_complete"):
            set_crawler_running(False)
            st.rerun()
    else:
        st.success("✅ 爬虫空闲，可以启动新任务")
    
    st.divider()
    
    # 任务选择
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
        
        st.info(f"预计搜索 {keyword_limit * 5} 个视频，耗时约 {keyword_limit * 2} 分钟")
        
        if st.button(
            "▶️ 开始初始发现",
            disabled=running,
            key="start_discovery"
        ):
            if not st.session_state.repository:
                st.error("数据库未连接，无法启动任务")
            else:
                # 完全清空日志（内存和文件）
                clear_logs()
                
                # 添加新任务的开始日志
                add_log("=" * 60, "INFO")
                add_log("开始新的爬虫任务 - 初始发现", "INFO")
                add_log("=" * 60, "INFO")
                add_log(f"用户启动初始发现任务，关键词数量: {keyword_limit}", "INFO")
                
                thread = threading.Thread(
                    target=run_crawler_task,
                    args=("discovery", st.session_state.repository),
                    kwargs={'keyword_limit': keyword_limit}
                )
                thread.daemon = True
                thread.start()
                set_crawler_running(True)
                
                # 设置跳转标记
                st.session_state.jump_to_logs = True
                st.session_state.auto_refresh_enabled = True  # 确保自动刷新开启
                time.sleep(0.5)
                st.rerun()
    
    with col2:
        st.subheader("🌐 扩散发现任务")
        st.write("从已有KOL的推荐列表中发现新KOL")
        
        stats = get_statistics()
        st.info(f"当前待扩散队列: {stats['pending_expansions']} 个KOL")
        
        if stats['pending_expansions'] == 0:
            st.warning("扩散队列为空，请先运行初始发现任务")
        
        if st.button(
            "▶️ 开始扩散发现",
            disabled=running or stats['pending_expansions'] == 0,
            key="start_expand"
        ):
            if not st.session_state.repository:
                st.error("数据库未连接，无法启动任务")
            else:
                # 完全清空日志（内存和文件）
                clear_logs()
                
                # 添加新任务的开始日志
                add_log("=" * 60, "INFO")
                add_log("开始新的爬虫任务 - 扩散发现", "INFO")
                add_log("=" * 60, "INFO")
                add_log("用户启动扩散发现任务", "INFO")
                
                thread = threading.Thread(
                    target=run_crawler_task,
                    args=("expand", st.session_state.repository)
                )
                thread.daemon = True
                thread.start()
                set_crawler_running(True)
                # 设置跳转标记
                st.session_state.jump_to_logs = True
                st.session_state.auto_refresh_enabled = True  # 确保自动刷新开启
                time.sleep(0.5)
                st.rerun()
    
    st.divider()
    
    # 配置参数
    with st.expander("⚙️ 高级配置", expanded=False):
        st.subheader("爬虫参数设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ai_threshold = st.slider(
                "AI内容占比阈值",
                min_value=0.1,
                max_value=0.9,
                value=0.3,
                step=0.05,
                format="%.0f%%",
                help="只有AI内容占比超过此阈值的频道才会被标记为合格"
            )
            
            sample_videos = st.number_input(
                "每个频道分析视频数",
                min_value=5,
                max_value=50,
                value=10,
                step=5,
                help="分析每个频道时抓取的视频数量"
            )
        
        with col2:
            rate_limit = st.number_input(
                "请求间隔(秒)",
                min_value=1,
                max_value=10,
                value=2,
                step=1,
                help="每次请求之间的延迟时间，避免被封禁"
            )
            
            max_kols = st.number_input(
                "最大KOL数量",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100,
                help="达到此数量后停止发现新KOL"
            )
        
        if st.button("💾 保存配置"):
            st.success("配置已保存！")


def render_data_browser():
    """渲染数据浏览页面"""
    st.markdown('<div class="main-header">📋 数据浏览器</div>', unsafe_allow_html=True)
    
    if not st.session_state.repository:
        st.warning("请先连接数据库")
        return
    
    # 筛选选项
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "状态筛选",
            ["全部", "合格", "待分析", "已拒绝"],
            index=1
        )
    
    with col2:
        sort_by = st.selectbox(
            "排序方式",
            ["AI占比", "订阅数", "平均观看", "发现时间"],
            index=0
        )
    
    with col3:
        limit = st.number_input(
            "显示数量",
            min_value=10,
            max_value=1000,
            value=50,
            step=10
        )
    
    # 构建查询
    status_map = {
        "全部": None,
        "合格": "qualified",
        "待分析": "pending",
        "已拒绝": "rejected"
    }
    
    sort_map = {
        "AI占比": "ai_ratio DESC",
        "订阅数": "subscribers DESC",
        "平均观看": "avg_views DESC",
        "发现时间": "discovered_at DESC"
    }
    
    # 查询数据
    query = "SELECT * FROM kols"
    if status_filter != "全部":
        query += f" WHERE status = '{status_map[status_filter]}'"
    query += f" ORDER BY {sort_map[sort_by]} LIMIT {limit}"
    
    kols = st.session_state.db.fetchall(query)
    
    if kols:
        df = pd.DataFrame(kols)
        
        # 选择要显示的列
        display_columns = [
            'channel_name', 'channel_url', 'subscribers', 'total_videos', 'ai_ratio',
            'avg_views', 'avg_likes', 'engagement_rate', 'status', 'discovered_at'
        ]
        
        display_df = df[display_columns].copy()
        
        display_df.columns = [
            '频道名称', '频道链接', '订阅数', '总视频', 'AI占比',
            '平均观看', '平均点赞', '互动率', '状态', '发现时间'
        ]
        
        # 格式化数据
        display_df['总视频'] = display_df['总视频'].apply(lambda x: str(int(x)))
        display_df['AI占比'] = display_df['AI占比'].apply(lambda x: f"{x*100:.1f}%")
        display_df['互动率'] = display_df['互动率'].apply(lambda x: f"{x:.2f}%")
        display_df['订阅数'] = display_df['订阅数'].apply(lambda x: f"{x:,}")
        display_df['平均观看'] = display_df['平均观看'].apply(lambda x: f"{x:,}")
        display_df['平均点赞'] = display_df['平均点赞'].apply(lambda x: f"{x:,}")
        
        # 格式化时间 - 将UTC时间转换为北京时间（UTC+8）
        def format_time(dt):
            if pd.isna(dt):
                return ""
            if isinstance(dt, str):
                dt = pd.to_datetime(dt)
            # 加8小时转换为北京时间
            dt_beijing = dt + pd.Timedelta(hours=8)
            return dt_beijing.strftime('%Y-%m-%d %H:%M:%S')
        
        display_df['发现时间'] = display_df['发现时间'].apply(format_time)
        
        # 动态计算表格高度：每行约35px，加上表头50px
        table_height = min(max(len(display_df) * 35 + 50, 200), 800)
        
        st.dataframe(
            display_df, 
            width='stretch', 
            hide_index=True, 
            height=table_height,
            column_config={
                "频道链接": st.column_config.LinkColumn(
                    "频道链接",
                    help="点击打开YouTube频道"
                ),
                "总视频": st.column_config.TextColumn(
                    "总视频"
                )
            }
        )
        
        # 导出按钮
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📥 导出Excel", key="export_excel"):
                from tasks.export_task import ExportTask
                export_task = ExportTask(st.session_state.repository)
                filepath = export_task.run()
                if filepath:
                    st.success(f"✅ 导出成功: {filepath}")
                    add_log(f"导出Excel: {filepath}", "SUCCESS")
        
        with col2:
            csv = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下载CSV",
                data=csv,
                file_name=f"kol_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("暂无数据")


def clear_logs():
    """清空日志"""
    global log_list
    log_list.clear()
    
    # 清空日志文件
    log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")
    if os.path.exists(log_file):
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("")
            return True
        except Exception as e:
            return False
    return True


def render_logs():
    """渲染日志查看页面"""
    st.markdown('<div class="main-header">📝 实时日志</div>', unsafe_allow_html=True)
    
    # 初始化自动刷新状态 - 默认开启
    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = True
    
    # 从文件读取爬虫状态（每次都重新读取，确保最新）
    crawler_is_running = is_crawler_running()
    
    # 日志控制
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
        # 自动刷新选项
        auto_refresh = st.checkbox(
            "自动刷新 (每3秒)", 
            value=st.session_state.auto_refresh_enabled,
            key="auto_refresh_checkbox_unique",
            help="爬虫运行时自动刷新日志"
        )
        # 更新状态
        if auto_refresh != st.session_state.auto_refresh_enabled:
            st.session_state.auto_refresh_enabled = auto_refresh
    
    # 显示日志
    st.divider()
    
    # 读取日志 - 只从文件读取，确保数据一致性
    log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")
    all_logs = []
    
    # 读取文件日志
    if os.path.exists(log_file):
        try:
            # 尝试多种编码读取
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
    
    # 显示日志数量和状态
    log_count = len(all_logs)
    display_count = min(log_count, 200)
    
    # 状态栏 - 改进UI，移除呼吸效果
    if crawler_is_running:
        st.markdown("""
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
        """.format(log_count=log_count, display_count=display_count), unsafe_allow_html=True)
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
        # 显示最新的日志（最新的在最下面）
        logs_text = "\n".join(all_logs[-200:])  # 显示最近200条
        
        # 使用HTML容器 + 自动滚动到底部
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
        
        # 创建日志容器 - 使用唯一ID
        log_container_id = f"log_container_{int(time.time() * 1000)}"
        
        # 转义HTML特殊字符
        import html
        logs_html = html.escape(logs_text)
        
        st.markdown(
            f'<div class="log-container" id="{log_container_id}">{logs_html}</div>',
            unsafe_allow_html=True
        )
        
        # JavaScript自动滚动到底部 - 使用setTimeout确保DOM加载完成
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
    
    # 自动刷新逻辑 - 简化，直接sleep后rerun
    if st.session_state.auto_refresh_enabled and crawler_is_running:
        time.sleep(3)
        st.rerun()


def render_ai_rules():
    """渲染AI规则配置页面"""
    st.markdown('<div class="main-header">🎯 AI过滤规则配置</div>', unsafe_allow_html=True)
    
    st.info("💡 配置AI内容识别规则，调整关键词和筛选条件")
    
    # 读取配置
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 基础参数配置
    st.subheader("📊 基础筛选参数")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**AI内容占比阈值**")
        # Slider直接使用0-100的范围，显示百分比
        ai_ratio_percentage = st.slider(
            "AI占比",
            min_value=0,
            max_value=100,
            value=int(config['crawler']['ai_ratio_threshold'] * 100),
            step=5,
            format="%d%%",
            help="只有AI内容占比超过此阈值的频道才会被标记为合格",
            label_visibility="collapsed"
        )
        # 转换回0-1的小数用于保存
        ai_ratio_threshold = ai_ratio_percentage / 100.0
    
    with col2:
        sample_video_count = st.number_input(
            "每个频道分析视频数",
            min_value=5,
            max_value=50,
            value=config['crawler']['sample_video_count'],
            step=5,
            help="分析每个频道时抓取的视频数量，越多越准确但越慢"
        )
    
    with col3:
        active_days_threshold = st.number_input(
            "活跃度阈值(天)",
            min_value=30,
            max_value=365,
            value=config['crawler']['active_days_threshold'],
            step=30,
            help="最后一次发布视频距今的天数，超过此值视为不活跃"
        )
    
    st.divider()
    
    # AI关键词配置
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
        high_keywords = st.text_area(
            "高优先级关键词（每行一个）",
            value="\n".join(config['keywords']['priority_high']),
            height=200,
            help="输入最新、最热门的AI工具名称"
        )
        newline = '\n'
        st.caption(f"✓ 当前数量: {len([k for k in high_keywords.split(newline) if k.strip()])} 个")
    
    with tab2:
        st.caption("💡 主流AI工具和常见术语（如：ChatGPT, Midjourney, Claude等）")
        medium_keywords = st.text_area(
            "中优先级关键词（每行一个）",
            value="\n".join(config['keywords']['priority_medium']),
            height=200,
            help="输入主流、常用的AI工具和术语"
        )
        st.caption(f"✓ 当前数量: {len([k for k in medium_keywords.split(newline) if k.strip()])} 个")
    
    with tab3:
        st.caption("💡 技术术语和专业词汇（如：LLM, Diffusion Model, AI workflow等）")
        low_keywords = st.text_area(
            "低优先级关键词（每行一个）",
            value="\n".join(config['keywords']['priority_low']),
            height=200,
            help="输入技术性较强的专业术语"
        )
        st.caption(f"✓ 当前数量: {len([k for k in low_keywords.split(newline) if k.strip()])} 个")
    
    st.divider()
    
    # 排除规则配置
    st.subheader("🚫 排除规则")
    
    st.markdown("""
    **排除规则说明**：
    - ⚠️ **匹配方式**：频道名称或视频标题中包含这些关键词将被自动排除
    - 💡 **常见类型**：课程/教学（第、讲、课）、学术机构（大学、研究所）、新闻媒体（news、新闻）等
    - ✏️ **完全自定义**：你可以添加任何想要排除的关键词，不限于上述分类
    - 🎯 **目的**：过滤掉非目标KOL，聚焦于AI内容创作者
    """)
    
    # 合并所有排除关键词到一个列表
    all_exclusion_keywords = []
    all_exclusion_keywords.extend(config['exclusion_rules'].get('course_keywords', []))
    all_exclusion_keywords.extend(config['exclusion_rules'].get('academic_keywords', []))
    all_exclusion_keywords.extend(config['exclusion_rules'].get('news_keywords', []))
    
    exclusion_keywords = st.text_area(
        "排除关键词（每行一个）",
        value="\n".join(all_exclusion_keywords),
        height=300,
        help="输入任何你想排除的关键词，如：课程、大学、新闻、tutorial、university等"
    )
    
    keyword_count = len([k for k in exclusion_keywords.split(newline) if k.strip()])
    st.caption(f"✓ 当前共 {keyword_count} 个排除关键词")
    
    # 显示一些常用示例
    with st.expander("💡 常用排除关键词参考", expanded=False):
        st.markdown("""
        **课程/教学类**：第、讲、课、lesson、lecture、tutorial、教程、教学、系列课
        
        **学术机构类**：university、大学、college、学院、institute、研究所、实验室
        
        **新闻媒体类**：news、新闻、media、媒体、报导、报道、频道
        
        **其他类型**：你可以根据实际需求添加任何关键词
        """)
    
    st.divider()
    
    # 保存按钮
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            # 更新配置
            config['crawler']['ai_ratio_threshold'] = ai_ratio_threshold
            config['crawler']['sample_video_count'] = sample_video_count
            config['crawler']['active_days_threshold'] = active_days_threshold
            
            config['keywords']['priority_high'] = [k.strip() for k in high_keywords.split(newline) if k.strip()]
            config['keywords']['priority_medium'] = [k.strip() for k in medium_keywords.split(newline) if k.strip()]
            config['keywords']['priority_low'] = [k.strip() for k in low_keywords.split(newline) if k.strip()]
            
            # 保存统一的排除关键词列表（为了兼容性，仍然保存到三个分类中，但实际使用时会合并）
            exclusion_list = [k.strip() for k in exclusion_keywords.split(newline) if k.strip()]
            config['exclusion_rules']['course_keywords'] = exclusion_list
            config['exclusion_rules']['academic_keywords'] = []
            config['exclusion_rules']['news_keywords'] = []
            
            # 保存到文件
            try:
                with open('config/config.json', 'w', encoding='utf-8') as f:
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
    
    # 显示当前配置摘要
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
    
    # 数据库设置
    st.subheader("🗄️ 数据库配置")
    
    st.info("💡 当前使用SQLite数据库，数据保存在 data/ai_kol_crawler.db")
    
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    col1, col2 = st.columns(2)
    
    with col1:
        db_host = st.text_input("数据库地址", value=config['database'].get('host', 'localhost'), disabled=True)
        db_port = st.number_input("端口", value=config['database'].get('port', 5432), disabled=True)
    
    with col2:
        db_name = st.text_input("数据库名", value=config['database'].get('database', 'ai_kol_crawler'), disabled=True)
        db_user = st.text_input("用户名", value=config['database'].get('user', 'postgres'), disabled=True)
    
    st.caption("💡 提示: SQLite数据库无需配置，如需使用PostgreSQL请修改 config/config.json")
    
    st.divider()
    
    # 导出设置
    st.subheader("📤 导出设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        output_dir = st.text_input("导出目录", value=config['export']['output_dir'])
    
    with col2:
        sort_by = st.selectbox(
            "默认排序",
            ["ai_ratio", "subscribers", "avg_views"],
            index=["ai_ratio", "subscribers", "avg_views"].index(config['export']['sort_by'])
        )
    
    st.divider()
    
    # 数据库管理
    st.subheader("🗂️ 数据库管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 查看数据库大小", use_container_width=True):
            import os
            db_path = 'data/ai_kol_crawler.db'
            if os.path.exists(db_path):
                size = os.path.getsize(db_path) / 1024 / 1024  # MB
                st.info(f"数据库大小: {size:.2f} MB")
            else:
                st.warning("数据库文件不存在")
    
    with col2:
        if st.button("💾 备份数据库", use_container_width=True):
            import shutil
            from datetime import datetime
            try:
                backup_name = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
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
                        st.session_state.db.execute("DELETE FROM videos")
                        st.session_state.db.execute("DELETE FROM expansion_queue")
                        st.session_state.db.execute("DELETE FROM kols")
                        st.success("✅ 数据库已清空")
                except Exception as e:
                    st.error(f"❌ 清空失败: {e}")
    
    st.divider()
    
    # 系统信息
    st.subheader("ℹ️ 系统信息")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**版本信息**")
        st.write("- 系统版本: v1.0")
        st.write("- 数据库: SQLite")
        st.write("- Python版本:", sys.version.split()[0])
    
    with col2:
        st.write("**统计信息**")
        stats = get_statistics()
        st.write(f"- 总KOL数: {stats['total_kols']}")
        st.write(f"- 合格KOL数: {stats['qualified_kols']}")
        st.write(f"- 总视频数: {stats['total_videos']}")


if __name__ == "__main__":
    """主程序"""
    init_session_state()
    
    # 初始化跳转标记和当前页面
    if 'jump_to_logs' not in st.session_state:
        st.session_state.jump_to_logs = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📊 仪表盘"
    
    # 侧边栏
    with st.sidebar:
        st.title("🤖 AI KOL爬虫")
        st.caption("智能发现AI领域KOL")
        st.title("导航菜单")
        
        # 数据库连接状态
        if connect_database():
            st.success("✅ 数据库已连接")
        else:
            st.error("❌ 数据库未连接")
        
        st.divider()
        
        # 页面选择
        pages = ["📊 仪表盘", "🚀 爬虫控制", "📋 数据浏览", "📝 日志查看", "🎯 AI规则", "⚙️ 设置"]
        
        # 如果需要跳转到日志，更新当前页面
        if st.session_state.jump_to_logs:
            st.session_state.current_page = "📝 日志查看"
            st.session_state.jump_to_logs = False
        
        # 获取当前页面的索引
        try:
            default_index = pages.index(st.session_state.current_page)
        except ValueError:
            default_index = 0
            st.session_state.current_page = pages[0]
        
        # 使用key来确保radio状态正确
        page = st.radio(
            "选择页面",
            pages,
            index=default_index,
            label_visibility="collapsed",
            key="page_selector"
        )
        
        # 只有当用户选择的页面与当前页面不同时才更新
        if page != st.session_state.current_page:
            st.session_state.current_page = page
            st.rerun()
        
        st.divider()
        
        # 快速统计
        stats = get_statistics()
        st.metric("合格KOL", stats['qualified_kols'])
        st.metric("总视频", stats['total_videos'])
        
        # 爬虫状态指示
        if is_crawler_running():
            st.warning("⚙️ 爬虫运行中...")
        
        st.divider()
        st.caption("AI KOL爬虫系统 v1.0")
        st.caption("© 2026 All Rights Reserved")
    
    # 主内容区 - 使用容器隔离每个页面
    main_container = st.container()
    
    with main_container:
        if page == "📊 仪表盘":
            render_dashboard()
        elif page == "🚀 爬虫控制":
            render_crawler_control()
        elif page == "📋 数据浏览":
            render_data_browser()
        elif page == "📝 日志查看":
            render_logs()
        elif page == "🎯 AI规则":
            render_ai_rules()
        elif page == "⚙️ 设置":
            render_settings()
