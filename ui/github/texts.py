# -*- coding: utf-8 -*-
"""
GitHub UI文本内容
"""

# ==================== 说明文本 ====================

INDIE_DEVELOPER_EXPLANATION = """
**独立开发者必须同时满足以下条件：**

1. **不属于大公司** - 不在Google、Microsoft、Meta等大公司工作
2. **不是项目成员** - 不是ComfyUI、Automatic1111等知名项目的团队成员
3. **有原创项目** - 至少有3个非fork的原创仓库
4. **有影响力** - Followers ≥ 100 或 总Stars ≥ 500
5. **有AI项目** - 至少有1个AI相关的原创项目
6. **主要是创作者** - fork项目的stars占比不超过70%（避免纯贡献者）

**排除规则：**
- Bio或Company中标注为某项目成员（如"ComfyUI team member"）
- 主要贡献集中在fork的项目上
"""

KEYWORDS_EXPLANATION = """
**核心关键词分类：**

**生成式AI（重点）：**
- stable-diffusion, diffusion-model
- text-to-image, text-to-video
- image-generation, video-generation
- controlnet, animatediff

**机器学习/深度学习：**
- machine-learning, deep-learning
- pytorch, tensorflow, keras

**LLM/NLP：**
- gpt, llm, large-language-model
- chatbot, transformer, bert

**计算机视觉：**
- computer-vision, object-detection
- image-recognition, face-recognition
"""

# ==================== 默认配置 ====================

DEFAULT_CONFIG = {
    'min_followers': 100,
    'min_stars': 500,
    'min_repos': 3,
    'core_ai_keywords': [
        # 机器学习/深度学习
        'machine-learning', 'deep-learning', 'neural-network', 'ml-model',
        'pytorch', 'tensorflow', 'keras', 'scikit-learn',
        # 生成式AI（重点）
        'stable-diffusion', 'diffusion-model', 'text-to-image', 'text-to-video',
        'image-generation', 'video-generation', 'generative-ai', 'gan',
        'controlnet', 'animatediff',
        # LLM/NLP
        'gpt', 'llm', 'large-language-model', 'chatbot', 'transformer',
        'bert', 'nlp', 'natural-language',
        # 计算机视觉
        'computer-vision', 'object-detection', 'image-recognition',
        'yolo', 'opencv-ai', 'face-recognition'
    ],
    'helper_keywords': ['ai-tool', 'ai-app', 'ai-api', 'ai-sdk', 'ai-saas'],
    'exclusion_companies': [
        'Google', 'Microsoft', 'Meta', 'Facebook', 'Amazon', 'Apple',
        'Alibaba', 'Tencent', 'ByteDance', 'Baidu', 'Huawei', 'OpenAI',
        'Stability AI', 'Midjourney', 'Runway', 'Anthropic', 'Cohere',
        'AWS', 'Azure', 'GCP', 'Cloudflare', 'Vercel'
    ],
    'exclusion_projects': ['ComfyUI', 'Automatic1111', 'Stable Diffusion WebUI', 'LangChain']
}

# ==================== 帮助文本 ====================

HELP_TEXTS = {
    'min_followers': "开发者的最小粉丝数量",
    'min_stars': "所有原创仓库的总stars数",
    'min_repos': "非fork的原创仓库数量",
    'core_ai_keywords': "这些关键词用于判断项目是否与AI相关，包括：机器学习、生成式AI、LLM、计算机视觉等",
    'helper_keywords': "这些关键词需要与'ai'组合使用，如：ai-tool, ai-api, ai-sdk",
    'exclusion_companies': "Company字段包含这些名称的开发者将被过滤",
    'exclusion_projects': "Bio或Company中标注为这些项目成员的开发者将被过滤"
}

# ==================== 标签 ====================

LABELS = {
    'rules_title': '🎯 GitHub 筛选规则',
    'rules_info': '💡 配置GitHub独立开发者筛选规则',
    'indie_developer_criteria': '📊 独立开发者判断标准',
    'screening_params': '🎯 筛选参数',
    'ai_keywords': '🔑 AI项目识别关键词',
    'core_keywords_tab': '🎯 核心关键词',
    'helper_keywords_tab': '🔧 辅助关键词',
    'exclusion_companies': '🏢 排除的公司/组织',
    'exclusion_projects': '🚫 排除的项目团队',
    'save_config': '💾 保存配置',
    'config_saved': '✅ 配置已保存！新配置将在下次爬虫任务时生效',
    'config_save_failed': '❌ 保存失败',
    'crawler_title': '🚀 GitHub 爬虫控制',
    'dashboard_title': '📊 GitHub 数据概览'
}

CAPTIONS = {
    'core_keywords': '用于识别AI相关项目的核心关键词（匹配任意一个即可）',
    'helper_keywords': '辅助关键词（需要同时包含\'ai\'才算匹配）',
    'exclusion_companies': '在这些公司工作的开发者将被排除',
    'exclusion_projects': '这些项目的团队成员将被排除'
}

# ==================== 搜索策略 ====================

STRATEGY_INFO = {
    "quality_projects": "从Stable Diffusion、ComfyUI等优质AI项目（100+ stars）中找贡献者，筛选有影响力的开发者（最精准，推荐）",
    "comprehensive": "智能组合多种策略，小数量时只用最快的方法，大数量时全策略覆盖",
    "keywords": "通过AI相关关键词搜索仓库，提取owner（快速，适合小数量）",
    "topics": "通过GitHub Topics标签搜索（中等速度，质量较高）",
    "awesome": "从Awesome列表提取贡献者（慢但质量高）",
    "explore": "搜索trending项目（覆盖面广）",
    "indie": "专门搜索独立开发者关键词（精准但数量少）"
}

STRATEGY_NAMES = {
    "quality_projects": "🎯 优质项目贡献者（推荐）",
    "comprehensive": "📦 综合策略",
    "keywords": "🔑 仅关键词",
    "topics": "🏷️ 仅Topics",
    "awesome": "⭐ 仅Awesome列表",
    "explore": "🔭 仅Explore",
    "indie": "👤 仅独立开发者"
}

# ==================== 工具函数 ====================

def get_estimated_time(max_developers: int) -> str:
    """根据开发者数量估算时间"""
    if max_developers <= 10:
        return "约1-2分钟"
    elif max_developers <= 50:
        return "约3-5分钟"
    elif max_developers <= 100:
        return "约8-12分钟"
    else:
        return "约15-25分钟"
