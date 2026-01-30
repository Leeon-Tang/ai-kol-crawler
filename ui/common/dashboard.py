# -*- coding: utf-8 -*-
"""
仪表盘渲染组件
"""
import streamlit as st


def render_youtube_dashboard(get_statistics_func):
    """渲染YouTube仪表盘"""
    st.markdown('<div class="main-header">YouTube 数据概览</div>', unsafe_allow_html=True)
    
    stats = get_statistics_func('youtube')
    
    # 第一行：主要指标（大卡片）
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">总KOL数</div>
            <div class="metric-value">{stats.get('total_kols', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="big-metric-card highlight">
            <div class="metric-label">合格KOL</div>
            <div class="metric-value">{stats.get('qualified_kols', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">待分析</div>
            <div class="metric-value">{stats.get('pending_kols', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 第二行：次要指标（中等卡片）
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">总视频数</div>
            <div class="metric-value-medium">{stats.get('total_videos', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">待扩散队列</div>
            <div class="metric-value-medium">{stats.get('pending_expansions', 0)}</div>
        </div>
        """, unsafe_allow_html=True)


def render_github_dashboard(get_statistics_func):
    """渲染GitHub仪表盘"""
    st.markdown('<div class="main-header">GitHub 数据概览</div>', unsafe_allow_html=True)
    
    stats = get_statistics_func('github')
    
    # 第一行：商业开发者统计
    st.subheader("💼 商业/独立开发者")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">总开发者数</div>
            <div class="metric-value">{stats.get('total_developers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="big-metric-card highlight">
            <div class="metric-label">合格开发者</div>
            <div class="metric-value">{stats.get('qualified_developers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">待分析</div>
            <div class="metric-value">{stats.get('pending_developers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 第二行：学术人士统计
    st.subheader("🎓 学术人士")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">总学术人士</div>
            <div class="metric-value">{stats.get('total_academic_developers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="big-metric-card highlight">
            <div class="metric-label">合格学术人士</div>
            <div class="metric-value">{stats.get('qualified_academic_developers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">待分析</div>
            <div class="metric-value">{stats.get('pending_academic_developers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 第三行：综合统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">总仓库数</div>
            <div class="metric-value-medium">{stats.get('total_repositories', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        qualified = stats.get('qualified_developers', 0)
        total = max(stats.get('total_developers', 1), 1)
        rate = (qualified / total * 100)
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">商业合格率</div>
            <div class="metric-value-medium">{rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        repos = stats.get('total_repositories', 0)
        devs = max(stats.get('total_developers', 1) + stats.get('total_academic_developers', 0), 1)
        avg = repos / devs
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">平均仓库数</div>
            <div class="metric-value-medium">{avg:.1f}</div>
        </div>
        """, unsafe_allow_html=True)


def render_twitter_dashboard(get_statistics_func):
    """渲染Twitter仪表盘"""
    st.markdown('<div class="main-header">Twitter/X 数据概览</div>', unsafe_allow_html=True)
    
    stats = get_statistics_func('twitter')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">总用户数</div>
            <div class="metric-value">{stats.get('total_users', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="big-metric-card highlight">
            <div class="metric-label">合格用户</div>
            <div class="metric-value">{stats.get('qualified_users', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="big-metric-card">
            <div class="metric-label">待分析</div>
            <div class="metric-value">{stats.get('pending_users', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">总推文数</div>
            <div class="metric-value-medium">{stats.get('total_tweets', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        ai_tweets = stats.get('ai_tweets', 0)
        total_tweets = max(stats.get('total_tweets', 1), 1)
        ai_rate = (ai_tweets / total_tweets * 100)
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">AI推文占比</div>
            <div class="metric-value-medium">{ai_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_score = stats.get('avg_quality_score', 0)
        st.markdown(f"""
        <div class="medium-metric-card">
            <div class="metric-label">平均质量分</div>
            <div class="metric-value-medium">{avg_score:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
