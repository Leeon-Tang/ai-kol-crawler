# -*- coding: utf-8 -*-
"""
GitHub规则配置页面
"""
import streamlit as st
import json
import os
from .texts import (
    INDIE_DEVELOPER_EXPLANATION,
    KEYWORDS_EXPLANATION,
    DEFAULT_CONFIG,
    HELP_TEXTS,
    LABELS,
    CAPTIONS
)


def render(project_root: str, add_log_func):
    """
    渲染GitHub规则配置页面
    
    Args:
        project_root: 项目根目录
        add_log_func: 日志记录函数
    """
    st.markdown(f'<div class="main-header">{LABELS["rules_title"]}</div>', unsafe_allow_html=True)
    st.info('💡 配置GitHub开发者筛选规则（自动分类为商业开发者或学术人士）')
    
    config_path = os.path.join(project_root, 'config', 'config.json')
    
    if not os.path.exists(config_path):
        st.error("❌ 配置文件不存在")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        st.error(f"❌ 读取配置文件失败: {e}")
        return
    
    # 如果配置中没有github部分，创建默认配置
    if 'github' not in config:
        config['github'] = DEFAULT_CONFIG.copy()
    
    # 确保有所有必要的字段
    if 'core_ai_keywords' not in config['github']:
        config['github']['core_ai_keywords'] = DEFAULT_CONFIG['core_ai_keywords'].copy()
    if 'exclusion_developers' not in config['github']:
        config['github']['exclusion_developers'] = []
    if 'academic_keywords' not in config['github']:
        config['github']['academic_keywords'] = DEFAULT_CONFIG['academic_keywords'].copy()
    if 'research_project_keywords' not in config['github']:
        config['github']['research_project_keywords'] = DEFAULT_CONFIG['research_project_keywords'].copy()
    
    # 使用容器限制宽度
    with st.container():
        # 使用标签页组织配置
        tab1, tab2, tab3, tab4 = st.tabs([
            "💼 商业开发者规则",
            "🎓 学术人士规则", 
            "🔍 搜索配置",
            "🚫 排除规则"
        ])
    
    # ==================== 标签1: 商业开发者规则 ====================
    with tab1:
        st.subheader("📊 独立开发者判断标准")
        
        st.info("""
        **独立开发者必须同时满足以下条件：**
        
        1. **不属于大公司** - 不在Google、Microsoft、Meta等大公司工作
        2. **不是项目成员** - 不是ComfyUI、Automatic1111等知名项目的团队成员
        3. **有影响力** - Followers或总Stars达到配置的阈值
        4. **有AI项目** - 至少有1个AI相关的原创项目
        
        **排除规则：**
        - Bio或Company中标注为某项目成员（如"ComfyUI team member"）
        """)
        
        st.divider()
        
        st.subheader("🎯 筛选参数")
        st.caption("用于判断开发者是否符合独立开发者标准")
        
        col1, col2 = st.columns(2)
        
        with col1:
            min_followers = st.number_input(
                "最小Followers数", 
                min_value=0, max_value=10000,
                value=config['github'].get('min_followers', 100), 
                step=50,
                help=HELP_TEXTS['min_followers'],
                key="commercial_min_followers"
            )
        
        with col2:
            min_stars = st.number_input(
                "最小总Stars数", 
                min_value=0, max_value=50000,
                value=config['github'].get('min_stars', 500), 
                step=100,
                help=HELP_TEXTS['min_stars'],
                key="commercial_min_stars"
            )
        
        st.info(f"📊 当前规则：Followers ≥ {min_followers} 或 总Stars ≥ {min_stars}")
        
        st.divider()
        
        st.subheader("🔑 多模态应用识别关键词")
        st.caption("用于判断开发者的项目是否与多模态应用相关")
        
        core_ai_keywords = st.text_area(
            "多模态应用判断关键词（每行一个）",
            value="\n".join(config['github'].get('core_ai_keywords', [])),
            height=300,
            help=HELP_TEXTS['core_ai_keywords'],
            key="commercial_core_keywords"
        )
        
        core_kw_count = len([k for k in core_ai_keywords.split('\n') if k.strip()])
        st.info(f"📊 当前配置了 {core_kw_count} 个多模态应用识别关键词")
        
        st.divider()
        
        st.subheader("💡 关键词说明")
        st.info(KEYWORDS_EXPLANATION)
    
    # ==================== 标签2: 学术人士规则 ====================
    with tab2:
        st.subheader("🎓 学术人士识别规则")
        
        st.info("""
        **学术人士自动识别条件：**
        
        1. **Profile包含学术关键词** - Bio/Company/Location中包含大学、研究所等关键词
        2. **有研究项目** - 至少2个项目包含论文、实验、研究等关键词
        3. **自动分类** - 符合条件的开发者会自动保存到学术人士表
        
        **与商业开发者的区别：**
        - 学术人士：专注于研究、论文复现、模型训练
        - 商业开发者：专注于应用开发、产品、工具
        """)
        
        st.divider()
        
        st.subheader("🎯 筛选参数")
        st.caption("用于判断学术人士是否符合标准")
        
        col1, col2 = st.columns(2)
        
        with col1:
            academic_min_followers = st.number_input(
                "最小Followers数", 
                min_value=0, max_value=10000,
                value=config['github'].get('academic_min_followers', 50), 
                step=50,
                help="学术人士的最小Followers数要求",
                key="academic_min_followers"
            )
        
        with col2:
            academic_min_stars = st.number_input(
                "最小总Stars数", 
                min_value=0, max_value=50000,
                value=config['github'].get('academic_min_stars', 100), 
                step=100,
                help="学术人士的最小总Stars数要求",
                key="academic_min_stars"
            )
        
        st.info(f"📊 当前规则：Followers ≥ {academic_min_followers} 或 总Stars ≥ {academic_min_stars}")
        
        st.divider()
        
        st.subheader("🏫 学术机构关键词")
        st.caption(CAPTIONS['academic_keywords'])
        
        academic_keywords = st.text_area(
            "学术机构关键词（每行一个）",
            value="\n".join(config['github'].get('academic_keywords', DEFAULT_CONFIG['academic_keywords'])),
            height=200,
            help=HELP_TEXTS['academic_keywords'],
            key="academic_keywords_input"
        )
        
        academic_kw_count = len([k for k in academic_keywords.split('\n') if k.strip()])
        st.info(f"📊 当前配置了 {academic_kw_count} 个学术关键词")
        
        st.divider()
        
        st.subheader("📚 研究项目关键词")
        st.caption(CAPTIONS['research_project_keywords'])
        
        research_project_keywords = st.text_area(
            "研究项目关键词（每行一个）",
            value="\n".join(config['github'].get('research_project_keywords', DEFAULT_CONFIG['research_project_keywords'])),
            height=200,
            help=HELP_TEXTS['research_project_keywords'],
            key="research_keywords_input"
        )
        
        research_kw_count = len([k for k in research_project_keywords.split('\n') if k.strip()])
        st.info(f"📊 当前配置了 {research_kw_count} 个研究关键词")
    
    # ==================== 标签3: 搜索配置 ====================
    with tab3:
        st.subheader("⚙️ 爬取控制参数")
        st.caption("控制爬虫的运行行为和停止条件")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_developers_per_run = st.number_input(
                "每次运行最大开发者数量", 
                min_value=10, max_value=1000,
                value=config['github'].get('max_developers_per_run', 100), 
                step=10,
                help="每次运行爬虫时，最多爬取多少个合格的商业开发者。达到这个数量后会自动停止。",
                key="max_developers_per_run"
            )
        
        with col2:
            min_repo_stars = st.number_input(
                "仓库最低星标要求", 
                min_value=0, max_value=1000,
                value=config['github'].get('min_repo_stars', 100), 
                step=10,
                help="只爬取星标数大于等于此值的仓库的贡献者。星标越高，项目质量越好，但可能会减少候选者数量。",
                key="min_repo_stars"
            )
        
        st.info(f"📊 当前规则：每次最多爬取 {max_developers_per_run} 个开发者，只爬取 ≥ {min_repo_stars} 星的仓库")
        
        st.divider()
        
        st.subheader("🔍 搜索项目关键词")
        st.caption("用于搜索GitHub项目的关键词（包括普通项目、awesome列表等）")
        
        search_keywords = st.text_area(
            "搜索关键词（每行一个）",
            value="\n".join(config['github'].get('search_keywords', DEFAULT_CONFIG.get('search_keywords', []))),
            height=300,
            help="这些关键词用于在GitHub上搜索相关项目，从而发现开发者。支持：\n- 普通关键词: stable diffusion, ComfyUI, AI tool\n- Awesome项目: awesome-generative-ai, awesome-stable-diffusion",
            key="search_keywords_input"
        )
        
        st.info("💡 支持搜索普通项目和awesome列表，爬取项目owner和贡献者")
        search_kw_count = len([k for k in search_keywords.split('\n') if k.strip()])
        st.info(f"📊 当前配置了 {search_kw_count} 个搜索关键词")
    
    # ==================== 标签4: 排除规则 ====================
    with tab4:
        st.markdown("### 🏢 排除的公司/组织和项目团队")
        st.caption("在这些公司工作或项目团队的开发者将被排除")
        
        # 从github.exclusion_organizations读取
        existing_orgs = config['github'].get('exclusion_organizations', [])
        
        exclusion_orgs = st.text_area(
            "公司/组织/项目名称（每行一个）",
            value="\n".join(existing_orgs),
            height=300,
            help="包括：大公司（Google, Microsoft等）、知名项目团队（ComfyUI, Automatic1111等）",
            key="exclusion_orgs_input"
        )
        
        exclusion_orgs_count = len([k for k in exclusion_orgs.split('\n') if k.strip()])
        st.info(f"📊 当前配置了 {exclusion_orgs_count} 个排除项")
        
        st.divider()
        
        st.markdown("### 🚫 已爬取开发者黑名单")
        st.caption(CAPTIONS['exclusion_developers'])
        
        with st.expander("💡 使用说明", expanded=False):
            st.markdown("""
            **适用场景：**
            - 数据库被误删，需要重新爬取
            - 想避免重复爬取已经联系过的开发者
            
            **使用方法：**
            1. 将已爬取过的开发者用户名粘贴到下方文本框
            2. 每行一个用户名（如：torvalds）
            3. 保存配置后，爬虫会自动跳过这些用户
            
            **注意：**
            - 只需要填写GitHub用户名，不需要完整URL
            - 大小写不敏感（会自动转为小写）
            - 空行会被自动忽略
            """)
        
        exclusion_developers = st.text_area(
            "开发者用户名（每行一个）",
            value="\n".join(config['github'].get('exclusion_developers', [])),
            height=200,
            help=HELP_TEXTS['exclusion_developers'],
            placeholder="例如：\ntorvalds\nguido\ngvanrossum",
            key="exclusion_developers_input"
        )
        
        exclusion_dev_list = [d.strip().lower() for d in exclusion_developers.split('\n') if d.strip()]
        if exclusion_dev_list:
            st.info(f"📊 当前黑名单中有 {len(exclusion_dev_list)} 个开发者")
    
    st.divider()
    
    # 保存按钮
    if st.button(LABELS["save_config"], type="primary", use_container_width=True):
        # 收集所有配置
        config['github']['min_followers'] = min_followers
        config['github']['min_stars'] = min_stars
        
        # 学术人士参数
        config['github']['academic_min_followers'] = academic_min_followers
        config['github']['academic_min_stars'] = academic_min_stars
        
        # 爬取控制参数
        config['github']['max_developers_per_run'] = max_developers_per_run
        config['github']['min_repo_stars'] = min_repo_stars
        
        # 处理搜索关键词
        search_kw_list = [k.strip() for k in search_keywords.split('\n') if k.strip()]
        config['github']['search_keywords'] = search_kw_list
        
        # 处理AI判断关键词
        core_kw_list = [k.strip() for k in core_ai_keywords.split('\n') if k.strip()]
        config['github']['core_ai_keywords'] = core_kw_list
        
        # 处理学术关键词
        academic_kw_list = [k.strip() for k in academic_keywords.split('\n') if k.strip()]
        config['github']['academic_keywords'] = academic_kw_list
        
        research_kw_list = [k.strip() for k in research_project_keywords.split('\n') if k.strip()]
        config['github']['research_project_keywords'] = research_kw_list
        
        # 处理排除规则
        exclusion_orgs_list = [k.strip() for k in exclusion_orgs.split('\n') if k.strip()]
        config['github']['exclusion_organizations'] = exclusion_orgs_list
        
        # 保存开发者黑名单（转为小写）
        exclusion_dev_list = [k.strip().lower() for k in exclusion_developers.split('\n') if k.strip()]
        config['github']['exclusion_developers'] = exclusion_dev_list
        
        # 清理旧字段
        old_fields = ['search_topics', 'awesome_search_keywords', 'helper_keywords', 'keywords', 'min_repos', 'exclusion_companies', 'exclusion_projects']
        for field in old_fields:
            if field in config['github']:
                del config['github'][field]
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 显示详细的保存结果
            st.success("✅ " + LABELS["config_saved"])
            
            # 显示保存的内容统计
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("搜索关键词", len(search_kw_list))
            with col2:
                st.metric("AI判断关键词", len(core_kw_list))
            with col3:
                st.metric("学术关键词", len(academic_kw_list))
            with col4:
                st.metric("研究关键词", len(research_kw_list))
            
            # 显示其他统计
            st.info(f"📊 排除组织/项目: {len(exclusion_orgs_list)} 个 | 开发者黑名单: {len(exclusion_dev_list)} 个")
            
            add_log_func("GitHub筛选规则配置已更新", "INFO")
            add_log_func(f"  - 商业开发者: 搜索{len(search_kw_list)}个关键词, AI判断{len(core_kw_list)}个关键词", "INFO")
            add_log_func(f"  - 学术人士: 学术{len(academic_kw_list)}个关键词, 研究{len(research_kw_list)}个关键词", "INFO")
            add_log_func(f"  - 排除规则: 组织/项目{len(exclusion_orgs_list)}个, 黑名单{len(exclusion_dev_list)}个", "INFO")
            
        except Exception as e:
            st.error(f"❌ {LABELS['config_save_failed']}: {e}")
            import traceback
            st.code(traceback.format_exc())
