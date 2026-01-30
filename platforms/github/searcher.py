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
    
    def search_projects(self, keywords: List[str] = None, max_results_per_keyword: int = 10, max_developers: int = None) -> List[str]:
        """
        通过关键词搜索项目并提取开发者
        
        统一策略：
        - 支持普通关键词搜索 (如: stable diffusion, AI tool)
        - 支持awesome项目搜索 (如: awesome-generative-ai)
        - 自动获取项目owner和贡献者
        
        Args:
            keywords: 关键词列表，如果为None则从配置读取
            max_results_per_keyword: 每个关键词的最大结果数
            max_developers: 最大开发者数量，达到后提前终止
            
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
        
        logger.info(f"使用 {len(keywords)} 个关键词搜索GitHub项目（已随机打乱）")
        
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
            
            # 提取owner和贡献者
            for repo in repositories:
                if max_developers and len(developers) >= max_developers:
                    break
                
                # 添加owner
                username = repo.get('owner_username')
                if username and not self._is_organization(username):
                    developers.add(username)
                
                # 如果是awesome项目或高星项目，获取贡献者
                repo_name = repo.get('repo_name')
                stars = repo.get('stars', 0)
                is_awesome = 'awesome' in keyword.lower() or (repo_name and 'awesome' in repo_name.lower())
                
                if repo_name and (is_awesome or stars >= 100):
                    logger.info(f"  获取项目贡献者: {repo_name} ({stars} stars)")
                    contributors = self.scraper.get_repository_contributors(
                        repo_name, 
                        max_contributors=30
                    )
                    
                    for contrib in contributors:
                        if not self._is_organization(contrib):
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
    
    def discover_developers(self, limit: int = 100) -> List[str]:
        """
        发现开发者 - 统一策略
        
        使用配置文件中的搜索关键词搜索项目,提取owner和贡献者
        
        Args:
            limit: 最大开发者数量
            
        Returns:
            开发者用户名列表
        """
        logger.info(f"开始发现开发者，限制: {limit}")
        
        # 使用统一的搜索方法
        developers = self.search_projects(max_results_per_keyword=10, max_developers=limit * 2)
        
        # 随机打乱结果，增加多样性
        random.shuffle(developers)
        
        # 限制数量
        developer_list = developers[:limit]
        
        logger.info(f"发现完成，共 {len(developer_list)} 个开发者（已随机化）")
        
        return developer_list
