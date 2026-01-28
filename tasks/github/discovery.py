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
        运行发现任务 - 循环爬取直到达到目标合格数量
        
        Args:
            max_developers: 目标合格开发者数量
            strategy: 搜索策略
        """
        logger.info("=" * 60)
        logger.info("开始GitHub开发者发现任务")
        logger.info(f"目标合格数量: {max_developers} 个开发者")
        logger.info(f"搜索策略: {strategy}")
        logger.info("使用网页爬虫（无API速率限制）")
        logger.info("=" * 60)
        
        qualified_count = 0
        total_discovered = 0
        total_processed = 0
        skipped_existing = 0
        rejected_count = 0
        batch_number = 0
        
        # 最多尝试次数（避免无限循环）
        max_attempts = max_developers * 10
        
        while qualified_count < max_developers and total_discovered < max_attempts:
            batch_number += 1
            
            # 计算本批次需要爬取的数量
            # 根据当前合格率动态调整，初始按3倍，后续根据实际合格率调整
            remaining = max_developers - qualified_count
            if total_processed > 0:
                current_rate = qualified_count / total_processed
                if current_rate > 0:
                    # 根据合格率预估需要的数量，再加50%缓冲
                    batch_size = int(remaining / current_rate * 1.5)
                else:
                    batch_size = remaining * 5
            else:
                # 首次按3倍爬取
                batch_size = remaining * 3
            
            # 限制单批次最大数量
            batch_size = min(batch_size, 50)
            batch_size = max(batch_size, 10)  # 至少10个
            
            logger.info(f"\n{'='*60}")
            logger.info(f"第 {batch_number} 批次: 目标爬取 {batch_size} 个开发者")
            logger.info(f"当前进度: {qualified_count}/{max_developers} 合格")
            logger.info(f"{'='*60}")
            
            # 使用指定策略发现开发者
            developers = self.searcher.discover_developers(
                strategy=strategy,
                limit=batch_size
            )
            
            if not developers:
                logger.warning("本批次未发现新开发者，可能已搜索完所有结果")
                break
            
            total_discovered += len(developers)
            logger.info(f"本批次发现 {len(developers)} 个开发者，开始逐个分析...")
            
            # 分析并保存
            for i, username in enumerate(developers, 1):
                # 检查是否已达到目标
                if qualified_count >= max_developers:
                    logger.info(f"\n✓ 已达到目标数量 {max_developers}，停止爬取")
                    break
                
                logger.info(f"\n[批次{batch_number}-{i}/{len(developers)}] [总进度: {qualified_count}/{max_developers}] 处理: {username}")
                
                # 检查是否已存在
                if self.repository.developer_exists(username):
                    logger.info(f"  ⊙ 开发者已存在数据库，跳过")
                    skipped_existing += 1
                    continue
                
                total_processed += 1
                
                # 分析开发者
                result = self.analyzer.analyze_developer(username)
                
                if not result:
                    logger.warning(f"  ✗ 分析失败")
                    rejected_count += 1
                    continue
                
                # 保存到数据库
                result['discovered_from'] = f'{strategy}_search'
                self.repository.save_developer(result)
                
                if result.get('is_indie_developer'):
                    qualified_count += 1
                    logger.info(f"  ✓ 合格 [{qualified_count}/{max_developers}]")
                    logger.info(f"    - Followers: {result.get('followers', 0)}")
                    logger.info(f"    - 公开仓库: {result.get('public_repos', 0)}")
                    logger.info(f"    - 总Stars: {result.get('total_stars', 0)}")
                    logger.info(f"    - 联系方式: {result.get('contact_info', '无')}")
                else:
                    rejected_count += 1
                    logger.info(f"  ✗ 不合格（不符合独立开发者标准）")
            
            # 批次总结
            logger.info(f"\n批次 {batch_number} 完成:")
            logger.info(f"  - 发现: {len(developers)} 个")
            logger.info(f"  - 已存在: {skipped_existing} 个")
            logger.info(f"  - 当前合格: {qualified_count}/{max_developers}")
            
            if total_processed > 0:
                current_rate = qualified_count / total_processed * 100
                logger.info(f"  - 当前合格率: {current_rate:.1f}%")
        
        # 最终统计
        logger.info("\n" + "=" * 60)
        logger.info("发现任务完成")
        logger.info("=" * 60)
        logger.info(f"目标数量: {max_developers} 个合格开发者")
        logger.info(f"实际合格: {qualified_count} 个")
        logger.info(f"总共发现: {total_discovered} 个开发者")
        logger.info(f"已存在跳过: {skipped_existing} 个")
        logger.info(f"实际分析: {total_processed} 个")
        logger.info(f"不合格: {rejected_count} 个")
        if total_processed > 0:
            logger.info(f"合格率: {qualified_count/total_processed*100:.1f}%")
        logger.info(f"批次数: {batch_number}")
        
        if qualified_count < max_developers:
            logger.warning(f"\n⚠️ 未达到目标数量（{qualified_count}/{max_developers}）")
            logger.warning(f"可能原因: 搜索策略已穷尽，或合格率过低")
            logger.warning(f"建议: 尝试其他搜索策略或调整筛选标准")
        else:
            logger.info(f"\n✓ 成功达到目标: {qualified_count} 个合格开发者")
        
        logger.info("=" * 60)
