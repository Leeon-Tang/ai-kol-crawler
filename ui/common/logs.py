# -*- coding: utf-8 -*-
"""
日志查看UI组件
"""
import streamlit as st
import os
import time


def render_logs(check_and_fix_status_func, is_crawler_running_func, clear_logs_func, log_dir):
    """渲染日志查看页面"""
    st.markdown('<div class="main-header">实时日志</div>', unsafe_allow_html=True)
    
    # 检查并修复状态
    check_and_fix_status_func()
    
    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = True
    
    crawler_is_running = is_crawler_running_func()
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("刷新日志", key="refresh_logs_btn"):
            st.rerun()
    with col2:
        if st.button("清空日志", key="clear_logs_btn"):
            if clear_logs_func():
                st.success("日志已清空")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("清空日志失败")
    with col3:
        auto_refresh = st.checkbox("自动刷新 (每3秒)", value=st.session_state.auto_refresh_enabled,
                                   key="auto_refresh_checkbox_unique", help="爬虫运行时自动刷新日志")
        if auto_refresh != st.session_state.auto_refresh_enabled:
            st.session_state.auto_refresh_enabled = auto_refresh
    
    st.divider()
    
    # 使用北京时间获取日志文件
    from datetime import datetime, timedelta, timezone
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
    log_file = os.path.join(log_dir, f"{beijing_time.strftime('%Y%m%d')}.log")
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
                        爬虫运行中...
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
                        爬虫已停止
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
