# -*- coding: utf-8 -*-
"""
YouTube UI文本内容
"""

# ==================== 标签 ====================

LABELS = {
    'rules_title': '🎯 YouTube AI过滤规则',
    'rules_info': '💡 配置AI内容识别规则，调整关键词和筛选条件',
    'basic_params': '📊 基础筛选参数',
    'ai_keywords': '🔑 AI关键词库',
    'exclusion_rules': '🚫 排除规则',
    'exclusion_channels': '🚫 已爬取频道黑名单',
    'high_priority_tab': '🔥 高优先级',
    'medium_priority_tab': '⭐ 中优先级',
    'low_priority_tab': '📌 低优先级',
    'save_config': '💾 保存配置',
    'config_saved': '✅ 配置已保存！',
    'config_save_failed': '❌ 保存失败',
    'crawler_title': '🚀 YouTube 爬虫控制',
    'dashboard_title': '📊 YouTube 数据概览'
}

# ==================== 帮助文本 ====================

HELP_TEXTS = {
    'ai_ratio': 'AI内容占比阈值，低于此值将被过滤',
    'sample_video_count': '每个频道分析的视频数量',
    'active_days': '频道最近活跃天数阈值',
    'high_keywords': '高优先级AI关键词，匹配权重最高',
    'medium_keywords': '中优先级AI关键词',
    'low_keywords': '低优先级AI关键词',
    'exclusion_keywords': '包含这些关键词的频道将被排除（如教程、新闻类）',
    'exclusion_channels': '已爬取过的频道ID列表，避免重复爬取浪费资源（适用于数据库被删除后重新爬取的场景）'
}

# ==================== 说明文本 ====================

CRAWLER_INFO = {
    'discovery': {
        'title': '🔍 初始发现任务',
        'description': '通过关键词搜索YouTube，发现新的AI KOL',
        'note': '预计搜索 {count} 个频道，耗时约 {time} 分钟'
    },
    'expand': {
        'title': '🌐 扩散发现任务',
        'description': '从已有KOL的推荐列表中发现新KOL',
        'note': '当前待扩散队列: {count} 个KOL'
    }
}
