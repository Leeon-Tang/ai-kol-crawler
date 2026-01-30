# -*- coding: utf-8 -*-
"""
Twitter数据浏览UI组件
"""
import streamlit as st
import pandas as pd
import os
from utils.log_manager import add_log


def render_twitter_data_content():
    """渲染Twitter数据内容"""
    if not st.session_state.twitter_repository:
        st.warning("请先连接数据库")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("状态筛选", ["全部", "合格", "待分析"], index=1, key="tw_status")
    with col2:
        sort_by = st.selectbox("排序方式", ["爬取时间", "质量分数", "粉丝数", "推文数"], index=0, key="tw_sort")
    with col3:
        limit = st.number_input("显示数量", min_value=10, max_value=1000, value=50, step=10, key="tw_limit")
    
    status_map = {"全部": None, "合格": "qualified", "待分析": "pending"}
    sort_map = {"爬取时间": "discovered_at DESC", "质量分数": "quality_score DESC", "粉丝数": "followers_count DESC", "推文数": "tweet_count DESC"}
    
    query = "SELECT * FROM twitter_users"
    if status_filter != "全部":
        query += f" WHERE status = '{status_map[status_filter]}'"
    query += f" ORDER BY {sort_map[sort_by]} LIMIT {limit}"
    
    try:
        users = st.session_state.db.fetchall(query)
    except Exception as e:
        st.error(f"数据库查询失败: {str(e)}")
        add_log(f"Twitter数据查询失败: {str(e)}", "ERROR")
        
        # 提供修复选项
        if st.button("尝试修复数据库", key="repair_db_tw"):
            if st.session_state.db.repair_database():
                st.success("数据库修复成功，请刷新页面")
                add_log("数据库修复成功", "SUCCESS")
            else:
                st.error("数据库修复失败")
                add_log("数据库修复失败", "ERROR")
        return
    
    if users:
        df = pd.DataFrame(users)
        display_columns = ['username', 'name', 'followers_count', 'tweet_count', 'ai_ratio', 
                         'quality_score', 'avg_engagement', 'verified', 'contact_info', 'status', 'discovered_at']
        display_df = df[display_columns].copy()
        display_df.columns = ['用户名', '姓名', '粉丝数', '推文数', 'AI相关度', '质量分数', '平均互动', '认证', '联系方式', '状态', '爬取时间']
        
        display_df['粉丝数'] = display_df['粉丝数'].apply(lambda x: f"{x:,}")
        display_df['推文数'] = display_df['推文数'].apply(lambda x: f"{x:,}")
        display_df['AI相关度'] = display_df['AI相关度'].apply(lambda x: f"{x*100:.1f}%")
        display_df['质量分数'] = display_df['质量分数'].apply(lambda x: f"{x:.1f}")
        display_df['平均互动'] = display_df['平均互动'].apply(lambda x: f"{x:.1f}")
        display_df['认证'] = display_df['认证'].apply(lambda x: '已认证' if x == 1 else '未认证')
        display_df['联系方式'] = display_df['联系方式'].fillna('')
        
        # 时间格式化
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
        st.dataframe(display_df, width='stretch', hide_index=True, height=table_height)
        
        st.divider()
        
        # 导出按钮区域
        col1, col2 = st.columns(2)
        
        with col1:
            # 导出所有数据
            if st.button("导出所有数据", key="export_tw_all_data", use_container_width=True):
                try:
                    from tasks.twitter.export import TwitterExportTask
                    export_task = TwitterExportTask()
                    filepath = export_task.export_qualified_users(limit=1000)
                    if filepath and os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            excel_data = f.read()
                        st.download_button(
                            label="下载Excel文件",
                            data=excel_data,
                            file_name=os.path.basename(filepath),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="download_tw_all_excel_file"
                        )
                        add_log(f"导出Excel成功: {filepath}", "SUCCESS")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
                    add_log(f"导出Excel失败: {str(e)}", "ERROR")
        
        with col2:
            # 导出CSV
            if st.button("导出CSV", key="export_tw_csv", use_container_width=True):
                try:
                    from tasks.twitter.export import TwitterExportTask
                    export_task = TwitterExportTask()
                    filepath = export_task.export_all_users_csv()
                    if filepath and os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            csv_data = f.read()
                        st.download_button(
                            label="下载CSV文件",
                            data=csv_data,
                            file_name=os.path.basename(filepath),
                            mime="text/csv",
                            use_container_width=True,
                            key="download_tw_csv_file"
                        )
                        add_log(f"导出CSV成功: {filepath}", "SUCCESS")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
                    add_log(f"导出CSV失败: {str(e)}", "ERROR")
    else:
        st.info("暂无数据")
