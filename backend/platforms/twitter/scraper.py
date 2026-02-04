# -*- coding: utf-8 -*-
"""
Twitter/X爬虫 - 使用Selenium爬取公开页面(无需登录)
"""
import time
import re
from typing import Dict, List, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from backend.utils.logger import setup_logger
from backend.utils.rate_limiter import RateLimiter
from backend.utils.retry import retry_on_failure
from backend.utils.contact_extractor import ContactExtractor

logger = setup_logger(__name__)


class TwitterScraper:
    """Twitter爬虫 - 使用Selenium爬取公开页面"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.contact_extractor = ContactExtractor()
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """初始化Selenium WebDriver"""
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = webdriver.ChromeOptions()
            
            # 基础选项
            options.add_argument('--headless=new')  # 新版无头模式
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # 反检测选项
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User Agent
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 禁用图片和CSS加载以提高速度
            prefs = {
                'profile.managed_default_content_settings.images': 2,
                'profile.managed_default_content_settings.stylesheets': 2,
            }
            options.add_experimental_option('prefs', prefs)
            
            # 使用 webdriver-manager 自动管理 ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # 执行CDP命令隐藏webdriver特征
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            logger.info("Selenium WebDriver 初始化成功")
            
        except Exception as e:
            logger.error(f"Selenium WebDriver 初始化失败: {e}")
            logger.info("提示: 请确保已安装 Chrome 浏览器")
            raise
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    @retry_on_failure(max_retries=3)
    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        获取用户基本信息(从公开页面)
        
        Args:
            username: Twitter用户名 (不带@)
            
        Returns:
            用户信息字典
        """
        self.rate_limiter.wait()
        
        try:
            url = f"https://twitter.com/{username}"
            self.driver.get(url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 10)
            
            # 等待用户名元素出现
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="UserName"]')))
            
            # 提取用户信息
            user_data = {
                'username': username,
                'profile_url': url,
            }
            
            # 提取显示名称
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="UserName"]')
                user_data['name'] = name_elem.text.split('\n')[0] if name_elem else username
            except:
                user_data['name'] = username
            
            # 提取简介
            try:
                bio_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="UserDescription"]')
                user_data['bio'] = bio_elem.text if bio_elem else ''
            except:
                user_data['bio'] = ''
            
            # 提取位置
            try:
                location_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="UserLocation"]')
                user_data['location'] = location_elem.text if location_elem else ''
            except:
                user_data['location'] = ''
            
            # 提取网站
            try:
                website_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="UserUrl"]')
                user_data['website'] = website_elem.get_attribute('href') if website_elem else ''
            except:
                user_data['website'] = ''
            
            # 提取关注数据
            try:
                following_elem = self.driver.find_element(By.XPATH, '//a[contains(@href, "/following")]//span')
                user_data['following_count'] = self._parse_count(following_elem.text) if following_elem else 0
            except:
                user_data['following_count'] = 0
            
            try:
                followers_elem = self.driver.find_element(By.XPATH, '//a[contains(@href, "/verified_followers")]//span')
                user_data['followers_count'] = self._parse_count(followers_elem.text) if followers_elem else 0
            except:
                user_data['followers_count'] = 0
            
            # 提取头像
            try:
                avatar_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="UserAvatar-Container-unknown"] img')
                user_data['avatar_url'] = avatar_elem.get_attribute('src') if avatar_elem else ''
            except:
                user_data['avatar_url'] = ''
            
            # 提取联系方式
            contact_info = self._extract_contact_info(user_data)
            user_data['contact_info'] = contact_info
            
            logger.info(f"获取用户信息成功: @{username}")
            return user_data
            
        except Exception as e:
            logger.error(f"获取用户信息失败 @{username}: {e}")
            return None
    
    @retry_on_failure(max_retries=3)
    def get_user_tweets(self, username: str, limit: int = 20) -> List[Dict]:
        """
        获取用户最近的推文(从公开页面)
        
        Args:
            username: Twitter用户名
            limit: 获取数量
            
        Returns:
            推文列表
        """
        self.rate_limiter.wait()
        
        try:
            url = f"https://twitter.com/{username}"
            self.driver.get(url)
            
            # 等待推文加载
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]')))
            
            tweets = []
            scroll_attempts = 0
            max_scrolls = 5
            
            while len(tweets) < limit and scroll_attempts < max_scrolls:
                # 获取当前页面的推文
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                
                for elem in tweet_elements:
                    if len(tweets) >= limit:
                        break
                    
                    try:
                        # 提取推文文本
                        text_elem = elem.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                        text = text_elem.text if text_elem else ''
                        
                        # 提取时间
                        time_elem = elem.find_element(By.CSS_SELECTOR, 'time')
                        created_at = time_elem.get_attribute('datetime') if time_elem else ''
                        
                        # 提取互动数据
                        reply_count = self._extract_metric(elem, 'reply')
                        retweet_count = self._extract_metric(elem, 'retweet')
                        like_count = self._extract_metric(elem, 'like')
                        
                        tweet_data = {
                            'username': username,
                            'text': text,
                            'created_at': created_at,
                            'reply_count': reply_count,
                            'retweet_count': retweet_count,
                            'like_count': like_count,
                        }
                        
                        # 避免重复
                        if tweet_data not in tweets:
                            tweets.append(tweet_data)
                            
                    except Exception as e:
                        logger.debug(f"提取推文失败: {e}")
                        continue
                
                # 滚动加载更多
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scroll_attempts += 1
            
            logger.info(f"获取推文成功: @{username}, 数量: {len(tweets)}")
            return tweets[:limit]
            
        except Exception as e:
            logger.error(f"获取推文失败 @{username}: {e}")
            return []
    
    def search_tweets(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索推文(从公开搜索页面)
        
        Args:
            keyword: 搜索关键词
            limit: 结果数量
            
        Returns:
            推文列表
        """
        self.rate_limiter.wait()
        
        try:
            # Twitter搜索URL
            search_url = f"https://twitter.com/search?q={keyword}&src=typed_query&f=live"
            self.driver.get(search_url)
            
            # 等待搜索结果加载
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]')))
            
            tweets = []
            scroll_attempts = 0
            max_scrolls = 5
            
            while len(tweets) < limit and scroll_attempts < max_scrolls:
                # 获取当前页面的推文
                tweet_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                
                for elem in tweet_elements:
                    if len(tweets) >= limit:
                        break
                    
                    try:
                        # 提取用户名
                        username_elem = elem.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"] a')
                        username = username_elem.get_attribute('href').split('/')[-1] if username_elem else ''
                        
                        # 提取显示名称
                        name_elem = elem.find_element(By.CSS_SELECTOR, '[data-testid="User-Name"]')
                        user_name = name_elem.text.split('\n')[0] if name_elem else ''
                        
                        # 提取推文文本
                        text_elem = elem.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                        text = text_elem.text if text_elem else ''
                        
                        # 提取时间
                        time_elem = elem.find_element(By.CSS_SELECTOR, 'time')
                        created_at = time_elem.get_attribute('datetime') if time_elem else ''
                        
                        # 提取互动数据
                        reply_count = self._extract_metric(elem, 'reply')
                        retweet_count = self._extract_metric(elem, 'retweet')
                        like_count = self._extract_metric(elem, 'like')
                        
                        tweet_data = {
                            'username': username,
                            'user_name': user_name,
                            'text': text,
                            'created_at': created_at,
                            'reply_count': reply_count,
                            'retweet_count': retweet_count,
                            'like_count': like_count,
                            'tweet_url': f"https://twitter.com/{username}/status/{created_at}"
                        }
                        
                        # 避免重复
                        if tweet_data not in tweets:
                            tweets.append(tweet_data)
                            
                    except Exception as e:
                        logger.debug(f"提取搜索结果失败: {e}")
                        continue
                
                # 滚动加载更多
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scroll_attempts += 1
            
            logger.info(f"搜索推文成功: {keyword}, 数量: {len(tweets)}")
            return tweets[:limit]
            
        except Exception as e:
            logger.error(f"搜索推文失败 {keyword}: {e}")
            return []
    
    def _parse_count(self, text: str) -> int:
        """解析数字(如 1.2K, 3.5M)"""
        try:
            text = text.strip().upper()
            if 'K' in text:
                return int(float(text.replace('K', '')) * 1000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1000000)
            else:
                return int(text.replace(',', ''))
        except:
            return 0
    
    def _extract_metric(self, element, metric_type: str) -> int:
        """提取互动指标"""
        try:
            metric_elem = element.find_element(By.CSS_SELECTOR, f'[data-testid="{metric_type}"]')
            text = metric_elem.get_attribute('aria-label') or metric_elem.text
            # 从 aria-label 中提取数字
            numbers = re.findall(r'\d+', text)
            return int(numbers[0]) if numbers else 0
        except:
            return 0
    
    def _extract_contact_info(self, user_data: Dict) -> str:
        """提取联系方式"""
        contact_parts = []
        
        # 从bio中提取
        if user_data.get('bio'):
            contacts = self.contact_extractor.extract_all(user_data['bio'])
            if contacts.get('emails'):
                contact_parts.extend([f"Email: {e}" for e in contacts['emails']])
            if contacts.get('telegrams'):
                contact_parts.extend([f"Telegram: {t}" for t in contacts['telegrams']])
            if contacts.get('wechats'):
                contact_parts.extend([f"WeChat: {w}" for w in contacts['wechats']])
        
        # 网站
        if user_data.get('website'):
            contact_parts.append(f"Website: {user_data['website']}")
        
        # 位置
        if user_data.get('location'):
            contact_parts.append(f"Location: {user_data['location']}")
        
        return ' | '.join(contact_parts) if contact_parts else ''
