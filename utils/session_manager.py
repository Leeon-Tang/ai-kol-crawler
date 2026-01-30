# -*- coding: utf-8 -*-
"""
会话状态管理
"""
import streamlit as st


def init_session_state():
    """初始化会话状态"""
    if 'db' not in st.session_state:
        st.session_state.db = None
    if 'youtube_repository' not in st.session_state:
        st.session_state.youtube_repository = None
    if 'github_repository' not in st.session_state:
        st.session_state.github_repository = None
    if 'github_academic_repository' not in st.session_state:
        st.session_state.github_academic_repository = None
    if 'twitter_repository' not in st.session_state:
        st.session_state.twitter_repository = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "youtube_dashboard"
    if 'jump_to_logs' not in st.session_state:
        st.session_state.jump_to_logs = False
    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = True


def connect_database(add_log_func):
    """连接数据库"""
    try:
        if st.session_state.db is None:
            from storage.database import Database
            from storage.repositories.youtube_repository import YouTubeRepository
            from storage.repositories.github_repository import GitHubRepository
            from storage.repositories.github_academic_repository import GitHubAcademicRepository
            from storage.repositories.twitter_repository import TwitterRepository
            
            db = Database()
            db.connect()
            
            # 检查数据库完整性
            if not db.check_integrity():
                add_log_func("检测到数据库损坏，尝试修复...", "WARNING")
                if db.repair_database():
                    add_log_func("数据库修复成功", "SUCCESS")
                else:
                    add_log_func("数据库修复失败，请手动检查", "ERROR")
                    st.error("数据库损坏且无法自动修复，请查看日志")
                    return False
            
            db.init_tables()
            
            # 尝试迁移旧数据
            try:
                from storage.migrations.migration_v2 import migrate
                migrate()
            except Exception as e:
                add_log_func(f"数据迁移检查: {e}", "WARNING")
            
            st.session_state.db = db
            st.session_state.youtube_repository = YouTubeRepository(db)
            st.session_state.github_repository = GitHubRepository(db)
            st.session_state.github_academic_repository = GitHubAcademicRepository(db)
            st.session_state.twitter_repository = TwitterRepository(db)
            return True
    except Exception as e:
        st.error(f"数据库连接失败: {str(e)}")
        add_log_func(f"数据库连接失败: {str(e)}", "ERROR")
        return False
    return True


def get_statistics(platform='youtube'):
    """获取统计数据"""
    if platform == 'youtube' and st.session_state.youtube_repository:
        try:
            return st.session_state.youtube_repository.get_statistics()
        except:
            return {'total_kols': 0, 'qualified_kols': 0, 'pending_kols': 0, 'total_videos': 0, 'pending_expansions': 0}
    elif platform == 'github' and st.session_state.github_repository:
        try:
            stats = st.session_state.github_repository.get_statistics()
            # 添加学术人士统计
            if st.session_state.github_academic_repository:
                academic_stats = st.session_state.github_academic_repository.get_statistics()
                stats.update(academic_stats)
            return stats
        except:
            return {'total_developers': 0, 'qualified_developers': 0, 'pending_developers': 0, 'total_repositories': 0,
                   'total_academic_developers': 0, 'qualified_academic_developers': 0, 'pending_academic_developers': 0}
    elif platform == 'twitter' and st.session_state.twitter_repository:
        try:
            return st.session_state.twitter_repository.get_statistics()
        except:
            return {'total_users': 0, 'qualified_users': 0, 'pending_users': 0, 'total_tweets': 0}
    return {}
