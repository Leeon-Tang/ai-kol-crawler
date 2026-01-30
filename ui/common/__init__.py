# -*- coding: utf-8 -*-
"""
通用UI组件
"""
from .dashboard import render_youtube_dashboard, render_github_dashboard, render_twitter_dashboard
from .data_browser import render_data_browser
from .logs import render_logs
from .settings import render_settings

__all__ = [
    'render_youtube_dashboard',
    'render_github_dashboard',
    'render_twitter_dashboard',
    'render_data_browser',
    'render_logs',
    'render_settings'
]
