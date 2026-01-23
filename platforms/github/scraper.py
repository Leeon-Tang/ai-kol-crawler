# -*- coding: utf-8 -*-
"""
GitHub爬虫 - 简化版（无代理）
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

# Selenium相关导入（用于动态页面）
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium未安装，无法获取动态渲染的贡献者列表")


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
        self.driver = None  # Selenium driver
        
        logger.info(f"爬虫初始化（延迟3-5秒，{len(self.user_agents)}个UA）")
        logger.info("⏳ 等待3秒让IP冷却...")
        time.sleep(3)  # 改为3秒冷却期
        logger.info("✓ 冷却完成，开始爬取")
    
    # Selenium功能已禁用 - 不再初始化driver
    # def _get_selenium_driver(self):
    #     """获取或创建Selenium driver（懒加载）"""
    #     if not SELENIUM_AVAILABLE:
    #         logger.error("Selenium未安装，无法使用动态渲染功能")
    #         return None
    #     
    #     if self.driver is None:
    #         try:
    #             chrome_options = Options()
    #             chrome_options.add_argument('--headless')  # 无头模式
    #             chrome_options.add_argument('--no-sandbox')
    #             chrome_options.add_argument('--disable-dev-shm-usage')
    #             chrome_options.add_argument('--disable-gpu')
    #             chrome_options.add_argument(f'user-agent={random.choice(self.user_agents)}')
    #             
    #             # 使用webdriver-manager自动管理ChromeDriver
    #             service = Service(ChromeDriverManager().install())
    #             self.driver = webdriver.Chrome(service=service, options=chrome_options)
    #             logger.info("✓ Selenium driver已初始化")
    #         except Exception as e:
    #             logger.error(f"初始化Selenium driver失败: {e}")
    #             logger.error("请确保已安装Chrome浏览器")
    #             return None
    #     
    #     return self.driver
    
    # Selenium功能已禁用 - 不再需要清理
    # def __del__(self):
    #     """清理资源"""
    #     if hasattr(self, 'driver') and self.driver is not None:
    #         try:
    #             self.driver.quit()
    #             logger.info("✓ Selenium driver已关闭")
    #         except:
    #             pass
    
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
    def get_repository_contributors(self, repo_full_name: str, max_contributors: int = 20) -> List[str]:
        """
        获取仓库贡献者
        
        策略：
        1. 从仓库主页侧边栏获取（快速，通常10-13个）
        2. 如果侧边栏显示有>14个贡献者，才去/graphs/contributors页面获取更多
        """
        self._wait()
        
        contributors = []
        owner = repo_full_name.split('/')[0]
        
        try:
            # 从主页侧边栏获取
            url = f"https://github.com/{repo_full_name}"
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找Contributors侧边栏
            contributors_heading = soup.find('a', href=lambda x: x and '/graphs/contributors' in x if x else False)
            
            total_contributors_count = 0
            if contributors_heading:
                # 尝试获取总贡献者数量
                heading_text = contributors_heading.get_text()
                import re
                count_match = re.search(r'(\d+)', heading_text)
                if count_match:
                    total_contributors_count = int(count_match.group(1))
                
                parent = contributors_heading.find_parent('div', class_='BorderGrid-cell')
                
                if parent:
                    user_links = parent.select('a[data-hovercard-type="user"]')
                    
                    # 如果没有找到用户链接，可能是动态加载的，尝试从include-fragment获取
                    if len(user_links) == 0:
                        include_fragment = parent.select_one('include-fragment[src*="contributors_list"]')
                        if include_fragment:
                            fragment_src = include_fragment.get('src', '')
                            if fragment_src:
                                # 请求动态内容
                                try:
                                    self._wait()  # 遵守速率限制
                                    fragment_url = f"https://github.com{fragment_src}"
                                    fragment_response = self.session.get(fragment_url, headers=self._get_headers(), timeout=15)
                                    fragment_response.raise_for_status()
                                    
                                    fragment_soup = BeautifulSoup(fragment_response.text, 'html.parser')
                                    user_links = fragment_soup.select('a[data-hovercard-type="user"]')
                                except Exception as e:
                                    logger.warning(f"获取动态贡献者列表失败: {e}")
                    
                    for link in user_links:
                        href = link.get('href', '')
                        
                        if href:
                            # 处理完整URL和相对路径
                            if href.startswith('https://github.com/'):
                                username = href.replace('https://github.com/', '').split('/')[0]
                            elif href.startswith('/'):
                                username = href.strip('/').split('/')[0]
                            else:
                                continue
                            
                            # 排除owner和系统路径
                            if username and username != owner and username not in contributors:
                                if username not in ['github', 'apps', 'marketplace', 'features', 'enterprise', 'pricing']:
                                    contributors.append(username)
            
            # TODO: Selenium动态渲染功能已暂时禁用
            # 原因：滚动次数和等待时间不稳定，有时能获取20个，有时只有几个
            # 而且侧边栏获取也不稳定（有时13个，有时0个）
            # 当前策略：只依赖侧边栏的10-13个贡献者
            
            # if total_contributors_count > 14 and len(contributors) < max_contributors and SELENIUM_AVAILABLE:
            #     logger.info(f"从侧边栏获取{len(contributors)}个，使用Selenium获取更多...")
            #     
            #     driver = self._get_selenium_driver()
            #     if driver:
            #         try:
            #             self._wait()
            #             contrib_url = f"https://github.com/{repo_full_name}/graphs/contributors"
            #             driver.get(contrib_url)
            #             
            #             # 等待页面基本元素加载
            #             wait = WebDriverWait(driver, 20)
            #             wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            #             
            #             # 等待图表容器出现
            #             try:
            #                 wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.Index-module__chartListItem--aHSZR")))
            #                 time.sleep(2)  # 等待初始内容加载
            #             except:
            #                 pass
            #             
            #             # 持续滚动以触发懒加载
            #             scroll_count = 12
            #             
            #             for attempt in range(scroll_count):
            #                 driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            #                 time.sleep(2)
            #                 logger.debug(f"滚动第{attempt+1}/{scroll_count}次")
            #             
            #             # 滚动回顶部并等待渲染完成
            #             driver.execute_script("window.scrollTo(0, 0);")
            #             time.sleep(3)
            #             
            #             # 获取渲染后的HTML
            #             page_source = driver.page_source
            #             contrib_soup = BeautifulSoup(page_source, 'html.parser')
            #             
            #             # 从图表列表项中提取贡献者
            #             chart_items = contrib_soup.select('li.Index-module__chartListItem--aHSZR')
            #             logger.info(f"找到 {len(chart_items)} 个图表列表项")
            #             
            #             for item in chart_items:
            #                 if len(contributors) >= max_contributors:
            #                     break
            #                 
            #                 # 在每个图表项中查找用户链接（只取第一个，避免重复）
            #                 user_links = item.select('a.prc-Link-Link-9ZwDx[href^="/"]')
            #                 
            #                 if user_links:
            #                     # 只处理第一个链接（用户名链接）
            #                     link = user_links[0]
            #                     href = link.get('href', '')
            #                     if href:
            #                         username = href.strip('/').split('/')[0]
            #                         
            #                         # 排除owner和系统路径
            #                         if username and username != owner and username not in contributors:
            #                             if username not in ['github', 'apps', 'marketplace', 'features', 'enterprise', 
            #                                                'pricing', 'commits', 'graphs', 'issues', 'pulls', 'actions',
            #                                                'projects', 'security', 'insights', 'settings']:
            #                                 if username.replace('-', '').replace('_', '').isalnum():
            #                                     contributors.append(username)
            #                                     logger.debug(f"添加贡献者: {username}")
            #             
            #             logger.info(f"✓ 通过Selenium获取到总共{len(contributors)}个贡献者")
            #         
            #         except Exception as e:
            #             logger.warning(f"Selenium获取失败: {e}")
            
            logger.info(f"从{repo_full_name}获取{len(contributors)}个贡献者")
            return contributors
            
        except Exception as e:
            logger.warning(f"获取贡献者失败{repo_full_name}: {e}")
            return []
    
    def check_is_indie_developer(self, user_info: Dict, repositories: List[Dict]) -> bool:
        """
        判断是否为适合WaveSpeedAI合作的独立开发者
        
        WaveSpeedAI业务：图像/视频生成API平台
        目标客户：AI应用开发者、内容创作工具开发者、API集成者
        
        判断标准（针对优质项目贡献者）：
        1. 不属于大公司（包括竞争对手）
        2. 有一定影响力（followers >= 100 或 total_stars >= 100）
        3. 有原创项目（至少1个非fork仓库）
        4. 有明确的AI相关项目经验
        """
        username = user_info.get('username', '')
        
        # 1. 排除大公司员工和竞争对手
        company = (user_info.get('company') or '').lower()
        big_companies = [
            # 科技巨头
            'google', 'microsoft', 'meta', 'facebook', 'amazon', 'apple',
            'alibaba', 'tencent', 'bytedance', 'baidu', 'huawei', 'openai',
            # AI竞争对手（图像/视频生成领域）
            'stability', 'midjourney', 'runway', 'pika', 'leonardo',
            'replicate', 'together', 'anthropic', 'cohere',
            # 云服务商
            'aws', 'azure', 'gcp', 'cloudflare', 'vercel'
        ]
        
        for big_company in big_companies:
            if big_company in company:
                logger.info(f"❌ {username} 属于大公司/竞争对手: {company}")
                return False
        
        # 2. 检查影响力（followers >= 100 或 total_stars >= 100）
        followers = user_info.get('followers', 0)
        original_repos = [r for r in repositories if not r.get('is_fork', False)]
        total_stars = sum(r.get('stars', 0) for r in original_repos)
        
        if followers < 100 and total_stars < 100:
            logger.info(f"❌ {username} 影响力不足: followers={followers}, stars={total_stars}")
            return False
        
        # 3. 检查原创仓库数量（至少1个）
        if len(original_repos) < 1:
            logger.info(f"❌ {username} 没有原创仓库")
            return False
        
        # 4. 检查是否有AI相关项目（严格匹配核心AI关键词）
        # 核心AI关键词：必须明确与AI/ML相关
        core_ai_keywords = [
            # 机器学习/深度学习
            'machine-learning', 'deep-learning', 'neural-network', 'ml-model',
            'pytorch', 'tensorflow', 'keras', 'scikit-learn',
            # 生成式AI（重点）
            'stable-diffusion', 'diffusion-model', 'text-to-image', 'text-to-video',
            'image-generation', 'video-generation', 'generative-ai', 'gan',
            'controlnet', 'comfyui', 'automatic1111', 'animatediff',
            # LLM/NLP
            'gpt', 'llm', 'large-language-model', 'chatbot', 'transformer',
            'bert', 'nlp', 'natural-language',
            # 计算机视觉
            'computer-vision', 'object-detection', 'image-recognition',
            'yolo', 'opencv-ai', 'face-recognition'
        ]
        
        # 辅助关键词：需要与其他词组合才算
        helper_keywords = ['ai-tool', 'ai-app', 'ai-api', 'ai-sdk', 'ai-saas']
        
        has_ai_project = False
        ai_repo_name = None
        
        for repo in original_repos:
            repo_name = repo.get('repo_name', '').lower()
            description = repo.get('description', '').lower()
            language = repo.get('language', '').lower()
            
            repo_text = f"{repo_name} {description} {language}"
            
            # 检查核心AI关键词（任意一个即可）
            matched_core = [kw for kw in core_ai_keywords if kw in repo_text]
            
            # 检查辅助关键词（需要同时包含'ai'）
            matched_helper = [kw for kw in helper_keywords if kw in repo_text]
            
            if matched_core or matched_helper:
                has_ai_project = True
                ai_repo_name = repo.get('repo_name')
                logger.info(f"✓ {username} 有AI项目: {ai_repo_name}")
                if matched_core:
                    logger.info(f"  匹配核心关键词: {matched_core}")
                if matched_helper:
                    logger.info(f"  匹配辅助关键词: {matched_helper}")
                break
        
        if not has_ai_project:
            logger.info(f"❌ {username} 没有明确的AI相关项目")
            return False
        
        logger.info(f"✓ {username} 合格 - Followers:{followers}, Stars:{total_stars}")
        return True
