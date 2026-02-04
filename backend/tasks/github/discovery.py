# -*- coding: utf-8 -*-
"""
GitHub开发者发现任务
"""
from typing import List
from backend.utils.logger import setup_logger
from backend.utils.config_loader import load_config
from backend.platforms.github import GitHubPlatform

logger = setup_logger()


class GitHubDiscoveryTask:
    """GitHub开发者发现任务"""
    
    def __init__(self, searcher, analyzer, repository, academic_repository=None):
        self.searcher = searcher
        self.analyzer = analyzer
        self.repository = repository  # 商业开发者仓库
        self.academic_repository = academic_repository  # 学术人士仓库
        self.config = load_config()
        self.exclusion_developers = self._load_exclusion_developers()
    
    def _load_exclusion_developers(self) -> set:
        """加载开发者黑名单"""
        github_config = self.config.get('github', {})
        exclusion_list = github_config.get('exclusion_developers', [])
        # 转为小写的set，方便快速查找
        exclusion_set = {username.lower() for username in exclusion_list if username}
        if exclusion_set:
            logger.info(f"已加载开发者黑名单: {len(exclusion_set)} 个")
        return exclusion_set
    
    def _is_in_exclusion_list(self, username: str) -> bool:
        """检查开发者是否在黑名单中"""
        return username.lower() in self.exclusion_developers
    
    def run(self, max_developers: int = 50):
        """
        运行发现任务 - 深度优先爬取直到达到目标合格数量
        
        策略：
        - 逐个仓库深度挖掘
        - 一个仓库的所有贡献者分析完才换下一个仓库
        - 自动分类为商业开发者或学术人士
        - 分别存储到不同的表
        
        Args:
            max_developers: 目标合格开发者数量（商业开发者）
        """
        logger.info("=" * 60)
        logger.info("开始GitHub开发者发现任务（深度优先策略 + 学术/商业分类）")
        logger.info(f"目标合格数量: {max_developers} 个商业开发者")
        logger.info("使用网页爬虫（无API速率限制）")
        if self.exclusion_developers:
            logger.info(f"黑名单: {len(self.exclusion_developers)} 个开发者将被跳过")
        logger.info("=" * 60)
        
        qualified_commercial_count = 0  # 合格的商业开发者
        qualified_academic_count = 0    # 合格的学术人士
        total_discovered = 0
        total_processed = 0
        skipped_existing = 0
        rejected_count = 0
        
        # 最多尝试次数（避免无限循环）
        max_attempts = max_developers * 10
        
        # 使用生成器逐个获取候选者
        for username, source_info in self.searcher.discover_developers_generator(
            target_qualified=max_developers,
            max_attempts=max_attempts
        ):
            # 检查停止标志
            from utils.crawler_status import should_stop
            if should_stop():
                logger.warning("\n⚠️ 检测到停止信号，正在停止爬虫...")
                logger.info(f"当前进度: 商业开发者 {qualified_commercial_count}/{max_developers}, 学术人士 {qualified_academic_count}")
                break
            
            # 检查是否已达到目标
            if qualified_commercial_count >= max_developers:
                logger.info(f"\n✓ 已达到目标数量 {max_developers}，停止爬取")
                break
            
            total_discovered += 1
            
            logger.info(f"\n{'▶'*30}")
            logger.info(f"[商业: {qualified_commercial_count}/{max_developers}] [学术: {qualified_academic_count}] [已发现: {total_discovered}]")
            logger.info(f"开发者: {username}")
            logger.info(f"来源: {source_info}")  # source_info 已包含仓库进度信息
            logger.info(f"{'▶'*30}")
            
            # 检查是否在黑名单中
            if self._is_in_exclusion_list(username):
                logger.info(f"  🚫 开发者在黑名单中，跳过")
                skipped_existing += 1
                continue
            
            # 再次检查停止标志（在分析前）
            from utils.crawler_status import should_stop
            if should_stop():
                logger.warning("\n⚠️ 检测到停止信号，立即停止")
                break
            
            # 检查是否已存在（检查两个表）
            exists_in_commercial = self.repository.developer_exists(username)
            exists_in_academic = self.academic_repository and self.academic_repository.academic_developer_exists(username)
            
            if exists_in_commercial or exists_in_academic:
                table_name = "商业开发者表" if exists_in_commercial else "学术人士表"
                logger.info(f"  ⊙ 开发者已存在于{table_name}，跳过")
                skipped_existing += 1
                continue
            
            total_processed += 1
            
            # 分析开发者（会自动分类）
            result = self.analyzer.analyze_developer(username)
            
            if not result:
                logger.warning(f"  ✗ 分析失败")
                rejected_count += 1
                continue
            
            # 根据类型保存到不同的表
            result['discovered_from'] = 'search'
            developer_type = result.get('developer_type', 'commercial')
            
            if developer_type == 'academic':
                # 保存到学术人士表
                if self.academic_repository:
                    self.academic_repository.save_academic_developer(result)
                    qualified_academic_count += 1
                    logger.info(f"  🎓 学术人士 [总计: {qualified_academic_count}]")
                    logger.info(f"    - Followers: {result.get('followers', 0)}")
                    logger.info(f"    - 总Stars: {result.get('total_stars', 0)}")
                    logger.info(f"    - 研究领域: {', '.join(result.get('research_areas', []))}")
                    logger.info(f"    - 联系方式: {result.get('contact_info', '无')}")
                else:
                    logger.warning(f"  ⚠️ 学术人士仓库未初始化，跳过保存")
                    rejected_count += 1
            else:
                # 保存到商业开发者表
                self.repository.save_developer(result)
                
                if result.get('is_indie_developer'):
                    qualified_commercial_count += 1
                    logger.info(f"  ✓ 商业开发者 [{qualified_commercial_count}/{max_developers}]")
                    logger.info(f"    - Followers: {result.get('followers', 0)}")
                    logger.info(f"    - 公开仓库: {result.get('public_repos', 0)}")
                    logger.info(f"    - 总Stars: {result.get('total_stars', 0)}")
                    logger.info(f"    - 联系方式: {result.get('contact_info', '无')}")
                else:
                    rejected_count += 1
                    logger.info(f"  ✗ 不合格（不符合独立开发者标准）")
            
            # 显示当前合格率
            if total_processed > 0:
                commercial_rate = qualified_commercial_count / total_processed * 100
                academic_rate = qualified_academic_count / total_processed * 100
                logger.info(f"  商业合格率: {commercial_rate:.1f}% ({qualified_commercial_count}/{total_processed})")
                logger.info(f"  学术识别率: {academic_rate:.1f}% ({qualified_academic_count}/{total_processed})")
        
        # 最终统计
        logger.info("\n" + "=" * 60)
        logger.info("发现任务完成")
        logger.info("=" * 60)
        logger.info(f"目标数量: {max_developers} 个商业开发者")
        logger.info(f"实际合格商业: {qualified_commercial_count} 个")
        logger.info(f"识别学术人士: {qualified_academic_count} 个")
        logger.info(f"总共发现: {total_discovered} 个开发者")
        logger.info(f"已存在跳过: {skipped_existing} 个")
        logger.info(f"实际分析: {total_processed} 个")
        logger.info(f"不合格: {rejected_count} 个")
        if total_processed > 0:
            logger.info(f"商业合格率: {qualified_commercial_count/total_processed*100:.1f}%")
            logger.info(f"学术识别率: {qualified_academic_count/total_processed*100:.1f}%")
        
        if qualified_commercial_count < max_developers:
            logger.warning(f"\n⚠️ 未达到目标数量（{qualified_commercial_count}/{max_developers}）")
            logger.warning(f"可能原因: 搜索策略已穷尽，或合格率过低")
            logger.warning(f"建议: 尝试其他搜索策略或调整筛选标准")
        else:
            logger.info(f"\n✓ 成功达到目标: {qualified_commercial_count} 个商业开发者")
        
        if qualified_academic_count > 0:
            logger.info(f"✓ 额外识别: {qualified_academic_count} 个学术人士")
        
        logger.info("=" * 60)
