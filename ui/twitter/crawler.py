# -*- coding: utf-8 -*-
"""
Twitter爬虫控制UI
"""
import streamlit as st
from .texts import TEXTS


def render_crawler(
    is_crawler_running_func,
    check_and_fix_status_func,
    set_crawler_running_func,
    clear_logs_func,
    add_log_func,
    run_crawler_task_func,
    session_state,
    crawler_status_file,
    time_module,
    threading_module
):
    """渲染Twitter爬虫控制页面"""
    
    st.markdown(f'<div class="main-header">{TEXTS["crawler_title"]}</div>', unsafe_allow_html=True)
    
    # 检查并修复状态
    check_and_fix_status_func()
    
    running = is_crawler_running_func()
    
    if running:
        st.warning(TEXTS['crawler_running'])
        st.info(TEXTS['view_logs'])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(TEXTS['mark_complete'], key="mark_complete_twitter", use_container_width=True):
                success = set_crawler_running_func(False)
                if success:
                    st.success(TEXTS['status_reset'])
                    time_module.sleep(0.5)
                else:
                    st.error(TEXTS['reset_failed'])
                st.rerun()
        
        with col2:
            if st.button(TEXTS['force_reset'], key="force_reset_twitter", use_container_width=True):
                try:
                    with open(crawler_status_file, 'w', encoding='utf-8') as f:
                        f.write("stopped")
                    st.success(TEXTS['force_reset_success'])
                    time_module.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"{TEXTS['force_reset_failed']}: {e}")
    else:
        st.success(TEXTS['crawler_idle'])
    
    st.divider()
    
    # 爬虫任务选项
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader(TEXTS['keyword_discovery'])
        st.write(TEXTS['keyword_discovery_desc'])
        
        keyword_count = st.slider(
            TEXTS['keyword_count'],
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help=TEXTS['keyword_count_help'],
            key="twitter_keyword_count"
        )
        
        max_users_per_keyword = st.number_input(
            TEXTS['max_users'],
            min_value=5,
            max_value=50,
            value=10,
            step=5,
            key="twitter_max_users"
        )
        
        estimated_time = keyword_count * 2
        st.info(f"{TEXTS['estimated_time']} {estimated_time} {TEXTS['minutes']}")
        
        if st.button(TEXTS['start_keyword_discovery'], disabled=running, key="start_twitter_keyword_discovery"):
            if not session_state.twitter_repository:
                st.error(TEXTS['db_not_connected'])
            else:
                clear_logs_func()
                add_log_func("=" * 60, "INFO")
                add_log_func("开始新的爬虫任务 - Twitter关键词发现", "INFO")
                add_log_func("=" * 60, "INFO")
                add_log_func(f"用户启动关键词发现任务，关键词数量: {keyword_count}", "INFO")
                
                thread = threading_module.Thread(
                    target=run_crawler_task_func,
                    args=("keyword_discovery", session_state.twitter_repository),
                    kwargs={
                        'keyword_count': keyword_count,
                        'max_users_per_keyword': max_users_per_keyword
                    }
                )
                thread.daemon = True
                thread.start()
                set_crawler_running_func(True)
                session_state.jump_to_logs = True
                session_state.auto_refresh_enabled = True
                time_module.sleep(0.5)
                st.rerun()
    
    with col2:
        st.subheader(TEXTS['hashtag_discovery'])
        st.write(TEXTS['hashtag_discovery_desc'])
        
        hashtag_count = st.slider(
            TEXTS['hashtag_count'],
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            key="twitter_hashtag_count"
        )
        
        max_users_hashtag = st.number_input(
            "每个标签最大用户数",
            min_value=10,
            max_value=50,
            value=20,
            step=5,
            key="twitter_max_users_hashtag"
        )
        
        estimated_time_hashtag = hashtag_count * 1.5
        st.info(f"{TEXTS['estimated_time']} {estimated_time_hashtag:.0f} {TEXTS['minutes']}")
        
        if st.button(TEXTS['start_hashtag_discovery'], disabled=running, key="start_twitter_hashtag_discovery"):
            if not session_state.twitter_repository:
                st.error(TEXTS['db_not_connected'])
            else:
                clear_logs_func()
                add_log_func("=" * 60, "INFO")
                add_log_func("开始新的爬虫任务 - Twitter话题发现", "INFO")
                add_log_func("=" * 60, "INFO")
                add_log_func(f"用户启动话题发现任务，标签数量: {hashtag_count}", "INFO")
                
                thread = threading_module.Thread(
                    target=run_crawler_task_func,
                    args=("hashtag_discovery", session_state.twitter_repository),
                    kwargs={
                        'hashtag_count': hashtag_count,
                        'max_users': max_users_hashtag
                    }
                )
                thread.daemon = True
                thread.start()
                set_crawler_running_func(True)
                session_state.jump_to_logs = True
                session_state.auto_refresh_enabled = True
                time_module.sleep(0.5)
                st.rerun()
    
    st.divider()
    
    # 高级配置
    with st.expander("高级配置", expanded=False):
        st.subheader("爬虫参数设置")
        col1, col2 = st.columns(2)
        with col1:
            min_followers = st.number_input("最小粉丝数", min_value=100, max_value=10000, value=1000, step=100)
            ai_ratio = st.slider("AI相关度阈值", min_value=0.1, max_value=0.9, value=0.3, step=0.05, format="%.0f%%")
        with col2:
            sample_tweets = st.number_input("每个用户分析推文数", min_value=10, max_value=50, value=20, step=5)
            rate_limit = st.number_input("请求间隔(秒)", min_value=2, max_value=10, value=3, step=1)
        
        if st.button("保存配置"):
            st.success("配置已保存！")
