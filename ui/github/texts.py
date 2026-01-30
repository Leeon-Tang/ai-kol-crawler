# -*- coding: utf-8 -*-
"""
GitHub UI文本内容
"""

# ==================== 说明文本 ====================

INDIE_DEVELOPER_EXPLANATION = """
**独立开发者必须同时满足以下条件：**

1. **不属于大公司** - 不在Google、Microsoft、Meta等大公司工作
2. **不是项目成员** - 不是ComfyUI、Automatic1111等知名项目的团队成员
3. **有影响力** - Followers或总Stars达到配置的阈值
4. **有AI项目** - 至少有1个AI相关的原创项目

**排除规则：**
- Bio或Company中标注为某项目成员（如"ComfyUI team member"）
"""

KEYWORDS_EXPLANATION = """
**多模态应用关键词分类：**

**图像生成（核心）：**
- stable-diffusion, diffusion-model
- text-to-image, image-generation
- controlnet, lora, checkpoint
- midjourney, dalle, flux

**视频生成（核心）：**
- text-to-video, image-to-video
- video-generation, animatediff
- ai-video

**多模态模型：**
- multimodal, vision-language
- clip, blip, llava
- gpt-4v, gemini-vision

**3D生成：**
- text-to-3d, 3d-generation
- nerf, gaussian-splatting

**应用工具：**
- comfyui, automatic1111
- ai-art, ai-painting
"""

# ==================== 默认配置 ====================

DEFAULT_CONFIG = {
    'min_followers': 100,
    'min_stars': 500,
    'academic_min_followers': 50,
    'academic_min_stars': 100,
    'search_keywords': [
        'stable diffusion', 'ComfyUI', 'text-to-image', 'text-to-video',
        'image generation', 'video generation', 'AI SaaS', 'AI tool',
        'AI application', 'generative AI', 'diffusion model', 'AI API', 'AI SDK',
        'awesome-generative-ai', 'awesome-ai-tools', 'awesome-stable-diffusion',
        'awesome-image-generation', 'awesome-video', 'awesome-diffusion'
    ],
    'core_ai_keywords': [
        # 图像生成（核心）
        'stable-diffusion', 'diffusion-model', 'text-to-image', 'image-to-video',
        'image-generation', 'video-generation', 'generative-ai',
        'controlnet', 'animatediff', 'comfyui', 'automatic1111',
        'midjourney', 'dalle', 'flux', 'lora', 'checkpoint',
        'ai-art', 'ai-painting', 'ai-video',
        # 视频生成
        'text-to-video', 'image-to-video', 'video-generation',
        # 多模态
        'multimodal', 'vision-language', 'clip', 'blip', 'llava',
        'gpt-4v', 'gemini-vision', 'image-captioning', 'visual-question-answering',
        # 3D生成
        'text-to-3d', '3d-generation', 'nerf', 'gaussian-splatting'
    ],
    'exclusion_companies': [
        'Google', 'Microsoft', 'Meta', 'Facebook', 'Amazon', 'Apple',
        'Alibaba', 'Tencent', 'ByteDance', 'Baidu', 'Huawei', 'OpenAI',
        'Stability AI', 'Midjourney', 'Runway', 'Anthropic', 'Cohere',
        'AWS', 'Azure', 'GCP', 'Cloudflare', 'Vercel'
    ],
    'exclusion_projects': ['ComfyUI', 'Automatic1111', 'Stable Diffusion WebUI', 'LangChain'],
    'exclusion_developers': [],  # 已爬取的开发者黑名单
    # 学术特征配置
    'academic_keywords': [
        'university', 'college', 'institute', 'research', 'lab', 'laboratory',
        'phd', 'ph.d', 'professor', 'postdoc', 'post-doc', 'student',
        'academic', 'scholar', 'researcher', 'faculty',
        '大学', '学院', '研究所', '实验室', '博士', '教授', '研究员', '学者'
    ],
    'research_project_keywords': [
        'paper', 'arxiv', 'implementation', 'reproduction', 'reproduce',
        'research', 'experiment', 'benchmark', 'dataset', 'pretrained',
        'model', 'training', '论文', '复现', '实验', '研究'
    ]
}

# ==================== 帮助文本 ====================

HELP_TEXTS = {
    'min_followers': "开发者的最小粉丝数量（商业开发者）",
    'min_stars': "所有原创仓库的总stars数（商业开发者）",
    'academic_min_followers': "学术人士的最小粉丝数量",
    'academic_min_stars': "学术人士的最小总stars数",
    'core_ai_keywords': "这些关键词用于判断项目是否与多模态应用相关，包括：图像生成、视频生成、多模态模型、3D生成等",
    'exclusion_companies': "Company字段包含这些名称的开发者将被过滤",
    'exclusion_projects': "Bio或Company中标注为这些项目成员的开发者将被过滤",
    'exclusion_developers': "已爬取过的开发者用户名列表，避免重复爬取浪费资源（适用于数据库被删除后重新爬取的场景）",
    'academic_keywords': "用于识别学术人士的关键词，检查Bio/Company/Location字段",
    'research_project_keywords': "用于识别研究项目的关键词，检查仓库名称和描述"
}

# ==================== 标签 ====================

LABELS = {
    'rules_title': '🎯 GitHub 筛选规则',
    'rules_info': '💡 配置GitHub独立开发者筛选规则',
    'indie_developer_criteria': '📊 独立开发者判断标准',
    'screening_params': '🎯 筛选参数',
    'ai_keywords': '🔑 AI项目识别关键词',
    'exclusion_companies': '🏢 排除的公司/组织',
    'exclusion_projects': '🚫 排除的项目团队',
    'exclusion_developers': '🚫 已爬取开发者黑名单',
    'save_config': '💾 保存配置',
    'config_saved': '✅ 配置已保存！新配置将在下次爬虫任务时生效',
    'config_save_failed': '❌ 保存失败',
    'crawler_title': '🚀 GitHub 爬虫控制',
    'dashboard_title': '📊 GitHub 数据概览'
}

CAPTIONS = {
    'core_keywords': '用于识别AI相关项目的核心关键词（匹配任意一个即可）',
    'exclusion_companies': '在这些公司工作的开发者将被排除',
    'exclusion_projects': '这些项目的团队成员将被排除',
    'exclusion_developers': '⚠️ 已爬取过的开发者用户名（每行一个），爬虫会自动跳过这些用户，避免重复爬取',
    'academic_keywords': '用于识别学术人士的关键词（检查Profile信息）',
    'research_project_keywords': '用于识别研究项目的关键词（检查仓库信息）'
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
    if max_developers <= 20:
        return "约1-2分钟"
    elif max_developers <= 50:
        return "约3-5分钟"
    elif max_developers <= 100:
        return "约8-12分钟"
    elif max_developers <= 200:
        return "约15-25分钟"
    elif max_developers <= 300:
        return "约25-35分钟"
    else:
        return "约35-50分钟"
