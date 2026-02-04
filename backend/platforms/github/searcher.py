# -*- coding: utf-8 -*-
"""
GitHub搜索器 - 实现多种搜索策略
"""
import random
from typing import List, Dict, Set
from backend.utils.logger import setup_logger
from backend.utils.config_loader import load_config
from .scraper import GitHubScraper

logger = setup_logger()


class GitHubSearcher:
    """GitHub搜索器"""
    
    def __init__(self, scraper: GitHubScraper = None, repository=None):
        self.scraper = scraper or GitHubScraper()
        self.config = load_config()
        self.repository = repository  # 用于数据库去重
        
        # 加载发现策略配置
        github_config = self.config.get('github', {})
        self.strategy_config = github_config.get('discovery_strategy', {})
        
        # 加载仓库星标最低要求（可配置）
        self.min_repo_stars = github_config.get('min_repo_stars', 100)
        logger.info(f"✓ 仓库星标最低要求: {self.min_repo_stars} stars")
        
        # 去重缓存（根据配置决定是否启用）
        self.enable_deduplication = self.strategy_config.get('enable_deduplication', True)
        self.deduplication_scope = self.strategy_config.get('deduplication_scope', 'session')
        self.discovered_developers = set() if self.enable_deduplication else None
        
        if self.enable_deduplication:
            logger.info(f"✓ 去重策略已启用 (范围: {self.deduplication_scope})")
        else:
            logger.info("⊙ 去重策略已禁用")
    
    def _should_add_developer(self, username: str) -> bool:
        """
        判断是否应该添加该开发者（去重检查）
        
        Args:
            username: 开发者用户名
            
        Returns:
            True表示应该添加，False表示已存在
        """
        if not self.enable_deduplication:
            return True
        
        if username in self.discovered_developers:
            return False
        
        self.discovered_developers.add(username)
        return True
    
    def _filter_existing_developers(self, developers: Set[str]) -> Set[str]:
        """
        过滤掉数据库中已存在的开发者
        
        注意：此方法已禁用，去重逻辑移到discovery层
        这样可以动态补充，确保达到目标数量
        
        Args:
            developers: 开发者用户名集合
            
        Returns:
            原样返回（不过滤）
        """
        # 不再在这里过滤，让discovery层处理
        # 这样discovery可以动态请求更多开发者
        return developers
    
    def search_projects(self, keywords: List[str] = None, max_results_per_keyword: int = 10, 
                       max_developers: int = None, current_qualified: int = 0) -> List[str]:
        """
        通过关键词搜索项目并提取开发者（智能策略）
        
        统一策略：
        - 支持普通关键词搜索 (如: stable diffusion, AI tool)
        - 支持awesome项目搜索 (如: awesome-generative-ai)
        - 自动获取项目owner和贡献者
        - 智能控制发现数量，避免资源浪费
        
        Args:
            keywords: 关键词列表，如果为None则从配置读取
            max_results_per_keyword: 每个关键词的最大结果数
            max_developers: 目标开发者数量
            current_qualified: 当前已合格的开发者数量（用于智能停止）
            
        Returns:
            开发者用户名列表（去重）
        """
        if keywords is None:
            # 从配置文件读取搜索关键词
            github_config = self.config.get('github', {})
            keywords = github_config.get('search_keywords', [
                # 默认关键词（如果配置文件中没有）
                'stable diffusion', 'ComfyUI', 'AI tool',
                'awesome-generative-ai', 'awesome-stable-diffusion'
            ])
        
        # 随机打乱关键词顺序，增加随机性
        keywords = keywords.copy()
        random.shuffle(keywords)
        
        # 智能停止策略配置
        stop_when_sufficient = self.strategy_config.get('stop_when_sufficient', True)
        sufficient_buffer = self.strategy_config.get('sufficient_buffer_count', 5)
        
        logger.info(f"使用 {len(keywords)} 个关键词搜索GitHub项目（已随机打乱）")
        if stop_when_sufficient and max_developers:
            remaining = max_developers - current_qualified
            logger.info(f"智能停止策略: 还需 {remaining} 个合格开发者，缓冲 {sufficient_buffer} 个")
        
        developers = set()
        
        for i, keyword in enumerate(keywords, 1):
            # 智能停止：如果已经有足够的候选者，提前终止
            if stop_when_sufficient and max_developers and current_qualified > 0:
                remaining = max_developers - current_qualified
                if remaining <= 0:
                    logger.info(f"✓ 已达到目标数量，停止搜索")
                    break
                
                # 如果已发现的开发者数量 >= 剩余需要数量 + 缓冲数量，停止搜索
                if len(developers) >= remaining + sufficient_buffer:
                    logger.info(f"✓ 已发现足够候选者 ({len(developers)} >= {remaining + sufficient_buffer})，停止搜索")
                    break
            
            # 如果已经达到目标数量，提前终止
            if max_developers and len(developers) >= max_developers:
                logger.info(f"已达到目标数量 {max_developers}，提前终止搜索")
                break
            
            logger.info(f"[{i}/{len(keywords)}] 搜索关键词: {keyword}")
            
            # 随机选择排序方式，增加多样性
            sort_options = ['stars', 'updated', 'forks']
            sort = random.choice(sort_options)
            
            # 搜索仓库
            repositories = self.scraper.search_repositories(
                keyword, 
                max_results=max_results_per_keyword,
                sort=sort
            )
            
            # 提取owner和贡献者
            for repo in repositories:
                if max_developers and len(developers) >= max_developers:
                    break
                
                # 添加owner（去重检查）
                username = repo.get('owner_username')
                if username and not self._is_organization(username):
                    if self._should_add_developer(username):
                        developers.add(username)
                
                # 如果是awesome项目或高星项目，获取贡献者
                repo_name = repo.get('repo_name')
                stars = repo.get('stars', 0)
                is_awesome = 'awesome' in keyword.lower() or (repo_name and 'awesome' in repo_name.lower())
                
                # 动态获取贡献者数量限制
                if repo_name and (is_awesome or stars >= self.min_repo_stars):
                    max_contrib = self._get_contributor_limit(repo_name, stars, is_awesome)
                    
                    logger.info(f"  获取项目贡献者: {repo_name} ({stars} stars, 限制{max_contrib}个)")
                    contributors = self.scraper.get_repository_contributors(
                        repo_name, 
                        max_contributors=max_contrib
                    )
                    
                    for contrib in contributors:
                        if not self._is_organization(contrib):
                            # 去重检查
                            if self._should_add_developer(contrib):
                                developers.add(contrib)
                        
                        if max_developers and len(developers) >= max_developers:
                            break
            
            logger.info(f"当前已找到 {len(developers)} 个开发者")
        
        developer_list = list(developers)
        # 随机打乱结果顺序
        random.shuffle(developer_list)
        
        logger.info(f"总共找到 {len(developer_list)} 个独特的开发者")
        
        return developer_list
    
    def search_awesome_lists(self, topics: List[str] = None, max_developers: int = None) -> List[str]:
        """
        搜索awesome列表找开发者
        
        策略：
        1. 搜索 "awesome AI" 相关列表
        2. 获取列表中提到的项目
        3. 提取项目作者和贡献者
        
        Args:
            topics: awesome关键词列表，如果为None则从配置读取
            max_developers: 最大开发者数量
            
        Returns:
            开发者用户名列表
        """
        if topics is None:
            # 从配置文件读取awesome搜索关键词
            github_config = self.config.get('github', {})
            topics = github_config.get('awesome_search_keywords', [
                # 默认关键词（如果配置文件中没有）
                'awesome-generative-ai', 'awesome-ai-tools', 'awesome-stable-diffusion',
                'awesome-image-generation', 'awesome-video', 'awesome-ai-apps'
            ])
        
        logger.info(f"搜索 {len(topics)} 个awesome列表")
        
        developers = set()
        
        for topic in topics:
            # 达到目标后提前终止
            if max_developers and len(developers) >= max_developers:
                break
                
            logger.info(f"搜索: {topic}")
            
            # 搜索awesome仓库
            repositories = self.scraper.search_repositories(topic, max_results=5)
            
            # 获取每个仓库的贡献者和starred用户
            for repo in repositories:
                if max_developers and len(developers) >= max_developers:
                    break
                    
                repo_name = repo.get('repo_name')
                if repo_name:
                    # 获取贡献者
                    contributors = self.scraper.get_repository_contributors(repo_name, max_contributors=20)
                    developers.update(contributors)
                    logger.info(f"从 {repo_name} 获取 {len(contributors)} 个贡献者")
        
        developer_list = list(developers)
        logger.info(f"从awesome列表找到 {len(developer_list)} 个开发者")
        
        return developer_list
    
    def search_by_explore(self, languages: List[str] = None, max_developers: int = None) -> List[str]:
        """
        通过GitHub Explore发现开发者
        
        策略：
        1. 搜索trending仓库（AI相关）
        2. 搜索特定语言的AI项目
        3. 提取活跃的独立开发者
        
        Args:
            languages: 编程语言列表
            max_developers: 最大开发者数量
            
        Returns:
            开发者用户名列表
        """
        if languages is None:
            languages = ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust']
        
        logger.info(f"通过 {len(languages)} 种语言探索AI开发者")
        
        developers = set()
        
        # 搜索trending AI项目
        trending_keywords = ['AI', 'machine-learning', 'deep-learning', 'LLM', 'GPT']
        
        for keyword in trending_keywords:
            if max_developers and len(developers) >= max_developers:
                break
                
            for language in languages:
                if max_developers and len(developers) >= max_developers:
                    break
                    
                query = f"{keyword} language:{language}"
                logger.info(f"探索: {query}")
                
                repositories = self.scraper.search_repositories(query, max_results=10)
                
                for repo in repositories:
                    username = repo.get('owner_username')
                    if username and not self._is_organization(username):
                        developers.add(username)
                        
                    if max_developers and len(developers) >= max_developers:
                        break
        
        developer_list = list(developers)
        logger.info(f"通过探索找到 {len(developer_list)} 个开发者")
        
        return developer_list
    
    def search_by_topics(self, topics: List[str] = None, max_per_topic: int = 15, max_developers: int = None) -> List[str]:
        """
        通过GitHub Topics发现开发者
        
        策略：搜索特定topic标签的仓库，找到活跃的AI开发者
        
        Args:
            topics: topic列表，如果为None则从配置读取
            max_per_topic: 每个topic的最大仓库数
            max_developers: 最大开发者数量
            
        Returns:
            开发者用户名列表
        """
        if topics is None:
            # 从配置文件读取搜索topics
            github_config = self.config.get('github', {})
            topics = github_config.get('search_topics', [
                # 默认topics（如果配置文件中没有）
                'image-generation', 'video-generation', 'stable-diffusion',
                'generative-ai', 'ai-tools', 'ai-application'
            ])
        
        logger.info(f"通过 {len(topics)} 个topics搜索开发者")
        
        developers = set()
        
        for topic in topics:
            if max_developers and len(developers) >= max_developers:
                break
                
            query = f"topic:{topic}"
            logger.info(f"搜索topic: {topic}")
            
            repositories = self.scraper.search_repositories(query, max_results=max_per_topic)
            
            for repo in repositories:
                username = repo.get('owner_username')
                if username and not self._is_organization(username):
                    developers.add(username)
                    
                if max_developers and len(developers) >= max_developers:
                    break
        
        developer_list = list(developers)
        logger.info(f"通过topics找到 {len(developer_list)} 个开发者")
        
        return developer_list
    
    def search_by_quality_projects(self, max_developers: int = 50) -> List[str]:
        """
        通过优质AI项目找贡献者（新策略）
        
        策略：
        1. 搜索与WaveSpeedAI业务相关的优质开源项目（stars >= 100）
        2. 获取项目的贡献者
        3. 筛选有影响力的贡献者（followers >= 100 或 stars >= 100）
        
        这是最精准的方式，因为：
        - 项目质量有保证（stars >= 100）
        - 贡献者有实际AI项目经验
        - 业务相关性强
        
        Args:
            max_developers: 最大开发者数量
            
        Returns:
            开发者用户名列表
        """
        logger.info("🎯 使用优质项目策略搜索开发者")
        
        # WaveSpeedAI业务相关的搜索关键词
        # 重点：图像/视频生成、Stable Diffusion、ComfyUI等
        project_keywords = [
            # 图像生成核心
            'stable diffusion', 'stable-diffusion-webui', 'ComfyUI',
            'text-to-image', 'image generation api',
            # 视频生成
            'text-to-video', 'video generation', 'AnimateDiff',
            # AI工具/应用
            'AI image tool', 'AI art generator', 'generative AI app',
            # API/SDK相关
            'stable diffusion api', 'image generation sdk',
            'AI API wrapper', 'diffusion model api'
        ]
        
        developers = set()
        projects_found = 0
        
        # 随机打乱关键词，增加多样性
        random.shuffle(project_keywords)
        
        # 随机选择排序方式，避免每次都是相同结果
        sort_options = ['stars', 'updated', 'forks']
        
        for keyword in project_keywords:
            if max_developers and len(developers) >= max_developers * 2:
                logger.info(f"已收集足够开发者 ({len(developers)})，停止搜索")
                break
            
            logger.info(f"🔍 搜索项目: {keyword}")
            
            # 随机选择排序方式
            sort = random.choice(sort_options)
            
            # 搜索优质项目
            repositories = self.scraper.search_repositories(
                keyword, 
                max_results=10,  # 增加到10个
                sort=sort
            )
            
            # 随机打乱仓库顺序
            random.shuffle(repositories)
            
            for repo in repositories:
                repo_name = repo.get('repo_name')
                stars = repo.get('stars', 0)
                
                # 项目质量过滤：使用配置的最低星标要求
                if stars < self.min_repo_stars:
                    logger.debug(f"  跳过低星项目: {repo_name} ({stars} stars)")
                    continue
                
                projects_found += 1
                logger.info(f"  ✓ 优质项目: {repo_name} ({stars} stars)")
                
                # 获取贡献者
                contributors = self.scraper.get_repository_contributors(
                    repo_name, 
                    max_contributors=30
                )
                
                logger.info(f"    找到 {len(contributors)} 个贡献者")
                
                # 随机打乱贡献者顺序
                random.shuffle(contributors)
                
                for username in contributors:
                    if self._is_organization(username):
                        continue
                    
                    developers.add(username)
                
                if max_developers and len(developers) >= max_developers * 2:
                    break
        
        developer_list = list(developers)
        random.shuffle(developer_list)
        
        logger.info(f"✓ 从 {projects_found} 个优质项目找到 {len(developer_list)} 个贡献者")
        
        return developer_list
        """
        专门搜索独立开发者
        
        策略：
        1. 搜索 "indie hacker" + AI相关关键词
        2. 搜索 "solo developer" + AI
        3. 搜索 "side project" + AI
        
        Returns:
            开发者用户名列表
        """
        logger.info("搜索独立开发者")
        
        developers = set()
        
        indie_keywords = [
            # 独立开发者 + AI应用
            'indie maker AI tool', 'solo developer AI app', 'indie AI SaaS',
            # 创业者
            'AI startup founder', 'indie AI product', 'solo AI builder',
            # 副业项目
            'side project AI', 'weekend project AI', 'indie hacker generative AI'
        ]
        
        for keyword in indie_keywords:
            logger.info(f"搜索: {keyword}")
            repositories = self.scraper.search_repositories(keyword, max_results=10)
            
            for repo in repositories:
                username = repo.get('owner_username')
                if username and not self._is_organization(username):
                    developers.add(username)
        
        developer_list = list(developers)[:max_results]
        logger.info(f"找到 {len(developer_list)} 个独立开发者")
        
        return developer_list
    
    def _is_organization(self, username: str) -> bool:
        """
        简单判断是否为组织账号
        
        启发式规则：
        - 包含公司常见后缀
        - 全大写
        - 包含数字和特殊字符组合
        """
        org_indicators = ['inc', 'corp', 'company', 'team', 'lab', 'labs', 'ai', 'tech']
        username_lower = username.lower()
        
        # 检查是否包含组织指示词
        for indicator in org_indicators:
            if indicator in username_lower and len(username) > 10:
                return True
        
        # 全大写可能是组织
        if username.isupper() and len(username) > 3:
            return True
        
        return False
    
    def discover_developers_generator(self, target_qualified: int, max_attempts: int = 500):
        """
        发现开发者生成器 - 逐个返回候选者
        
        策略：深度优先，一个仓库的所有贡献者都返回完才换下一个仓库
        这样discovery层可以逐个分析，一个仓库分析完才换下一个
        
        Args:
            target_qualified: 目标合格开发者数量
            max_attempts: 最大尝试次数
            
        Yields:
            (username, source_info) 元组：开发者用户名和来源信息
        """
        logger.info(f"开始深度优先发现（生成器模式），目标: {target_qualified} 个合格开发者")
        
        # 从配置文件读取搜索关键词
        github_config = self.config.get('github', {})
        keywords = github_config.get('search_keywords', [
            'stable diffusion', 'ComfyUI', 'AI tool',
            'awesome-generative-ai', 'awesome-stable-diffusion'
        ])
        
        # 随机打乱关键词顺序
        keywords = keywords.copy()
        random.shuffle(keywords)
        
        logger.info(f"使用 {len(keywords)} 个关键词搜索（深度优先，已随机打乱）")
        
        discovered_count = 0
        
        for keyword_idx, keyword in enumerate(keywords, 1):
            # 检查停止标志
            from utils.crawler_status import should_stop
            if should_stop():
                logger.warning(f"\n⚠️ 检测到停止信号，停止搜索")
                break
            
            if discovered_count >= max_attempts:
                logger.info(f"已达到最大尝试次数 {max_attempts}，停止搜索")
                break
            
            logger.info(f"\n{'='*60}")
            logger.info(f"[{keyword_idx}/{len(keywords)}] 搜索关键词: {keyword}")
            logger.info(f"{'='*60}")
            
            # 随机选择排序方式
            sort_options = ['stars', 'updated', 'forks']
            sort = random.choice(sort_options)
            
            # 搜索仓库（一次性搜索10个，存起来）
            repositories = self.scraper.search_repositories(
                keyword, 
                max_results=10,
                sort=sort
            )
            
            if not repositories:
                logger.info(f"  未找到仓库，跳过该关键词")
                continue
            
            logger.info(f"✓ 找到 {len(repositories)} 个仓库，开始逐个深度挖掘...")
            
            # 逐个处理仓库（深度优先）
            for repo_idx, repo in enumerate(repositories, 1):
                # 检查停止标志
                from utils.crawler_status import should_stop
                if should_stop():
                    logger.warning(f"\n⚠️ 检测到停止信号，停止处理仓库")
                    return
                
                if discovered_count >= max_attempts:
                    logger.info(f"\n已达到最大尝试次数，停止")
                    break
                
                repo_name = repo.get('repo_name')
                stars = repo.get('stars', 0)
                
                # 过滤低星仓库（使用配置的最低星标要求）
                if stars < self.min_repo_stars:
                    logger.info(f"  ⊙ 仓库 [{repo_idx}/{len(repositories)}]: {repo_name} ({stars} ⭐) - 跳过低星仓库")
                    continue
                
                logger.info(f"\n{'─'*60}")
                logger.info(f"仓库 [{repo_idx}/{len(repositories)}]: {repo_name} ({stars} ⭐)")
                logger.info(f"{'─'*60}")
                
                # 直接获取贡献者（不分析 Owner）
                if not repo_name:
                    logger.info(f"  ⊙ 仓库名称无效，跳过")
                    continue
                
                # 打印获取贡献者的日志
                logger.info(f"  📡 开始获取贡献者...")
                
                # 获取所有贡献者
                contributors, error_msg = self.scraper.get_repository_contributors(repo_name)
                
                if not contributors:
                    logger.warning(f"  ✗ 获取贡献者失败: {error_msg}")
                    if "202" in error_msg:
                        logger.info(f"     说明：GitHub正在异步生成贡献者数据，这是正常现象")
                        logger.info(f"     解决：等待几分钟后，该仓库的数据会准备好")
                    logger.info(f"     查看：https://github.com/{repo_name}/graphs/contributors")
                    continue
                
                total_contributors = len(contributors)
                logger.info(f"  ✓ 成功获取 {total_contributors} 个贡献者，逐个分析...")
                
                # 逐个返回贡献者（深度优先：一个仓库的所有贡献者都返回完才换下一个）
                repo_yield_count = 0
                for contrib_idx, contrib_info in enumerate(contributors, 1):
                    if discovered_count >= max_attempts:
                        break
                    
                    username = contrib_info['username']
                    commits = contrib_info['commits']
                    rank = contrib_info['rank']
                    
                    if not self._is_organization(username):
                        if self._should_add_developer(username):
                            discovered_count += 1
                            repo_yield_count += 1
                            # 显示当前仓库进度：已处理/总数
                            remaining = total_contributors - contrib_idx
                            source_info = f"Contributor #{rank} of {repo_name} ({commits} commits, 剩余{remaining}个)"
                            logger.info(f"  → 返回贡献者 [{contrib_idx}/{total_contributors}]: {username} (排名#{rank}, {commits} commits, 剩余 {remaining} 个)")
                            yield (username, source_info)
                
                logger.info(f"  ✓ 该仓库返回了 {repo_yield_count} 个新开发者")
                logger.info(f"  累计已发现: {discovered_count} 个")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"深度优先搜索完成，共发现 {discovered_count} 个独特的开发者")
        logger.info(f"{'='*60}")
    
    def discover_developers(self, limit: int = 100, current_qualified: int = 0) -> List[str]:
        """
        发现开发者 - 深度优先策略
        
        策略：逐个仓库深度挖掘，而不是广度搜索
        - 先搜索一个仓库，获取所有贡献者
        - 如果数量不够，再搜索下一个仓库
        - 避免过早搜索多个仓库造成资源浪费
        
        Args:
            limit: 目标开发者数量
            current_qualified: 当前已合格的开发者数量
            
        Returns:
            开发者用户名列表
        """
        logger.info(f"开始发现开发者（深度优先），目标: {limit}, 当前已合格: {current_qualified}")
        
        # 计算实际需要发现的数量（带缓冲）
        remaining = limit - current_qualified
        buffer_ratio = self.strategy_config.get('discovery_buffer_ratio', 1.3)
        target_discovery = int(remaining * buffer_ratio)
        
        # 限制单批次最大/最小数量
        max_per_batch = self.strategy_config.get('max_discovery_per_batch', 50)
        min_per_batch = self.strategy_config.get('min_discovery_per_batch', 10)
        target_discovery = max(min(target_discovery, max_per_batch), min_per_batch)
        
        logger.info(f"智能策略: 还需 {remaining} 个，本批次目标发现 {target_discovery} 个（缓冲比例: {buffer_ratio}）")
        
        # 使用深度优先搜索
        developers = self._search_depth_first(target_count=target_discovery)
        
        # 随机打乱结果，增加多样性
        random.shuffle(developers)
        
        logger.info(f"发现完成，共 {len(developers)} 个开发者（已随机化）")
        
        return developers
    
    def _search_depth_first(self, target_count: int) -> List[str]:
        """
        深度优先搜索开发者
        
        策略：
        1. 逐个搜索关键词
        2. 对每个关键词，逐个处理仓库
        3. 对每个仓库，获取所有贡献者（不限制数量）
        4. 达到目标数量后立即停止
        
        Args:
            target_count: 目标发现数量
            
        Returns:
            开发者用户名列表
        """
        # 从配置文件读取搜索关键词
        github_config = self.config.get('github', {})
        keywords = github_config.get('search_keywords', [
            'stable diffusion', 'ComfyUI', 'AI tool',
            'awesome-generative-ai', 'awesome-stable-diffusion'
        ])
        
        # 随机打乱关键词顺序
        keywords = keywords.copy()
        random.shuffle(keywords)
        
        logger.info(f"使用 {len(keywords)} 个关键词搜索（深度优先，已随机打乱）")
        
        developers = set()
        
        for keyword_idx, keyword in enumerate(keywords, 1):
            # 检查是否已达到目标
            if len(developers) >= target_count:
                logger.info(f"✓ 已达到目标数量 {target_count}，停止搜索")
                break
            
            remaining = target_count - len(developers)
            logger.info(f"[{keyword_idx}/{len(keywords)}] 搜索关键词: {keyword} (还需 {remaining} 个)")
            
            # 随机选择排序方式
            sort_options = ['stars', 'updated', 'forks']
            sort = random.choice(sort_options)
            
            # 搜索仓库
            repositories = self.scraper.search_repositories(
                keyword, 
                max_results=10,
                sort=sort
            )
            
            if not repositories:
                logger.debug(f"  未找到仓库，跳过")
                continue
            
            # 逐个处理仓库（深度优先）
            for repo_idx, repo in enumerate(repositories, 1):
                if len(developers) >= target_count:
                    logger.info(f"  ✓ 已达到目标，停止处理仓库")
                    break
                
                repo_name = repo.get('repo_name')
                stars = repo.get('stars', 0)
                owner_username = repo.get('owner_username')
                
                # 添加owner
                if owner_username and not self._is_organization(owner_username):
                    if self._should_add_developer(owner_username):
                        developers.add(owner_username)
                        logger.debug(f"  + Owner: {owner_username}")
                
                # 判断是否需要获取贡献者
                is_awesome = 'awesome' in keyword.lower() or (repo_name and 'awesome' in repo_name.lower())
                
                if not repo_name or (not is_awesome and stars < self.min_repo_stars):
                    logger.debug(f"  跳过低星项目: {repo_name} ({stars} stars)")
                    continue
                
                logger.info(f"  [{repo_idx}/{len(repositories)}] 深度挖掘: {repo_name} ({stars} stars)")
                
                # 获取所有贡献者（不限制数量）
                contributors = self.scraper.get_repository_contributors(repo_name)
                
                if not contributors:
                    logger.debug(f"    无贡献者数据")
                    continue
                
                # 添加所有贡献者（去重）
                added_count = 0
                for contrib in contributors:
                    if len(developers) >= target_count:
                        break
                    
                    if not self._is_organization(contrib):
                        if self._should_add_developer(contrib):
                            developers.add(contrib)
                            added_count += 1
                
                logger.info(f"    ✓ 从该仓库新增 {added_count} 个开发者，当前总数: {len(developers)}")
                
                # 如果已经足够，提前停止
                if len(developers) >= target_count:
                    logger.info(f"  ✓ 已达到目标数量，停止搜索")
                    break
        
        developer_list = list(developers)
        logger.info(f"深度优先搜索完成，共找到 {len(developer_list)} 个独特的开发者")
        
        return developer_list
