# -*- coding: utf-8 -*-
"""
Twitter数据导出任务
"""
import os
import json
from datetime import datetime
from typing import List, Dict
import pandas as pd
from utils.logger import setup_logger
from utils.config_loader import get_project_root
from storage.database import Database
from storage.repositories.twitter_repository import TwitterRepository

logger = setup_logger(__name__)


class TwitterExportTask:
    """Twitter数据导出任务"""
    
    def __init__(self):
        self.db = Database()
        self.db.connect()
        self.repository = TwitterRepository(self.db)
        
        # 导出目录
        self.project_root = get_project_root()
        self.export_dir = os.path.join(self.project_root, 'exports')
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_qualified_users(self, limit: int = 1000) -> str:
        """
        导出合格用户到Excel
        
        Args:
            limit: 导出数量限制
            
        Returns:
            导出文件路径
        """
        logger.info(f"开始导出合格用户，限制: {limit}")
        
        # 获取合格用户
        users = self.repository.get_qualified_users(limit=limit)
        
        if not users:
            logger.warning("没有合格用户可导出")
            return ""
        
        # 转换为DataFrame
        df_data = []
        for user in users:
            # 解析matched_keywords
            try:
                matched_keywords = json.loads(user.get('matched_keywords', '[]'))
                keywords_str = ', '.join(matched_keywords) if matched_keywords else ''
            except:
                keywords_str = ''
            
            df_data.append({
                '用户名': f"@{user['username']}",
                '姓名': user.get('name', ''),
                '简介': user.get('bio', ''),
                '粉丝数': user.get('followers_count', 0),
                '推文数': user.get('tweet_count', 0),
                'AI相关度': f"{user.get('ai_ratio', 0) * 100:.1f}%",
                '质量分数': f"{user.get('quality_score', 0):.1f}",
                '平均互动': f"{user.get('avg_engagement', 0):.1f}",
                '原创率': f"{user.get('original_ratio', 0) * 100:.1f}%",
                '认证状态': '已认证' if user.get('verified') else ('蓝V' if user.get('is_blue_verified') else '未认证'),
                '匹配关键词': keywords_str,
                '联系方式': user.get('contact_info', ''),
                '位置': user.get('location', ''),
                '网站': user.get('website', ''),
                '主页': user.get('profile_url', ''),
                '发现来源': user.get('discovered_from', ''),
                '发现时间': user.get('discovered_at', '')
            })
        
        df = pd.DataFrame(df_data)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"twitter_users_{timestamp}.xlsx"
        filepath = os.path.join(self.export_dir, filename)
        
        # 导出Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Twitter用户', index=False)
            
            # 调整列宽
            worksheet = writer.sheets['Twitter用户']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
        
        logger.info(f"导出完成: {filepath}, 共 {len(df)} 个用户")
        return filepath
    
    def export_all_users_csv(self) -> str:
        """
        导出所有用户到CSV
        
        Returns:
            导出文件路径
        """
        logger.info("开始导出所有用户到CSV")
        
        # 查询所有用户
        query = "SELECT * FROM twitter_users ORDER BY quality_score DESC"
        users = self.db.fetchall(query)
        
        if not users:
            logger.warning("没有用户可导出")
            return ""
        
        # 转换为DataFrame
        df = pd.DataFrame(users)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"twitter_users_all_{timestamp}.csv"
        filepath = os.path.join(self.export_dir, filename)
        
        # 导出CSV
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"导出完成: {filepath}, 共 {len(df)} 个用户")
        return filepath
    
    def export_statistics(self) -> Dict:
        """
        导出统计信息
        
        Returns:
            统计数据字典
        """
        stats = self.repository.get_statistics()
        
        # 添加更多统计
        # 平均质量分数
        result = self.db.fetchone(
            "SELECT AVG(quality_score) as avg_score FROM twitter_users WHERE status = 'qualified'"
        )
        stats['avg_quality_score'] = result['avg_score'] if result and result['avg_score'] else 0
        
        # 平均粉丝数
        result = self.db.fetchone(
            "SELECT AVG(followers_count) as avg_followers FROM twitter_users WHERE status = 'qualified'"
        )
        stats['avg_followers'] = result['avg_followers'] if result and result['avg_followers'] else 0
        
        # 平均AI相关度
        result = self.db.fetchone(
            "SELECT AVG(ai_ratio) as avg_ai_ratio FROM twitter_users WHERE status = 'qualified'"
        )
        stats['avg_ai_ratio'] = result['avg_ai_ratio'] if result and result['avg_ai_ratio'] else 0
        
        return stats
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'db'):
            self.db.close()
