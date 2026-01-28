# -*- coding: utf-8 -*-
"""
GitHub搜索器 - 实现多种搜索策略
"""
import random
from typing import List, Dict, Set
from utils.logger import setup_logger
from utils.config_loader import load_config
from .scraper import GitHubScraper

logger = setup_logger()


class GitHubSearcher:
    """GitHub搜索器"""
    
    def __init__(self, scraper: GitHubScraper = None, repository=None):
        self.scraper = scraper or GitHubScraper()
        self.config = load_config()
        self.repository = repository  # 用于数据库去重
    
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
    
    def search_by_keywords(self, keywords: List[str] = None, max_results_per_keyword: int = 10, max_developers: int = None) -> List[str]:
        """
        通过关键词搜索开发者
        
        策略：搜索仓库 -> 提取owner -> 去重
        重点关注：AI工具、AI应用、AI框架的独立开发者
        
        Args:
            keywords: 关键词列表，如果为None则从配置读取
            max_results_per_keyword: 每个关键词的最大结果数
            max_developers: 最大开发者数量，达到后提前终止
            
        Returns:
            开发者用户名列表（去重）
        """
        if keywords is None:
            # 针对WaveSpeedAI业务的精准关键词
            # WaveSpeedAI：图像/视频生成API平台，面向AI应用开发者
            keywords = [
                # AI应用开发者
                'AI SaaS', 'AI tool builder', 'AI application',
                # 图像/视频相关
                'image generation', 'video generation', 'AI image tool',
                # API集成者
                'API integration', 'AI API wrapper', 'AI SDK',
                # 内容创作工具
                'content creation tool', 'AI editor', 'generative AI app',
                # 创业者/独立开发者
                'indie maker AI', 'solo developer AI', 'AI startup'
            ]
        
        # 随机打乱关键词顺序，增加随机性
        keywords = keywords.copy()
        random.shuffle(keywords)
        
        logger.info(f"使用 {len(keywords)} 个关键词搜索GitHub开发者（已随机打乱）")
        
        developers = set()
        
        for i, keyword in enumerate(keywords, 1):
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
            
            # 提取owner
            for repo in repositories:
                username = repo.get('owner_username')
                if username and not self._is_organization(username):
                    developers.add(username)
                    
                    # 达到目标后立即停止
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
        3. 提取项目作者
        
        Args:
            topics: 主题列表
            max_developers: 最大开发者数量
            
        Returns:
            开发者用户名列表
        """
        if topics is None:
            # 针对WaveSpeedAI业务的awesome列表
            topics = [
                'awesome-generative-ai', 'awesome-ai-tools', 'awesome-ai-apps',
                'awesome-image-generation', 'awesome-video', 'awesome-stable-diffusion',
                'awesome-api', 'awesome-saas', 'awesome-indie-maker'
            ]
        
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
            topics: topic列表
            max_per_topic: 每个topic的最大仓库数
            max_developers: 最大开发者数量
            
        Returns:
            开发者用户名列表
        """
        if topics is None:
            # 针对WaveSpeedAI业务的精准topics
            topics = [
                # 图像/视频生成
                'image-generation', 'video-generation', 'text-to-image', 'text-to-video',
                'stable-diffusion', 'generative-ai', 'diffusion-models',
                # AI应用开发
                'ai-tools', 'ai-application', 'ai-saas', 'ai-sdk',
                # API相关
                'api-wrapper', 'api-client', 'rest-api',
                # 内容创作
                'content-creation', 'creative-tools', 'media-generation',
                # 开发者工具
                'developer-tools', 'automation', 'productivity'
            ]
        
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
                
                # 项目质量过滤：至少100 stars
                if stars < 100:
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
    
    def discover_developers(self, strategy: str = 'comprehensive', limit: int = 100) -> List[str]:
        """
        综合发现开发者 - 智能策略分配
        
        Args:
            strategy: 搜索策略
                - 'quality_projects': 优质项目贡献者（推荐，最精准）
                - 'comprehensive': 综合策略
                - 'keywords': 仅关键词
                - 'awesome': 仅awesome列表
                - 'explore': 仅explore
                - 'topics': 仅topics
                - 'indie': 仅独立开发者
            limit: 最大开发者数量
            
        Returns:
            开发者用户名列表
        """
        logger.info(f"开始发现开发者，策略: {strategy}, 限制: {limit}")
        
        all_developers = set()
        
        if strategy == 'quality_projects':
            # 新策略：从优质AI项目找贡献者（最精准）
            logger.info("🎯 使用优质项目策略（推荐）")
            developers = self.search_by_quality_projects(max_developers=limit)
            all_developers.update(developers)
            
        elif strategy == 'comprehensive':
            # 智能策略：根据目标数量动态调整
            logger.info("使用综合策略，智能权重分配")
            
            if limit <= 10:
                # 小数量：只用最快最有效的方法
                logger.info(f"小数量模式（{limit}个），使用快速策略")
                developers = self.search_by_keywords(max_results_per_keyword=3, max_developers=limit)
                all_developers.update(developers)
                
            elif limit <= 50:
                # 中等数量：关键词 + Topics
                logger.info(f"中等数量模式（{limit}个），使用关键词+Topics")
                
                # 关键词 (60%)
                target = int(limit * 0.6)
                developers = self.search_by_keywords(max_results_per_keyword=5, max_developers=target)
                all_developers.update(developers)
                
                # Topics (40%)
                if len(all_developers) < limit:
                    remaining = limit - len(all_developers)
                    developers = self.search_by_topics(max_per_topic=8, max_developers=remaining)
                    all_developers.update(developers)
                
            else:
                # 大数量：全策略
                logger.info(f"大数量模式（{limit}个），使用全策略")
                
                # 1. 关键词搜索 (40%)
                target = int(limit * 0.4)
                developers = self.search_by_keywords(max_results_per_keyword=5, max_developers=target)
                all_developers.update(developers)
                logger.info(f"关键词策略: {len(developers)} 个开发者")
                
                # 2. Topics搜索 (30%)
                if len(all_developers) < limit:
                    remaining = limit - len(all_developers)
                    target = min(remaining, int(limit * 0.3))
                    developers = self.search_by_topics(max_per_topic=8, max_developers=target)
                    all_developers.update(developers)
                    logger.info(f"Topics策略: {len(developers)} 个开发者")
                
                # 3. Awesome列表 (20%)
                if len(all_developers) < limit:
                    remaining = limit - len(all_developers)
                    target = min(remaining, int(limit * 0.2))
                    developers = self.search_awesome_lists(max_developers=target)
                    all_developers.update(developers)
                    logger.info(f"Awesome策略: {len(developers)} 个开发者")
                
                # 4. Explore (10%)
                if len(all_developers) < limit:
                    remaining = limit - len(all_developers)
                    developers = self.search_by_explore(max_developers=remaining)
                    all_developers.update(developers)
                    logger.info(f"Explore策略: {len(developers)} 个开发者")
            
        elif strategy == 'keywords':
            developers = self.search_by_keywords(max_developers=limit)
            all_developers.update(developers)
        elif strategy == 'awesome':
            developers = self.search_awesome_lists(max_developers=limit)
            all_developers.update(developers)
        elif strategy == 'explore':
            developers = self.search_by_explore(max_developers=limit)
            all_developers.update(developers)
        elif strategy == 'topics':
            developers = self.search_by_topics(max_developers=limit)
            all_developers.update(developers)
        elif strategy == 'indie':
            developers = self.search_indie_developers(max_results=limit)
            all_developers.update(developers)
        
        developer_list = list(all_developers)[:limit]
        
        # 注意：不再在这里过滤已存在的开发者
        # 去重逻辑已移到discovery层，这样可以动态补充
        
        # 随机打乱结果，增加多样性
        random.shuffle(developer_list)
        
        logger.info(f"发现完成，共 {len(developer_list)} 个开发者（已随机化）")
        
        return developer_list
