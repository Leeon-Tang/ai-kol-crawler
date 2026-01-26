# -*- coding: utf-8 -*-
"""
YouTube AI规则配置页面
"""
import streamlit as st
import json
import os
import shutil
from .texts import LABELS, HELP_TEXTS


def render(project_root: str, add_log_func):
    """
    渲染YouTube AI规则配置页面
    
    Args:
        project_root: 项目根目录
        add_log_func: 日志记录函数
    """
    st.markdown(f'<div class="main-header">{LABELS["rules_title"]}</div>', unsafe_allow_html=True)
    st.info(LABELS["rules_info"])
    
    config_path = os.path.join(project_root, 'config', 'config.json')
    config_example_path = os.path.join(project_root, 'config', 'config.example.json')
    
    if not os.path.exists(config_path):
        if os.path.exists(config_example_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            shutil.copy(config_example_path, config_path)
            st.success("✅ 已自动创建配置文件")
        else:
            st.error("❌ 配置文件不存在")
            return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        st.error(f"❌ 读取配置文件失败: {e}")
        return
    
    # 基础筛选参数
    st.subheader(LABELS["basic_params"])
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ai_ratio_percentage = st.slider(
            "AI占比阈值", 
            min_value=0, 
            max_value=100,
            value=int(config['crawler']['ai_ratio_threshold'] * 100),
            step=5, 
            format="%d%%",
            help=HELP_TEXTS['ai_ratio']
        )
        ai_ratio_threshold = ai_ratio_percentage / 100.0
    
    with col2:
        sample_video_count = st.number_input(
            "分析视频数", 
            min_value=5, 
            max_value=50,
            value=config['crawler']['sample_video_count'], 
            step=5,
            help=HELP_TEXTS['sample_video_count']
        )
    
    with col3:
        active_days_threshold = st.number_input(
            "活跃度阈值(天)", 
            min_value=30, 
            max_value=365,
            value=config['crawler']['active_days_threshold'], 
            step=30,
            help=HELP_TEXTS['active_days']
        )
    
    st.divider()
    
    # AI关键词库
    st.subheader(LABELS["ai_keywords"])
    tab1, tab2, tab3 = st.tabs([
        LABELS["high_priority_tab"], 
        LABELS["medium_priority_tab"], 
        LABELS["low_priority_tab"]
    ])
    
    with tab1:
        high_keywords = st.text_area(
            "高优先级关键词（每行一个）",
            value="\n".join(config['keywords']['priority_high']),
            height=200,
            help=HELP_TEXTS['high_keywords']
        )
    
    with tab2:
        medium_keywords = st.text_area(
            "中优先级关键词（每行一个）",
            value="\n".join(config['keywords']['priority_medium']),
            height=200,
            help=HELP_TEXTS['medium_keywords']
        )
    
    with tab3:
        low_keywords = st.text_area(
            "低优先级关键词（每行一个）",
            value="\n".join(config['keywords']['priority_low']),
            height=200,
            help=HELP_TEXTS['low_keywords']
        )
    
    st.divider()
    
    # 排除规则
    st.subheader(LABELS["exclusion_rules"])
    all_exclusion_keywords = []
    all_exclusion_keywords.extend(config['exclusion_rules'].get('course_keywords', []))
    all_exclusion_keywords.extend(config['exclusion_rules'].get('academic_keywords', []))
    all_exclusion_keywords.extend(config['exclusion_rules'].get('news_keywords', []))
    
    exclusion_keywords = st.text_area(
        "排除关键词（每行一个）", 
        value="\n".join(all_exclusion_keywords),
        height=200,
        help=HELP_TEXTS['exclusion_keywords']
    )
    
    # 保存按钮
    if st.button(LABELS["save_config"], type="primary", use_container_width=True):
        config['crawler']['ai_ratio_threshold'] = ai_ratio_threshold
        config['crawler']['sample_video_count'] = sample_video_count
        config['crawler']['active_days_threshold'] = active_days_threshold
        
        config['keywords']['priority_high'] = [k.strip() for k in high_keywords.split('\n') if k.strip()]
        config['keywords']['priority_medium'] = [k.strip() for k in medium_keywords.split('\n') if k.strip()]
        config['keywords']['priority_low'] = [k.strip() for k in low_keywords.split('\n') if k.strip()]
        
        exclusion_list = [k.strip() for k in exclusion_keywords.split('\n') if k.strip()]
        config['exclusion_rules']['course_keywords'] = exclusion_list
        config['exclusion_rules']['academic_keywords'] = []
        config['exclusion_rules']['news_keywords'] = []
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            st.success(LABELS["config_saved"])
            add_log_func("YouTube AI规则配置已更新", "INFO")
        except Exception as e:
            st.error(f"{LABELS['config_save_failed']}: {e}")
