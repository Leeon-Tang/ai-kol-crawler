# -*- coding: utf-8 -*-
"""
数据浏览UI组件
"""
import streamlit as st
import pandas as pd
import os


def render_data_browser():
    """渲染统一的数据浏览页面"""
    st.markdown('<div class="main-header">数据浏览</div>', unsafe_allow_html=True)
    
    # 初始化平台选择
    if 'data_browser_platform' not in st.session_state:
        st.session_state.data_browser_platform = "YouTube"
    
    # 平台选择 - 使用按钮组（3个按钮：YouTube、GitHub-商业、GitHub-学术）
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("YouTube", key="btn_yt_data", use_container_width=True, 
                    type="primary" if st.session_state.data_browser_platform == "YouTube" else "secondary"):
            st.session_state.data_browser_platform = "YouTube"
            st.rerun()
    with col2:
        if st.button("GitHub-商业", key="btn_gh_commercial_data", use_container_width=True,
                    type="primary" if st.session_state.data_browser_platform == "GitHub_Commercial" else "secondary"):
            st.session_state.data_browser_platform = "GitHub_Commercial"
            st.rerun()
    with col3:
        if st.button("GitHub-学术", key="btn_gh_academic_data", use_container_width=True,
                    type="primary" if st.session_state.data_browser_platform == "GitHub_Academic" else "secondary"):
            st.session_state.data_browser_platform = "GitHub_Academic"
            st.rerun()
    
    st.divider()
    
    # 导入子模块
    from ui.youtube.data_browser import render_youtube_data_content
    from ui.github.data_browser import render_github_commercial_data, render_github_academic_data
    from ui.twitter.data_browser import render_twitter_data_content
    
    if st.session_state.data_browser_platform == "YouTube":
        render_youtube_data_content()
    elif st.session_state.data_browser_platform == "GitHub_Commercial":
        render_github_commercial_data()
    elif st.session_state.data_browser_platform == "GitHub_Academic":
        render_github_academic_data()
