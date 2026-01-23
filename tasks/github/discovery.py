# -*- coding: utf-8 -*-
"""
GitHub开发者发现任务
"""
from typing import List
from utils.logger import setup_logger
from platforms.github import GitHubPlatform

logger = setup_logger()


class GitHubDiscoveryTask:
    """GitHub开发者发现任务"""
    
    def __init__(self, searcher, analyzer, repository):
        self.searcher = searcher
        self.analyzer = analyzer
        self.repository = repository
    
    def run(self, max_developers: int = 50, strategy: str = 'comprehensive'):
        """
        运行发现任务 - 使用可配置策略
        
        Args:
            max_developers: 最大开发者数量
            strategy: 搜索策略
        """
        logger.info("=" * 60)
        logger.info("开始GitHub开发者发现任务")
        logger.info(f"目标数量: {max_developers} 个开发者")
        logger.info(f"搜索策略: {strategy}")
        logger.info("使用网页爬虫（无API速率限制）")
        logger.info("=" * 60)
        
        # 使用指定策略发现开发者
        developers = self.searcher.discover_developers(
            strategy=strategy,
            limit=max_developers
        )
        
        logger.info(f"发现 {len(developers)} 个开发者，开始分析...")
        
        # 分析并保存
        qualified_count = 0
        processed_count = 0
        
        for i, username in enumerate(developers, 1):
            logger.info(f"\n[{i}/{len(developers)}] 处理开发者: {username}")
            
            # 检查是否已存在
            if self.repository.developer_exists(username):
                logger.info(f"开发者 {username} 已存在，跳过")
                continue
            
            processed_count += 1
            
            # 分析开发者
            result = self.analyzer.analyze_developer(username)
            
            if not result:
                logger.warning(f"分析开发者 {username} 失败")
                continue
            
            # 保存到数据库
            result['discovered_from'] = f'{strategy}_search'
            self.repository.save_developer(result)
            
            if result.get('is_indie_developer'):
                qualified_count += 1
                logger.info(f"✓ 合格的独立开发者: {username}")
                logger.info(f"  - Followers: {result.get('followers', 0)}")
                logger.info(f"  - 公开仓库: {result.get('public_repos', 0)}")
                logger.info(f"  - 总Stars: {result.get('total_stars', 0)}")
            else:
                logger.info(f"✗ 不符合独立开发者标准: {username}")
        
        logger.info("=" * 60)
        logger.info(f"发现任务完成")
        logger.info(f"总共发现: {len(developers)} 个开发者")
        logger.info(f"实际处理: {processed_count} 个（排除已存在）")
        logger.info(f"合格开发者: {qualified_count} 个")
        logger.info(f"合格率: {qualified_count/processed_count*100:.1f}%" if processed_count > 0 else "合格率: 0%")
        logger.info("=" * 60)
