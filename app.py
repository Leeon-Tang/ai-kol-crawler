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

# 导入工具模块
from utils.log_manager import add_log, clear_logs
from utils.session_manager import init_session_state, connect_database, get_statistics
from utils.crawler_status import set_crawler_running, is_crawler_running, check_and_fix_crawler_status
from utils.config_loader import load_config
from ui.common.dashboard import render_youtube_dashboard, render_github_dashboard, render_twitter_dashboard
from ui.common.logs import render_logs
from ui.common.settings import render_settings
from ui.common.data_browser import render_data_browser

# 加载配置
config = load_config()

# 状态文件和日志目录路径
CRAWLER_STATUS_FILE = os.path.join(PROJECT_ROOT, "data", "crawler_status.txt")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# 页面配置
st.set_page_config(
    page_title="多平台爬虫系统",
    page_icon="",
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

# 包装函数，适配新模块
def _set_crawler_running(status):
    return set_crawler_running(status, CRAWLER_STATUS_FILE, add_log)

def _is_crawler_running():
    return is_crawler_running(CRAWLER_STATUS_FILE)

def _check_and_fix_crawler_status():
    return check_and_fix_crawler_status(CRAWLER_STATUS_FILE, add_log)

def _connect_database():
    return connect_database(add_log)

def _clear_logs():
    return clear_logs(LOG_DIR)

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
        
        _set_crawler_running(True)
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
            success = _set_crawler_running(False)
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
        from utils.crawler_status import should_stop
        
        _set_crawler_running(True)
        add_log(f"开始执行GitHub任务: {task_type}", "INFO")
        
        scraper = GitHubScraper()
        searcher = GitHubSearcher(scraper, repository)  # 传入repository用于去重
        analyzer = GitHubAnalyzer(scraper)
        
        if task_type == "discovery":
            # 获取学术人士仓库
            academic_repository = kwargs.get('academic_repository')
            task = GitHubDiscoveryTask(searcher, analyzer, repository, academic_repository)
            max_developers = kwargs.get('max_developers', 50)
            task.run(max_developers=max_developers)
        
        # 检查是否被停止
        if should_stop():
            add_log(f"GitHub任务被用户停止: {task_type}", "WARNING")
        else:
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
            success = _set_crawler_running(False)
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

def run_twitter_crawler_task(task_type, repository, **kwargs):
    """运行Twitter爬虫任务"""
    task = None
    try:
        from tasks.twitter.discovery import TwitterDiscoveryTask
        from utils.crawler_status import should_stop
        
        _set_crawler_running(True)
        add_log(f"开始执行Twitter任务: {task_type}", "INFO")
        
        task = TwitterDiscoveryTask()
        
        if task_type == "keyword_discovery":
            keyword_count = kwargs.get('keyword_count', 5)
            max_users_per_keyword = kwargs.get('max_users_per_keyword', 10)
            add_log(f"使用 {keyword_count} 个关键词进行搜索", "INFO")
            
            # 从配置文件读取关键词
            from utils.config_loader import load_config
            config = load_config()
            keywords = config.get('twitter', {}).get('search_keywords', [])[:keyword_count]
            
            stats = task.discover_by_keywords(keywords, max_results_per_keyword=max_users_per_keyword)
            add_log(f"关键词发现完成: 发现 {stats['total_discovered']} 个用户，合格 {stats['qualified']} 个", "SUCCESS")
            
        elif task_type == "hashtag_discovery":
            hashtag_count = kwargs.get('hashtag_count', 3)
            max_users = kwargs.get('max_users', 20)
            add_log(f"使用 {hashtag_count} 个话题标签进行搜索", "INFO")
            
            # 从配置文件读取话题标签
            from utils.config_loader import load_config
            config = load_config()
            hashtags = config.get('twitter', {}).get('hashtags', [])[:hashtag_count]
            
            stats = task.discover_by_hashtags(hashtags, max_results=max_users)
            add_log(f"话题发现完成: 发现 {stats['total_discovered']} 个用户，合格 {stats['qualified']} 个", "SUCCESS")
        
        # 检查是否被停止
        if should_stop():
            add_log(f"Twitter任务被用户停止: {task_type}", "WARNING")
        else:
            add_log(f"Twitter任务完成: {task_type}", "SUCCESS")
        add_log("正在更新爬虫状态...", "INFO")
        
    except KeyboardInterrupt:
        add_log("任务被用户中断", "WARNING")
    except Exception as e:
        add_log(f"Twitter任务执行失败: {str(e)}", "ERROR")
        add_log(traceback.format_exc(), "ERROR")
    finally:
        # 确保状态一定会被更新
        try:
            add_log("任务结束，正在停止爬虫...", "INFO")
            success = _set_crawler_running(False)
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



def render_youtube_crawler():
    """渲染YouTube爬虫控制"""
    st.markdown('<div class="main-header">YouTube 爬虫控制</div>', unsafe_allow_html=True)
    
    # 检查并修复状态
    _check_and_fix_crawler_status()
    
    running = _is_crawler_running()
    if running:
        st.warning("爬虫正在运行中，请等待任务完成...")
        st.info("切换到「日志查看」页面查看实时进度")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("标记为已完成", key="mark_complete", use_container_width=True):
                success = _set_crawler_running(False)
                if success:
                    st.success("状态已重置")
                    time.sleep(0.5)
                else:
                    st.error("状态重置失败")
                st.rerun()
        
        with col2:
            if st.button("强制重置状态", key="force_reset", use_container_width=True):
                try:
                    # 强制写入
                    with open(CRAWLER_STATUS_FILE, 'w', encoding='utf-8') as f:
                        f.write("stopped")
                    st.success("已强制重置")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"强制重置失败: {e}")
    else:
        st.success("爬虫空闲，可以启动新任务")
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("初始发现任务")
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
        
        if st.button("开始初始发现", disabled=running, key="start_youtube_discovery"):
                if not st.session_state.youtube_repository:
                    st.error("数据库未连接，无法启动任务")
                else:
                    _clear_logs()
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
                    _set_crawler_running(True)
                    st.session_state.jump_to_logs = True
                    st.session_state.auto_refresh_enabled = True
                    time.sleep(0.5)
                    st.rerun()
    
    with col2:
        st.subheader("扩散发现任务")
        st.write("从已有KOL的推荐列表中发现新KOL")
        
        stats = get_statistics('youtube')
        st.info(f"当前待扩散队列: {stats.get('pending_expansions', 0)} 个KOL")
        
        if stats.get('pending_expansions', 0) == 0:
            st.warning("扩散队列为空，请先运行初始发现任务")
        
        if st.button("开始扩散发现", disabled=running or stats.get('pending_expansions', 0) == 0, key="start_youtube_expand"):
                if not st.session_state.youtube_repository:
                    st.error("数据库未连接，无法启动任务")
                else:
                    _clear_logs()
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
                    _set_crawler_running(True)
                    st.session_state.jump_to_logs = True
                    st.session_state.auto_refresh_enabled = True
                    time.sleep(0.5)
                    st.rerun()
    
    st.divider()
    
    with st.expander("高级配置", expanded=False):
        st.subheader("爬虫参数设置")
        col1, col2 = st.columns(2)
        with col1:
            ai_threshold = st.slider("AI内容占比阈值", min_value=0.1, max_value=0.9, value=0.3, step=0.05, format="%.0f%%")
            sample_videos = st.number_input("每个频道分析视频数", min_value=5, max_value=50, value=10, step=5)
        with col2:
            rate_limit = st.number_input("请求间隔(秒)", min_value=1, max_value=10, value=2, step=1)
            max_kols = st.number_input("最大KOL数量", min_value=100, max_value=10000, value=1000, step=100)
        if st.button("保存配置"):
            st.success("配置已保存！")

def render_github_crawler():
    """渲染GitHub爬虫控制"""
    from ui.github import render_crawler
    render_crawler(
        is_crawler_running_func=_is_crawler_running,
        check_and_fix_status_func=_check_and_fix_crawler_status,
        set_crawler_running_func=_set_crawler_running,
        clear_logs_func=_clear_logs,
        add_log_func=add_log,
        run_crawler_task_func=run_github_crawler_task,
        session_state=st.session_state,
        crawler_status_file=CRAWLER_STATUS_FILE,
        time_module=time,
        threading_module=threading,
        academic_repository=st.session_state.github_academic_repository,
        config=config
    )

def render_twitter_crawler():
    """渲染Twitter爬虫控制"""
    from ui.twitter import render_crawler
    render_crawler(
        is_crawler_running_func=_is_crawler_running,
        check_and_fix_status_func=_check_and_fix_crawler_status,
        set_crawler_running_func=_set_crawler_running,
        clear_logs_func=_clear_logs,
        add_log_func=add_log,
        run_crawler_task_func=run_twitter_crawler_task,
        session_state=st.session_state,
        crawler_status_file=CRAWLER_STATUS_FILE,
        time_module=time,
        threading_module=threading
    )


def render_ai_rules():
    """渲染YouTube AI规则配置页面"""
    from ui.youtube import render_rules
    render_rules(PROJECT_ROOT, add_log)

def render_github_rules():
    """渲染GitHub规则配置页面"""
    from ui.github import render_rules
    render_rules(PROJECT_ROOT, add_log)


if __name__ == "__main__":
    """主程序"""
    init_session_state()
    
    with st.sidebar:
        st.markdown("### 多平台爬虫")
        
        if _connect_database():
            st.success("已连接")
        else:
            st.error("未连接")
        
        # 快速统计 - 更紧凑
        youtube_stats = get_statistics('youtube')
        github_stats = get_statistics('github')
        # twitter_stats = get_statistics('twitter')  # 暂时禁用
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**YouTube**")
            st.markdown(f"<div class='stat-number'>{youtube_stats.get('qualified_kols', 0)}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("**GitHub**")
            st.markdown(f"<div class='stat-number'>{github_stats.get('qualified_developers', 0)}</div>", unsafe_allow_html=True)
        # with col3:
        #     st.markdown("**Twitter**")
        #     st.markdown(f"<div class='stat-number'>{twitter_stats.get('qualified_users', 0)}</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # 数据浏览（最前面）
        is_active = st.session_state.current_page == "data_browser"
        if st.button(
            "数据浏览", 
            key="btn_data_browser", 
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.current_page = "data_browser"
            st.rerun()
        
        # YouTube分类
        st.markdown("### YouTube")
        youtube_pages = {
            "youtube_dashboard": "仪表盘",
            "youtube_crawler": "爬虫",
            "youtube_ai_rules": "规则"
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
        st.markdown("### GitHub")
        github_pages = {
            "github_dashboard": "仪表盘",
            "github_crawler": "爬虫",
            "github_rules": "规则"
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
        
        # Twitter分类 - 暂时禁用(功能未完善)
        # st.markdown("### Twitter/X")
        # twitter_pages = {
        #     "twitter_dashboard": "仪表盘",
        #     "twitter_crawler": "爬虫"
        # }
        # 
        # for page_key, page_name in twitter_pages.items():
        #     is_active = st.session_state.current_page == page_key
        #     if st.button(
        #         page_name, 
        #         key=f"btn_{page_key}", 
        #         use_container_width=True,
        #         type="primary" if is_active else "secondary"
        #     ):
        #         st.session_state.current_page = page_key
        #         st.rerun()
        
        st.divider()
        
        # 日志查看和设置（最后面）
        system_pages = {
            "logs": "日志查看",
            "settings": "设置"
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
        
        if _is_crawler_running():
            st.warning("爬虫运行中...")
        
        st.caption("多平台爬虫系统 v2.0")
        st.caption("© 2026 All Rights Reserved")
    
    # 处理跳转到日志
    if st.session_state.jump_to_logs:
        st.session_state.current_page = "logs"
        st.session_state.jump_to_logs = False
    
    # 主内容区
    page = st.session_state.current_page
    
    if page == "youtube_dashboard":
        render_youtube_dashboard(get_statistics)
    elif page == "youtube_crawler":
        render_youtube_crawler()
    elif page == "youtube_ai_rules":
        render_ai_rules()
    elif page == "github_dashboard":
        render_github_dashboard(get_statistics)
    elif page == "github_crawler":
        render_github_crawler()
    elif page == "github_rules":
        render_github_rules()
    # Twitter 页面暂时禁用(功能未完善)
    # elif page == "twitter_dashboard":
    #     render_twitter_dashboard(get_statistics)
    # elif page == "twitter_crawler":
    #     render_twitter_crawler()
    elif page == "data_browser":
        render_data_browser()
    elif page == "logs":
        render_logs(_check_and_fix_crawler_status, _is_crawler_running, _clear_logs, LOG_DIR)
    elif page == "settings":
        render_settings(add_log, get_statistics)
    else:
        render_youtube_dashboard(get_statistics)
