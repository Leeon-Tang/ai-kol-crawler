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
    st.info(LABELS["rules_info"])
    
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
    
    # 兼容旧配置：如果有keywords字段但没有core_ai_keywords，使用默认值而不是迁移
    if 'core_ai_keywords' not in config['github']:
        # 使用完整的默认关键词列表
        config['github']['core_ai_keywords'] = DEFAULT_CONFIG['core_ai_keywords'].copy()
    
    # 确保有helper_keywords
    if 'helper_keywords' not in config['github']:
        config['github']['helper_keywords'] = DEFAULT_CONFIG['helper_keywords'].copy()
    
    # 确保有exclusion_developers（新增）
    if 'exclusion_developers' not in config['github']:
        config['github']['exclusion_developers'] = []
    
    # 渲染独立开发者判断标准
    st.subheader(LABELS["indie_developer_criteria"])
    with st.expander("ℹ️ 什么是独立开发者？", expanded=True):
        st.markdown(INDIE_DEVELOPER_EXPLANATION)
    
    st.divider()
    
    # 渲染筛选参数
    st.subheader(LABELS["screening_params"])
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_followers = st.number_input(
            "最小Followers数", 
            min_value=0, max_value=10000,
            value=config['github'].get('min_followers', 100), 
            step=50,
            help=HELP_TEXTS['min_followers']
        )
    
    with col2:
        min_stars = st.number_input(
            "最小总Stars数", 
            min_value=0, max_value=50000,
            value=config['github'].get('min_stars', 500), 
            step=100,
            help=HELP_TEXTS['min_stars']
        )
    
    with col3:
        min_repos = st.number_input(
            "最小原创仓库数", 
            min_value=1, max_value=100,
            value=config['github'].get('min_repos', 3), 
            step=1,
            help=HELP_TEXTS['min_repos']
        )
    
    st.divider()
    
    # 渲染AI关键词配置
    st.subheader(LABELS["ai_keywords"])
    
    tab1, tab2 = st.tabs(["🔍 搜索项目关键词", "✅ 判断AI项目关键词"])
    
    with tab1:
        st.caption("用于搜索GitHub项目的关键词（包括普通项目、awesome列表等）")
        search_keywords = st.text_area(
            "搜索关键词（每行一个）",
            value="\n".join(config['github'].get('search_keywords', DEFAULT_CONFIG.get('search_keywords', []))),
            height=400,
            help="这些关键词用于在GitHub上搜索相关项目，从而发现开发者。支持：\n- 普通关键词: stable diffusion, ComfyUI, AI tool\n- Awesome项目: awesome-generative-ai, awesome-stable-diffusion"
        )
        st.info("💡 支持搜索普通项目和awesome列表，爬取项目owner和贡献者")
    
    with tab2:
        st.caption("用于判断开发者的项目是否与AI相关")
        core_ai_keywords = st.text_area(
            "AI项目判断关键词（每行一个）",
            value="\n".join(config['github'].get('core_ai_keywords', [])),
            height=400,
            help=HELP_TEXTS['core_ai_keywords']
        )
        
        with st.expander("💡 关键词说明", expanded=False):
            st.markdown(KEYWORDS_EXPLANATION)
    
    st.divider()
    
    # 渲染排除规则
    st.subheader(LABELS["exclusion_companies"])
    st.caption(CAPTIONS['exclusion_companies'])
    
    exclusion_companies = st.text_area(
        "公司名称（每行一个）",
        value="\n".join(config['github'].get('exclusion_companies', [])),
        height=200,
        help=HELP_TEXTS['exclusion_companies']
    )
    
    st.divider()
    
    st.subheader(LABELS["exclusion_projects"])
    st.caption(CAPTIONS['exclusion_projects'])
    
    exclusion_projects = st.text_area(
        "项目名称（每行一个）",
        value="\n".join(config['github'].get('exclusion_projects', [])),
        height=150,
        help=HELP_TEXTS['exclusion_projects']
    )
    
    st.divider()
    
    # 新增：已爬取开发者黑名单
    st.subheader(LABELS["exclusion_developers"])
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
        placeholder="例如：\ntorvalds\nguido\ngvanrossum"
    )
    
    # 显示统计
    exclusion_dev_list = [d.strip().lower() for d in exclusion_developers.split('\n') if d.strip()]
    if exclusion_dev_list:
        st.info(f"📊 当前黑名单中有 {len(exclusion_dev_list)} 个开发者")
    
    st.divider()
    
    # 保存按钮
    if st.button(LABELS["save_config"], type="primary", use_container_width=True):
        # 收集所有配置
        config['github']['min_followers'] = min_followers
        config['github']['min_stars'] = min_stars
        config['github']['min_repos'] = min_repos
        
        # 处理搜索关键词
        search_kw_list = [k.strip() for k in search_keywords.split('\n') if k.strip()]
        config['github']['search_keywords'] = search_kw_list
        
        # 处理AI判断关键词
        core_kw_list = [k.strip() for k in core_ai_keywords.split('\n') if k.strip()]
        config['github']['core_ai_keywords'] = core_kw_list
        
        # 处理排除规则
        exclusion_companies_list = [k.strip() for k in exclusion_companies.split('\n') if k.strip()]
        config['github']['exclusion_companies'] = exclusion_companies_list
        
        exclusion_projects_list = [k.strip() for k in exclusion_projects.split('\n') if k.strip()]
        config['github']['exclusion_projects'] = exclusion_projects_list
        
        # 保存开发者黑名单（转为小写）
        exclusion_dev_list = [k.strip().lower() for k in exclusion_developers.split('\n') if k.strip()]
        config['github']['exclusion_developers'] = exclusion_dev_list
        
        # 清理旧字段
        old_fields = ['search_topics', 'awesome_search_keywords', 'helper_keywords', 'keywords']
        for field in old_fields:
            if field in config['github']:
                del config['github'][field]
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 显示详细的保存结果
            st.success("✅ " + LABELS["config_saved"])
            
            # 显示保存的内容统计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("搜索关键词", len(search_kw_list))
            with col2:
                st.metric("AI判断关键词", len(core_kw_list))
            with col3:
                st.metric("开发者黑名单", len(exclusion_dev_list))
            
            # 显示其他统计
            st.info(f"📊 排除公司: {len(exclusion_companies_list)} 个 | 排除项目: {len(exclusion_projects_list)} 个")
            
            add_log_func("GitHub筛选规则配置已更新", "INFO")
            add_log_func(f"  - 搜索关键词: {len(search_kw_list)} 个", "INFO")
            add_log_func(f"  - AI判断关键词: {len(core_kw_list)} 个", "INFO")
            add_log_func(f"  - 开发者黑名单: {len(exclusion_dev_list)} 个", "INFO")
            
        except Exception as e:
            st.error(f"❌ {LABELS['config_save_failed']}: {e}")
            import traceback
            st.code(traceback.format_exc())
