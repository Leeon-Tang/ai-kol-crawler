# -*- coding: utf-8 -*-
"""
GitHub爬虫控制页面
"""
import streamlit as st
from .texts import STRATEGY_INFO, STRATEGY_NAMES, get_estimated_time, LABELS


def render(
    is_crawler_running_func,
    check_and_fix_status_func,
    set_crawler_running_func,
    clear_logs_func,
    add_log_func,
    run_crawler_task_func,
    session_state,
    crawler_status_file,
    time_module,
    threading_module,
    academic_repository=None
):
    """
    渲染GitHub爬虫控制页面
    
    Args:
        is_crawler_running_func: 检查爬虫是否运行的函数
        check_and_fix_status_func: 检查并修复状态的函数
        set_crawler_running_func: 设置爬虫状态的函数
        clear_logs_func: 清空日志的函数
        add_log_func: 添加日志的函数
        run_crawler_task_func: 运行爬虫任务的函数
        session_state: Streamlit session state
        crawler_status_file: 爬虫状态文件路径
        time_module: time模块
        threading_module: threading模块
        academic_repository: 学术人士仓库（可选）
    """
    st.markdown(f'<div class="main-header">{LABELS["crawler_title"]}</div>', unsafe_allow_html=True)
    
    # 检查并修复状态
    check_and_fix_status_func()
    
    running = is_crawler_running_func()
    
    if running:
        st.warning("⚠️ 爬虫正在运行中，请等待任务完成...")
        st.info("💡 切换到「📝 日志查看」页面查看实时进度")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏹️ 标记为已完成", key="mark_complete_github", use_container_width=True):
                success = set_crawler_running_func(False)
                if success:
                    st.success("✅ 状态已重置")
                    time_module.sleep(0.5)
                else:
                    st.error("❌ 状态重置失败")
                st.rerun()
        
        with col2:
            if st.button("🔄 强制重置状态", key="force_reset_github", use_container_width=True):
                try:
                    # 强制写入
                    with open(crawler_status_file, 'w', encoding='utf-8') as f:
                        f.write("stopped")
                    st.success("✅ 已强制重置")
                    time_module.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 强制重置失败: {e}")
    else:
        st.success("✅ 爬虫空闲，可以启动新任务")
    
    st.divider()
    
    st.subheader("🔍 GitHub开发者发现")
    st.write("使用网页爬虫（无API限制）搜索GitHub，自动分类为商业开发者或学术人士")
    
    st.info("""
    **自动分类说明：**
    - 💼 **商业/独立开发者** - 专注于应用开发、产品、工具
    - 🎓 **学术人士** - 高校研究者、论文复现、模型训练
    - 爬虫会自动识别并分别存储到不同的表
    """)
    
    max_developers = st.slider(
        "目标商业开发者数量",
        min_value=10,
        max_value=500,
        value=50,
        step=10,
        help="限制本次任务最多爬取的商业开发者数量（学术人士会额外识别）"
    )
    
    st.info("💡 使用配置文件中的搜索关键词搜索项目，自动获取owner和贡献者")
    
    # 预估时间
    estimated_time = get_estimated_time(max_developers)
    st.caption(f"⏱️ 预计耗时：{estimated_time}（使用网页爬虫，无API限制）")
    
    if st.button("▶️ 开始GitHub发现", disabled=running, key="start_github_discovery"):
        if not session_state.github_repository:
            st.error("数据库未连接，无法启动任务")
        else:
            clear_logs_func()
            add_log_func("=" * 60, "INFO")
            add_log_func("开始新的爬虫任务 - GitHub开发者发现（自动分类）", "INFO")
            add_log_func("=" * 60, "INFO")
            add_log_func(f"用户启动GitHub发现任务", "INFO")
            add_log_func(f"  - 目标商业开发者: {max_developers}", "INFO")
            add_log_func(f"  - 自动识别学术人士", "INFO")
            add_log_func(f"  - 使用网页爬虫（无API限制）", "INFO")
            
            thread = threading_module.Thread(
                target=run_crawler_task_func,
                args=("discovery", session_state.github_repository),
                kwargs={
                    "max_developers": max_developers,
                    "academic_repository": academic_repository
                }
            )
            thread.daemon = True
            thread.start()
            set_crawler_running_func(True)
            session_state.jump_to_logs = True
            session_state.auto_refresh_enabled = True
            time_module.sleep(0.5)
            st.rerun()
