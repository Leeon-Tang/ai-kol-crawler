# -*- coding: utf-8 -*-
"""
设置页面UI组件
"""
import streamlit as st
import os
import sys


def render_settings(add_log_func, get_statistics_func):
    """渲染设置页面"""
    st.markdown('<div class="main-header">系统设置</div>', unsafe_allow_html=True)
    
    st.subheader("数据库信息")
    st.info("当前使用SQLite数据库，数据保存在 data/ai_kol_crawler.db")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("查看数据库大小", use_container_width=True):
            db_path = 'data/ai_kol_crawler.db'
            if os.path.exists(db_path):
                size = os.path.getsize(db_path) / 1024 / 1024
                st.info(f"数据库大小: {size:.2f} MB")
            else:
                st.warning("数据库文件不存在")
    
    with col2:
        if st.button("备份数据库", use_container_width=True):
            import shutil
            from datetime import datetime, timedelta, timezone
            try:
                backup_dir = "backups"
                os.makedirs(backup_dir, exist_ok=True)
                beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
                backup_name = f"{backup_dir}/backup_{beijing_time.strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy('data/ai_kol_crawler.db', backup_name)
                st.success(f"备份成功: {backup_name}")
            except Exception as e:
                st.error(f"备份失败: {e}")
    
    with col3:
        if st.button("修复数据库", use_container_width=True):
            if st.session_state.db:
                with st.spinner("正在修复数据库..."):
                    if st.session_state.db.repair_database():
                        st.success("数据库修复成功")
                        add_log_func("数据库修复成功", "SUCCESS")
                    else:
                        st.error("数据库修复失败")
                        add_log_func("数据库修复失败", "ERROR")
            else:
                st.warning("数据库未连接")
    
    st.divider()
    
    st.subheader("系统信息")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**版本信息**")
        st.write("- 系统版本: v2.0")
        st.write("- 数据库: SQLite")
        st.write("- Python:", sys.version.split()[0])
    
    with col2:
        st.write("**统计信息**")
        youtube_stats = get_statistics_func('youtube')
        github_stats = get_statistics_func('github')
        twitter_stats = get_statistics_func('twitter')
        st.write(f"- YouTube KOL: {youtube_stats.get('qualified_kols', 0)}")
        st.write(f"- GitHub开发者: {github_stats.get('qualified_developers', 0)}")
        st.write(f"- Twitter用户: {twitter_stats.get('qualified_users', 0)}")
