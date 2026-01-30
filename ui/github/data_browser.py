# -*- coding: utf-8 -*-
"""
GitHub数据浏览UI组件
"""
import streamlit as st
import pandas as pd
import os
from utils.log_manager import add_log


def render_github_commercial_data():
    """渲染商业开发者数据"""
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("状态筛选", ["全部", "合格", "待分析", "已拒绝"], index=1, key="gh_commercial_status")
    with col2:
        sort_by = st.selectbox("排序方式", ["爬取时间", "总Stars", "Followers", "仓库数"], index=0, key="gh_commercial_sort")
    with col3:
        limit = st.number_input("显示数量", min_value=10, max_value=1000, value=50, step=10, key="gh_commercial_limit")
    
    status_map = {"全部": None, "合格": "qualified", "待分析": "pending", "已拒绝": "rejected"}
    sort_map = {"爬取时间": "discovered_at DESC", "总Stars": "total_stars DESC", "Followers": "followers DESC", "仓库数": "public_repos DESC"}
    
    query = "SELECT * FROM github_developers"
    if status_filter != "全部":
        query += f" WHERE status = '{status_map[status_filter]}'"
    query += f" ORDER BY {sort_map[sort_by]} LIMIT {limit}"
    
    try:
        devs = st.session_state.db.fetchall(query)
    except Exception as e:
        st.error(f"数据库查询失败: {str(e)}")
        add_log(f"GitHub商业数据查询失败: {str(e)}", "ERROR")
        
        if st.button("尝试修复数据库", key="repair_db_gh_commercial"):
            if st.session_state.db.repair_database():
                st.success("数据库修复成功，请刷新页面")
                add_log("数据库修复成功", "SUCCESS")
            else:
                st.error("数据库修复失败")
                add_log("数据库修复失败", "ERROR")
        return
    
    if devs:
        df = pd.DataFrame(devs)
        display_columns = ['username', 'name', 'profile_url', 'followers', 'public_repos', 'total_stars', 'contact_info', 'status', 'discovered_at']
        display_df = df[display_columns].copy()
        display_df.columns = ['用户名', '姓名', '主页链接', 'Followers', '仓库数', '总Stars', '联系方式', '状态', '爬取时间']
        
        display_df['Followers'] = display_df['Followers'].apply(lambda x: f"{x:,}")
        display_df['仓库数'] = display_df['仓库数'].apply(lambda x: f"{x:,}")
        display_df['总Stars'] = display_df['总Stars'].apply(lambda x: f"{x:,}")
        display_df['联系方式'] = display_df['联系方式'].fillna('')
        
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("导出所有数据", key="export_gh_commercial_all", use_container_width=True):
                try:
                    from tasks.github.export import GitHubExportTask
                    export_task = GitHubExportTask(st.session_state.github_repository)
                    filepath = export_task.run()
                    if filepath and os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            excel_data = f.read()
                        st.download_button(
                            label="下载Excel文件",
                            data=excel_data,
                            file_name=os.path.basename(filepath),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="download_gh_commercial_excel"
                        )
                        add_log(f"导出商业开发者Excel成功: {filepath}", "SUCCESS")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
                    add_log(f"导出商业开发者Excel失败: {str(e)}", "ERROR")
        
        with col2:
            from datetime import datetime, timedelta, timezone
            beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
            today_str = beijing_time.strftime('%Y-%m-%d')
            
            if st.button(f"导出今日数据 ({today_str})", key="export_gh_commercial_today", use_container_width=True):
                try:
                    from tasks.github.export import GitHubExportTask
                    export_task = GitHubExportTask(st.session_state.github_repository)
                    
                    today_start = beijing_time.replace(hour=0, minute=0, second=0, microsecond=0)
                    today_end = beijing_time.replace(hour=23, minute=59, second=59, microsecond=0)
                    
                    filepath = export_task.run_today(today_start, today_end)
                    if filepath and os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            excel_data = f.read()
                        st.download_button(
                            label="下载今日Excel文件",
                            data=excel_data,
                            file_name=os.path.basename(filepath),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="download_gh_commercial_today_excel"
                        )
                        add_log(f"导出今日商业开发者Excel成功: {filepath}", "SUCCESS")
                    else:
                        st.warning("今天暂无数据")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
                    add_log(f"导出今日商业开发者Excel失败: {str(e)}", "ERROR")
    else:
        st.info("暂无数据")



def render_github_academic_data():
    """渲染学术人士数据"""
    if not st.session_state.github_academic_repository:
        st.warning("学术人士仓库未初始化")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("状态筛选", ["全部", "合格", "待分析"], index=1, key="gh_academic_status")
    with col2:
        sort_by = st.selectbox("排序方式", ["爬取时间", "总Stars", "Followers", "仓库数"], index=0, key="gh_academic_sort")
    with col3:
        limit = st.number_input("显示数量", min_value=10, max_value=1000, value=50, step=10, key="gh_academic_limit")
    
    status_map = {"全部": None, "合格": "qualified", "待分析": "pending"}
    sort_map = {"爬取时间": "discovered_at DESC", "总Stars": "total_stars DESC", "Followers": "followers DESC", "仓库数": "public_repos DESC"}
    
    query = "SELECT * FROM github_academic_developers"
    if status_filter != "全部":
        query += f" WHERE status = '{status_map[status_filter]}'"
    query += f" ORDER BY {sort_map[sort_by]} LIMIT {limit}"
    
    try:
        devs = st.session_state.db.fetchall(query)
    except Exception as e:
        st.error(f"数据库查询失败: {str(e)}")
        add_log(f"GitHub学术数据查询失败: {str(e)}", "ERROR")
        
        if st.button("尝试修复数据库", key="repair_db_gh_academic"):
            if st.session_state.db.repair_database():
                st.success("数据库修复成功，请刷新页面")
                add_log("数据库修复成功", "SUCCESS")
            else:
                st.error("数据库修复失败")
                add_log("数据库修复失败", "ERROR")
        return
    
    if devs:
        df = pd.DataFrame(devs)
        display_columns = ['username', 'name', 'profile_url', 'followers', 'public_repos', 'total_stars', 'research_areas', 'contact_info', 'status', 'discovered_at']
        display_df = df[display_columns].copy()
        display_df.columns = ['用户名', '姓名', '主页链接', 'Followers', '仓库数', '总Stars', '研究领域', '联系方式', '状态', '爬取时间']
        
        display_df['Followers'] = display_df['Followers'].apply(lambda x: f"{x:,}")
        display_df['仓库数'] = display_df['仓库数'].apply(lambda x: f"{x:,}")
        display_df['总Stars'] = display_df['总Stars'].apply(lambda x: f"{x:,}")
        
        def format_research_areas(areas_json):
            if pd.isna(areas_json) or not areas_json:
                return ""
            try:
                import json
                areas = json.loads(areas_json)
                return ", ".join(areas) if areas else ""
            except:
                return str(areas_json)
        
        display_df['研究领域'] = display_df['研究领域'].apply(format_research_areas)
        display_df['联系方式'] = display_df['联系方式'].fillna('')
        
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("导出所有数据", key="export_gh_academic_all", use_container_width=True):
                try:
                    from tasks.github.export_academic import GitHubAcademicExportTask
                    export_task = GitHubAcademicExportTask(st.session_state.github_academic_repository)
                    filepath = export_task.run()
                    if filepath and os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            excel_data = f.read()
                        st.download_button(
                            label="下载Excel文件",
                            data=excel_data,
                            file_name=os.path.basename(filepath),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="download_gh_academic_excel"
                        )
                        add_log(f"导出学术人士Excel成功: {filepath}", "SUCCESS")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
                    add_log(f"导出学术人士Excel失败: {str(e)}", "ERROR")
        
        with col2:
            from datetime import datetime, timedelta, timezone
            beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
            today_str = beijing_time.strftime('%Y-%m-%d')
            
            if st.button(f"导出今日数据 ({today_str})", key="export_gh_academic_today", use_container_width=True):
                try:
                    from tasks.github.export_academic import GitHubAcademicExportTask
                    export_task = GitHubAcademicExportTask(st.session_state.github_academic_repository)
                    
                    today_start = beijing_time.replace(hour=0, minute=0, second=0, microsecond=0)
                    today_end = beijing_time.replace(hour=23, minute=59, second=59, microsecond=0)
                    
                    filepath = export_task.run_today(today_start, today_end)
                    if filepath and os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            excel_data = f.read()
                        st.download_button(
                            label="下载今日Excel文件",
                            data=excel_data,
                            file_name=os.path.basename(filepath),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="download_gh_academic_today_excel"
                        )
                        add_log(f"导出今日学术人士Excel成功: {filepath}", "SUCCESS")
                    else:
                        st.warning("今天暂无数据")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
                    add_log(f"导出今日学术人士Excel失败: {str(e)}", "ERROR")
    else:
        st.info("暂无数据")
