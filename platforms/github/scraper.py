# -*- coding: utf-8 -*-
"""
GitHub爬虫 - 使用API获取贡献者

策略更新（2026-01-30）：
- 使用GitHub内部API (/graphs/contributors-data) 获取贡献者
- 速度快、稳定、可获取完整列表（100+个贡献者）
- 不再使用Selenium或侧边栏爬取
"""
import requests
import time
import re
import random
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from utils.logger import setup_logger
from utils.retry import retry_on_failure

logger = setup_logger()


class GitHubScraper:
    """GitHub爬虫（UA轮换+智能延迟）"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # 20个User-Agent
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        
        self.min_delay = 3.0  # 增加到3秒
        self.max_delay = 5.0  # 增加到5秒
        self.last_request_time = 0
        self.rate_limit_count = 0
        self.consecutive_429 = 0  # 连续429次数
        
        logger.info(f"爬虫初始化（延迟3-5秒，{len(self.user_agents)}个UA）")
        logger.info("⏳ 等待3秒让IP冷却...")
        time.sleep(3)  # 改为3秒冷却期
        logger.info("✓ 冷却完成，开始爬取")
    
    def _get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
    
    def _wait(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        delay = random.uniform(self.min_delay, self.max_delay)
        
        # 如果连续触发429，增加额外延迟
        if self.consecutive_429 > 0:
            penalty = min(self.consecutive_429 * 2, 5)
            delay = min(delay + penalty, 5.0)
            logger.debug(f"连续429 {self.consecutive_429}次，延迟增加到{delay:.1f}秒")
        
        if time_since_last < delay:
            time.sleep(delay - time_since_last)
        
        self.last_request_time = time.time()
    
    @retry_on_failure(max_retries=3)
    def search_repositories(self, keyword: str, max_results: int = 10, sort: str = 'stars') -> List[Dict]:
        self._wait()
        
        try:
            url = "https://github.com/search"
            params = {'q': keyword, 'type': 'repositories', 's': sort, 'o': 'desc'}
            
            response = self.session.get(url, params=params, headers=self._get_headers(), timeout=15)
            
            if response.status_code == 429:
                self.consecutive_429 += 1
                wait_time = min(2 ** self.consecutive_429, 5)
                logger.warning(f"429错误（第{self.consecutive_429}次），等待{wait_time}秒...")
                time.sleep(wait_time)
                
                # 如果连续3次429，建议更长的冷却期
                if self.consecutive_429 >= 3:
                    logger.warning("⚠️ 连续多次429，建议稍后再试或降低爬取频率")
                
                return self.search_repositories(keyword, max_results, sort)
            
            response.raise_for_status()
            
            # 成功后重置429计数
            if self.consecutive_429 > 0:
                logger.info(f"✓ 速率限制已解除（之前连续{self.consecutive_429}次429）")
                self.consecutive_429 = 0
            
            soup = BeautifulSoup(response.text, 'html.parser')
            repositories = []
            
            repo_items = soup.select('div[data-testid="results-list"] > div')
            if not repo_items:
                repo_items = soup.select('.repo-list-item')
            if not repo_items:
                repo_items = soup.select('li.repo-list-item')
            
            for item in repo_items[:max_results * 2]:
                try:
                    repo_link = item.select_one('a[href^="/"]')
                    if not repo_link:
                        continue
                    
                    href = repo_link.get('href', '')
                    if not href or '/topics' in href or '/search' in href:
                        continue
                    
                    repo_name = href.strip('/').split('?')[0]
                    parts = repo_name.split('/')
                    if len(parts) >= 2:
                        repo_name = f"{parts[0]}/{parts[1]}"
                    else:
                        continue
                    
                    owner_username = parts[0]
                    
                    desc_elem = item.select_one('p')
                    description = desc_elem.text.strip() if desc_elem else ''
                    
                    stars = 0
                    stars_elem = item.select_one('a[href*="stargazers"]')
                    if stars_elem:
                        stars_text = stars_elem.text.strip().replace(',', '')
                        if 'k' in stars_text.lower():
                            stars = int(float(stars_text.lower().replace('k', '')) * 1000)
                        else:
                            try:
                                stars = int(stars_text)
                            except:
                                pass
                    
                    lang_elem = item.select_one('[itemprop="programmingLanguage"]')
                    language = lang_elem.text.strip() if lang_elem else ''
                    
                    repositories.append({
                        'repo_id': hash(repo_name),
                        'repo_name': repo_name,
                        'repo_url': f"https://github.com/{repo_name}",
                        'owner_username': owner_username,
                        'owner_url': f"https://github.com/{owner_username}",
                        'description': description,
                        'stars': stars,
                        'forks': 0,
                        'language': language,
                        'created_at': None,
                        'updated_at': None
                    })
                    
                    if len(repositories) >= max_results:
                        break
                except:
                    continue
            
            logger.info(f"搜索'{keyword}'找到{len(repositories)}个仓库")
            return repositories
            
        except Exception as e:
            if '429' in str(e):
                self.consecutive_429 += 1
                wait_time = min(2 ** self.consecutive_429, 5)
                logger.warning(f"429错误（第{self.consecutive_429}次），等待{wait_time}秒...")
                time.sleep(wait_time)
            logger.error(f"搜索失败: {e}")
            return []
    
    @retry_on_failure(max_retries=3)
    def get_user_info(self, username: str) -> Optional[Dict]:
        self._wait()
        
        try:
            url = f"https://github.com/{username}"
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            user_info = {
                'user_id': hash(username),
                'username': username,
                'name': '',
                'profile_url': url,
                'avatar_url': '',
                'bio': '',
                'company': '',
                'location': '',
                'email': '',
                'blog': '',
                'twitter': '',
                'public_repos': 0,
                'followers': 0,
                'following': 0,
                'created_at': None,
                'updated_at': None
            }
            
            name_elem = soup.select_one('span[itemprop="name"]')
            if name_elem:
                user_info['name'] = name_elem.text.strip()
            
            avatar_elem = soup.select_one('img[alt*="@"]')
            if avatar_elem:
                user_info['avatar_url'] = avatar_elem.get('src', '')
            
            bio_elem = soup.select_one('[data-bio-text]')
            if bio_elem:
                user_info['bio'] = bio_elem.text.strip()
            
            company_elem = soup.select_one('[itemprop="worksFor"]')
            if company_elem:
                user_info['company'] = company_elem.text.strip()
            
            location_elem = soup.select_one('[itemprop="homeLocation"]')
            if location_elem:
                user_info['location'] = location_elem.text.strip()
            
            blog_elem = soup.select_one('[itemprop="url"]')
            if blog_elem:
                user_info['blog'] = blog_elem.get('href', '')
            
            # 提取邮箱 - 多种方式
            # 方式1：从itemprop="email"标签提取（最准确）
            email_elem = soup.select_one('li[itemprop="email"] a[href^="mailto:"]')
            if email_elem:
                user_info['email'] = email_elem.text.strip()
            
            # 方式2：从任何mailto链接提取
            if not user_info['email']:
                email_elem = soup.select_one('a[href^="mailto:"]')
                if email_elem:
                    user_info['email'] = email_elem.get('href', '').replace('mailto:', '')
            
            # 方式3：从bio或其他文本中提取
            if not user_info['email']:
                bio_text = user_info.get('bio', '')
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                email_match = re.search(email_pattern, bio_text)
                if email_match:
                    user_info['email'] = email_match.group(0)
            
            # 方式4：如果profile没有邮箱，尝试从commit记录提取
            if not user_info['email']:
                logger.debug(f"Profile无邮箱，尝试从commit提取: {username}")
                commit_email = self._extract_email_from_commits(username)
                if commit_email:
                    user_info['email'] = commit_email
                    logger.info(f"✓ 从commit提取到邮箱: {commit_email}")
            
            # 提取博客/网站
            blog_elem = soup.select_one('li[itemprop="url"] a[rel*="nofollow"]')
            if blog_elem:
                user_info['blog'] = blog_elem.get('href', '')
            elif not user_info['blog']:
                # 备用方案
                blog_elem = soup.select_one('[itemprop="url"]')
                if blog_elem:
                    user_info['blog'] = blog_elem.get('href', '')
            
            # 提取Twitter/X
            twitter_elem = soup.select_one('a[href*="twitter.com"], a[href*="x.com"]')
            if twitter_elem:
                twitter_url = twitter_elem.get('href', '')
                twitter_match = re.search(r'(?:twitter\.com|x\.com)/([^/?]+)', twitter_url)
                if twitter_match:
                    user_info['twitter'] = twitter_match.group(1)
            
            followers_elem = soup.select_one('a[href*="followers"] span')
            if followers_elem:
                try:
                    followers_text = followers_elem.text.strip().replace(',', '').lower()
                    if 'k' in followers_text:
                        user_info['followers'] = int(float(followers_text.replace('k', '')) * 1000)
                    elif 'm' in followers_text:
                        user_info['followers'] = int(float(followers_text.replace('m', '')) * 1000000)
                    else:
                        user_info['followers'] = int(followers_text)
                except:
                    pass
            
            following_elem = soup.select_one('a[href*="following"] span')
            if following_elem:
                try:
                    following_text = following_elem.text.strip().replace(',', '').lower()
                    if 'k' in following_text:
                        user_info['following'] = int(float(following_text.replace('k', '')) * 1000)
                    elif 'm' in following_text:
                        user_info['following'] = int(float(following_text.replace('m', '')) * 1000000)
                    else:
                        user_info['following'] = int(following_text)
                except:
                    pass
            
            repos_elem = soup.select_one('a[data-tab-item="repositories"] span')
            if repos_elem:
                try:
                    user_info['public_repos'] = int(repos_elem.text.strip().replace(',', ''))
                except:
                    pass
            
            logger.info(f"获取用户{username}成功")
            return user_info
            
        except Exception as e:
            logger.error(f"获取用户失败{username}: {e}")
            return None
    
    def _extract_email_from_commits(self, username: str) -> Optional[str]:
        """
        从用户的commit记录中提取邮箱（高效版本）
        
        策略：
        - 只检查最近更新的2个仓库
        - 每个仓库只获取最近5个commits
        - 找到第一个有效邮箱就返回
        
        Args:
            username: GitHub用户名
            
        Returns:
            邮箱地址或None
        """
        try:
            # 1. 获取用户最近的2个仓库（API方式，更快）
            repos_url = f"https://api.github.com/users/{username}/repos"
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/vnd.github.v3+json'
            }
            params = {'sort': 'updated', 'per_page': 2}
            
            response = self.session.get(repos_url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                return None
            
            repos = response.json()
            
            if not isinstance(repos, list) or not repos:
                return None
            
            # 2. 对每个仓库，获取最近的commits
            for repo in repos:
                repo_full_name = repo.get('full_name')
                if not repo_full_name:
                    continue
                
                # 获取该仓库该用户的最近5个commits
                commits_url = f"https://api.github.com/repos/{repo_full_name}/commits"
                params = {'author': username, 'per_page': 5}
                
                try:
                    commits_response = self.session.get(commits_url, headers=headers, params=params, timeout=10)
                    
                    if commits_response.status_code != 200:
                        continue
                    
                    commits = commits_response.json()
                    
                    if not isinstance(commits, list) or not commits:
                        continue
                    
                    # 3. 提取邮箱
                    for commit in commits:
                        commit_data = commit.get('commit', {})
                        author = commit_data.get('author', {})
                        email = author.get('email', '')
                        
                        if email and 'noreply.github.com' not in email.lower():
                            # 找到有效邮箱，立即返回
                            return email
                    
                except Exception:
                    continue
            
            return None
            
        except Exception:
            return None
    
    @retry_on_failure(max_retries=3)
    def get_user_repositories(self, username: str, max_repos: int = 30) -> List[Dict]:
        self._wait()
        
        try:
            url = f"https://github.com/{username}?tab=repositories"
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            repositories = []
            
            repo_items = soup.select('div[id="user-repositories-list"] li')
            if not repo_items:
                repo_items = soup.select('li')
            
            for item in repo_items[:max_repos]:
                try:
                    repo_link = item.select_one('a[href*="/"]')
                    if not repo_link:
                        continue
                    
                    href = repo_link.get('href', '')
                    repo_name = href.strip('/')
                    
                    if '/' not in repo_name:
                        repo_name = f"{username}/{repo_name}"
                    
                    desc_elem = item.select_one('p')
                    description = desc_elem.text.strip() if desc_elem else ''
                    
                    stars = 0
                    stars_elem = item.select_one('a[href*="stargazers"]')
                    if stars_elem:
                        try:
                            stars = int(stars_elem.text.strip().replace(',', ''))
                        except:
                            pass
                    
                    lang_elem = item.select_one('[itemprop="programmingLanguage"]')
                    language = lang_elem.text.strip() if lang_elem else ''
                    
                    is_fork = 'fork' in item.text.lower()
                    
                    repositories.append({
                        'repo_id': hash(repo_name),
                        'repo_name': repo_name,
                        'repo_url': f"https://github.com/{repo_name}",
                        'description': description,
                        'stars': stars,
                        'forks': 0,
                        'language': language,
                        'is_fork': is_fork,
                        'created_at': None,
                        'updated_at': None
                    })
                except:
                    continue
            
            logger.info(f"获取{username}的{len(repositories)}个仓库")
            return repositories
            
        except Exception as e:
            logger.error(f"获取仓库失败{username}: {e}")
            return []
    
    @retry_on_failure(max_retries=3)
    def get_repository_contributors(self, repo_full_name: str, max_contributors: int = None) -> List[str]:
        """
        获取仓库贡献者列表（使用GitHub API）
        
        通过GitHub的contributors-data API获取完整的贡献者列表
        这是推荐的方法，速度快且稳定
        
        Args:
            repo_full_name: 仓库全名，格式为 "owner/repo"
            max_contributors: 最大获取数量，None表示不限制
            
        Returns:
            贡献者用户名列表
        """
        contributors = []
        owner = repo_full_name.split('/')[0]
        
        try:
            self._wait()
            
            # 使用GitHub的contributors-data API
            api_url = f"https://github.com/{repo_full_name}/graphs/contributors-data"
            logger.debug(f"获取贡献者: {repo_full_name}")
            
            # 需要特殊的headers来访问这个API
            headers = self._get_headers()
            headers['Accept'] = 'application/json'
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
            response = self.session.get(api_url, headers=headers, timeout=15)
            
            # 检查响应状态
            if response.status_code == 404:
                logger.debug(f"仓库不存在或无贡献者数据: {repo_full_name}")
                return []
            
            if response.status_code == 429:
                logger.warning(f"速率限制: {repo_full_name}")
                return []
            
            response.raise_for_status()
            
            # 检查响应内容类型
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                logger.debug(f"非JSON响应 ({content_type}): {repo_full_name}")
                return []
            
            # 检查响应是否为空
            if not response.text or response.text.strip() == '':
                logger.debug(f"空响应: {repo_full_name}")
                return []
            
            # 解析JSON数据
            try:
                data = response.json()
            except ValueError as json_err:
                logger.debug(f"JSON解析失败 {repo_full_name}: {json_err}")
                return []
            
            if not isinstance(data, list):
                logger.debug(f"API返回数据格式错误 ({type(data).__name__}): {repo_full_name}")
                return []
            
            if len(data) == 0:
                logger.debug(f"无贡献者数据: {repo_full_name}")
                return []
            
            logger.debug(f"API返回 {len(data)} 个贡献者")
            
            # 提取用户名
            seen_usernames = set()
            for contributor_data in data:
                # 如果设置了限制且已达到，停止
                if max_contributors and len(contributors) >= max_contributors:
                    break
                
                if not isinstance(contributor_data, dict):
                    continue
                
                author = contributor_data.get('author')
                if not author or not isinstance(author, dict):
                    continue
                
                username = author.get('login')
                if not username:
                    continue
                
                # 过滤：排除owner、去重、验证格式
                if username and username != owner and username not in seen_usernames:
                    if username.replace('-', '').replace('_', '').isalnum():
                        contributors.append(username)
                        seen_usernames.add(username)
            
            if contributors:
                logger.info(f"✓ 从{repo_full_name}获取{len(contributors)}个贡献者")
            else:
                logger.debug(f"未找到有效贡献者: {repo_full_name}")
            
            return contributors
            
        except requests.exceptions.Timeout:
            logger.debug(f"请求超时: {repo_full_name}")
            return []
        except requests.exceptions.RequestException as req_err:
            logger.debug(f"请求失败 {repo_full_name}: {req_err}")
            return []
        except Exception as e:
            logger.warning(f"获取贡献者失败 {repo_full_name}: {e}")
            return []
    
    def check_is_indie_developer(self, user_info: Dict, repositories: List[Dict]) -> bool:
        """
        判断是否为适合WaveSpeedAI合作的独立开发者
        
        WaveSpeedAI业务：图像/视频生成API平台
        目标客户：AI应用开发者、内容创作工具开发者、API集成者
        
        判断标准（针对独立开发者）：
        1. 不属于大公司（包括竞争对手）
        2. 有一定影响力（followers或stars达到配置阈值）
        3. 有明确的AI相关项目经验
        4. **核心：必须是独立开发者，不是某个大项目的成员/贡献者**
        """
        # 加载配置（一次性加载）
        from utils.config_loader import load_config
        config = load_config()
        github_config = config.get('github', {})
        exclusion_rules = config.get('exclusion_rules', {})
        
        username = user_info.get('username', '')
        
        # 1. 排除大公司员工、竞争对手和项目团队成员（从配置读取）
        company = (user_info.get('company') or '').lower()
        bio = (user_info.get('bio') or '').lower()
        
        # 从配置读取排除的组织列表（从github.exclusion_organizations读取）
        exclusion_organizations = github_config.get('exclusion_organizations', [])
        
        # 转为小写列表
        exclusion_orgs_lower = [org.lower() for org in exclusion_organizations if org]
        
        for org in exclusion_orgs_lower:
            # 检查company字段
            if org in company:
                logger.info(f"❌ {username} 属于排除的组织: {company}")
                return False
            
            # 检查bio中是否标注为该组织的成员
            if f"{org} team" in bio or f"{org} member" in bio or f"{org} contributor" in bio:
                logger.info(f"❌ {username} 是 {org} 组织成员")
                return False
        
        # 2. 获取原创仓库
        original_repos = [r for r in repositories if not r.get('is_fork', False)]
        
        # 3. 检查影响力（从配置文件读取阈值）
        min_followers = github_config.get('min_followers', 100)
        min_stars = github_config.get('min_stars', 500)
        
        followers = user_info.get('followers', 0)
        total_stars = sum(r.get('stars', 0) for r in original_repos)
        
        if followers < min_followers and total_stars < min_stars:
            logger.info(f"❌ {username} 影响力不足: followers={followers} (需要>={min_followers}), stars={total_stars} (需要>={min_stars})")
            return False
        
        # 4. 检查是否有知名项目的成员标识（从配置读取）
        # 通过bio、company字段检查是否标注为某个项目的成员
        bio = (user_info.get('bio') or '').lower()
        
        # 使用同样的排除组织列表
        for project in exclusion_orgs_lower:
            # 检查是否在bio或company中标注为该项目成员
            if f"{project} team" in bio or f"{project} member" in bio or f"{project} contributor" in bio:
                logger.info(f"❌ {username} 是 {project} 项目成员")
                return False
            if project in company and ('team' in company or 'member' in company):
                logger.info(f"❌ {username} 在company中标注为 {project} 成员")
                return False
        
        # 5. 检查是否有AI相关项目（从配置文件读取关键词）
        core_ai_keywords = github_config.get('core_ai_keywords', [
            # 默认关键词（如果配置文件中没有）
            'machine-learning', 'deep-learning', 'neural-network', 'ml-model',
            'pytorch', 'tensorflow', 'keras', 'scikit-learn',
            'stable-diffusion', 'diffusion-model', 'text-to-image', 'text-to-video',
            'image-generation', 'video-generation', 'generative-ai', 'gan',
            'controlnet', 'animatediff',
            'gpt', 'llm', 'large-language-model', 'chatbot', 'transformer',
            'bert', 'nlp', 'natural-language',
            'computer-vision', 'object-detection', 'image-recognition',
            'yolo', 'opencv-ai', 'face-recognition'
        ])
        
        has_ai_project = False
        ai_repo_name = None
        
        for repo in original_repos:
            repo_name = repo.get('repo_name', '').lower()
            description = repo.get('description', '').lower()
            language = repo.get('language', '').lower()
            
            repo_text = f"{repo_name} {description} {language}"
            
            # 检查核心AI关键词（任意一个即可）
            matched_core = [kw for kw in core_ai_keywords if kw in repo_text]
            
            if matched_core:
                has_ai_project = True
                ai_repo_name = repo.get('repo_name')
                logger.info(f"✓ {username} 有AI项目: {ai_repo_name}")
                logger.info(f"  匹配关键词: {matched_core}")
                break
        
        if not has_ai_project:
            logger.info(f"❌ {username} 没有明确的AI相关项目")
            return False
        
        logger.info(f"✓ {username} 合格 - 独立开发者 - Followers:{followers}, Stars:{total_stars}")
        return True
    
    def check_is_academic(self, user_info: Dict, repositories: List[Dict]) -> tuple[bool, list, list]:
        """
        判断是否为学术人士
        
        学术人士特征：
        1. Bio/Company包含学术机构关键词
        2. 项目主要是研究性质（论文复现、模型训练、研究工具）
        3. 深度学习/神经网络相关的研究项目
        4. 满足影响力要求（followers或stars达到配置阈值）
        
        Args:
            user_info: 用户信息
            repositories: 仓库列表
            
        Returns:
            (is_academic, academic_indicators, research_areas)
            - is_academic: 是否为学术人士
            - academic_indicators: 学术指标列表
            - research_areas: 研究领域列表
        """
        from utils.config_loader import load_config
        config = load_config()
        github_config = config.get('github', {})
        
        username = user_info.get('username', '')
        bio = (user_info.get('bio') or '').lower()
        company = (user_info.get('company') or '').lower()
        location = (user_info.get('location') or '').lower()
        
        academic_indicators = []
        research_areas = []
        
        # 1. 从配置文件读取学术机构关键词
        academic_keywords = github_config.get('academic_keywords', [
            'university', 'college', 'institute', 'research', 'lab', 'laboratory',
            'phd', 'ph.d', 'professor', 'postdoc', 'post-doc', 'student',
            'academic', 'scholar', 'researcher', 'faculty',
            '大学', '学院', '研究所', '实验室', '博士', '教授', '研究员', '学者'
        ])
        
        for keyword in academic_keywords:
            if keyword.lower() in bio or keyword.lower() in company or keyword.lower() in location:
                academic_indicators.append(f"Profile contains: {keyword}")
                break
        
        # 2. 检查项目特征
        research_keywords = {
            'deep-learning': ['deep-learning', 'deep learning', 'deeplearning', 'dl'],
            'neural-network': ['neural-network', 'neural network', 'neuralnetwork', 'nn'],
            'machine-learning': ['machine-learning', 'machine learning', 'machinelearning', 'ml'],
            'computer-vision': ['computer-vision', 'computer vision', 'cv', 'image-processing'],
            'nlp': ['nlp', 'natural-language', 'natural language processing', 'text-processing'],
            'reinforcement-learning': ['reinforcement-learning', 'reinforcement learning', 'rl'],
            'multimodal': ['multimodal', 'multi-modal', 'vision-language', 'vlm'],
            'transformer': ['transformer', 'attention', 'bert', 'gpt'],
            'diffusion': ['diffusion', 'stable-diffusion', 'ddpm', 'ddim'],
            'gan': ['gan', 'generative adversarial', 'stylegan'],
        }
        
        # 从配置文件读取研究项目关键词
        research_project_indicators = github_config.get('research_project_keywords', [
            'paper', 'arxiv', 'implementation', 'reproduction', 'reproduce',
            'research', 'experiment', 'benchmark', 'dataset', 'pretrained',
            'model', 'training', 'pytorch', 'tensorflow', 'keras',
            '论文', '复现', '实验', '研究'
        ])
        
        # 统计研究项目数量
        research_project_count = 0
        matched_areas = set()
        
        for repo in repositories:
            repo_name = repo.get('repo_name', '').lower()
            description = repo.get('description', '').lower()
            repo_text = f"{repo_name} {description}"
            
            # 检查是否为研究项目
            is_research = any(indicator.lower() in repo_text for indicator in research_project_indicators)
            
            if is_research:
                research_project_count += 1
                
                # 识别研究领域
                for area, keywords in research_keywords.items():
                    if any(kw in repo_text for kw in keywords):
                        matched_areas.add(area)
        
        if research_project_count > 0:
            academic_indicators.append(f"Research projects: {research_project_count}")
        
        if matched_areas:
            research_areas = list(matched_areas)
            academic_indicators.append(f"Research areas: {', '.join(research_areas)}")
        
        # 3. 判断是否为学术人士
        # 条件：有学术机构关键词 或 有2个以上研究项目
        is_academic = len(academic_indicators) > 0 and (
            any('Profile contains' in ind for ind in academic_indicators) or
            research_project_count >= 2
        )
        
        if not is_academic:
            return False, [], []
        
        # 4. 检查影响力（从配置文件读取学术人士的阈值）
        academic_min_followers = github_config.get('academic_min_followers', 50)
        academic_min_stars = github_config.get('academic_min_stars', 100)
        
        followers = user_info.get('followers', 0)
        original_repos = [r for r in repositories if not r.get('is_fork', False)]
        total_stars = sum(r.get('stars', 0) for r in original_repos)
        
        if followers < academic_min_followers and total_stars < academic_min_stars:
            logger.info(f"❌ {username} 学术人士影响力不足: followers={followers} (需要>={academic_min_followers}), stars={total_stars} (需要>={academic_min_stars})")
            return False, [], []
        
        logger.info(f"✓ {username} 识别为学术人士")
        logger.info(f"  学术指标: {academic_indicators}")
        logger.info(f"  研究领域: {research_areas}")
        logger.info(f"  影响力: Followers={followers}, Stars={total_stars}")
        
        return is_academic, academic_indicators, research_areas
