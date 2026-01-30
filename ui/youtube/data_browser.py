# -*- coding: utf-8 -*-
"""
YouTube数据浏览UI组件
"""
import streamlit as st
import pandas as pd
import os
from utils.log_manager import add_log


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
    
    try:
        kols = st.session_state.db.fetchall(query)
    except Exception as e:
        st.error(f"数据库查询失败: {str(e)}")
        add_log(f"YouTube数据查询失败: {str(e)}", "ERROR")
        
        # 提供修复选项
        if st.button("尝试修复数据库", key="repair_db_yt"):
            if st.session_state.db.repair_database():
                st.success("数据库修复成功，请刷新页面")
                add_log("数据库修复成功", "SUCCESS")
            else:
                st.error("数据库修复失败")
                add_log("数据库修复失败", "ERROR")
        return
    
    if kols:
        df = pd.DataFrame(kols)
        display_columns = ['channel_name', 'channel_url', 'subscribers', 'total_videos', 'ai_ratio',
                         'avg_views', 'avg_likes', 'avg_comments', 'engagement_rate', 'contact_info', 'status', 'discovered_at']
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
            if st.button("导出所有数据", key="export_yt_all_data", use_container_width=True):
                try:
                    from tasks.youtube.export import YouTubeExportTask
                    export_task = YouTubeExportTask(st.session_state.youtube_repository)
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
                            key="download_yt_all_excel_file"
                        )
                        add_log(f"导出Excel成功: {filepath}", "SUCCESS")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
                    add_log(f"导出Excel失败: {str(e)}", "ERROR")
        
        with col2:
            # 导出今日数据
            from datetime import datetime, timedelta, timezone
            beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)
            today_str = beijing_time.strftime('%Y-%m-%d')
            
            if st.button(f"导出今日数据 ({today_str})", key="export_yt_today_data", use_container_width=True):
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
                            label="下载今日Excel文件",
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
                    st.error(f"导出失败: {str(e)}")
                    add_log(f"导出今日Excel失败: {str(e)}", "ERROR")
    else:
        st.info("暂无数据")
