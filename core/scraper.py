"""
yt-dlp爬虫核心模块
"""
import yt_dlp
from datetime import datetime
from utils.rate_limiter import RateLimiter
from utils.retry import retry_on_failure
from utils.logger import setup_logger


logger = setup_logger()


class YouTubeScraper:
    """YouTube爬虫（基于yt-dlp）"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'socket_timeout': 10,  # 10秒超时
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['hls', 'dash']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
    
    @retry_on_failure()
    def search_videos(self, keyword, max_results=50):
        """
        搜索视频
        返回: 视频列表
        """
        self.rate_limiter.wait()
        
        search_query = f"ytsearch{max_results}:{keyword}"
        
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                result = ydl.extract_info(search_query, download=False)
                videos = result.get('entries', [])
                
                logger.info(f"搜索关键词 '{keyword}' 找到 {len(videos)} 个视频")
                return videos
            except Exception as e:
                logger.error(f"搜索失败: {keyword}, 错误: {str(e)}")
                raise
    
    @retry_on_failure()
    def get_channel_info(self, channel_id):
        """
        获取频道基本信息
        返回: 频道信息字典
        """
        self.rate_limiter.wait()
        
        # 尝试多种URL格式
        urls = [
            f"https://www.youtube.com/channel/{channel_id}",
            f"https://www.youtube.com/@{channel_id}",
            f"https://www.youtube.com/c/{channel_id}"
        ]
        
        for channel_url in urls:
            opts = self.ydl_opts.copy()
            opts['extract_flat'] = 'in_playlist'
            opts['ignoreerrors'] = True
            opts['socket_timeout'] = 15  # 15秒超时
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info = ydl.extract_info(channel_url, download=False)
                    
                    if info:
                        channel_data = {
                            'channel_id': channel_id,
                            'channel_name': info.get('channel', info.get('uploader', info.get('title', ''))),
                            'channel_url': channel_url,
                            'subscribers': info.get('channel_follower_count', 0),
                            'total_videos': info.get('playlist_count', 0),
                            'total_views': info.get('view_count', 0),
                        }
                        
                        logger.info(f"  获取频道信息成功: {channel_data['channel_name']}")
                        return channel_data
                except Exception as e:
                    logger.debug(f"尝试URL失败: {channel_url}, 错误: {str(e)}")
                    continue
        
        # 如果所有URL都失败，返回基本信息
        logger.warning(f"无法获取频道详细信息: {channel_id}，使用基本信息")
        return {
            'channel_id': channel_id,
            'channel_name': f'Channel_{channel_id[:8]}',
            'channel_url': f"https://www.youtube.com/channel/{channel_id}",
            'subscribers': 0,
            'total_videos': 0,
            'total_views': 0,
        }
    
    @retry_on_failure()
    def get_channel_videos(self, channel_id, limit=50):
        """
        获取频道的视频列表
        返回: 视频列表
        """
        self.rate_limiter.wait()
        
        # 尝试多种URL格式
        urls = [
            f"https://www.youtube.com/channel/{channel_id}/videos",
            f"https://www.youtube.com/@{channel_id}/videos"
        ]
        
        for channel_url in urls:
            opts = self.ydl_opts.copy()
            opts['playlistend'] = limit
            opts['ignoreerrors'] = True
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    result = ydl.extract_info(channel_url, download=False)
                    
                    if result and 'entries' in result:
                        videos = [v for v in result.get('entries', []) if v is not None]
                        logger.info(f"获取频道 {channel_id} 的 {len(videos)} 个视频")
                        return videos[:limit]
                except Exception as e:
                    logger.debug(f"尝试URL失败: {channel_url}, 错误: {str(e)}")
                    continue
        
        logger.error(f"获取频道视频失败: {channel_id}")
        return []
    
    @retry_on_failure()
    def get_video_info(self, video_id):
        """
        获取单个视频详细信息
        返回: 视频信息字典
        """
        self.rate_limiter.wait()
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        opts = self.ydl_opts.copy()
        opts['extract_flat'] = False
        opts['ignoreerrors'] = True
        opts['quiet'] = True  # 抑制错误输出
        opts['no_warnings'] = True
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=False)
                
                if not info:
                    raise Exception("无法获取视频信息")
                
                # 检查是否是会员专属视频
                if info.get('availability') == 'subscriber_only':
                    raise Exception("会员专属视频，跳过")
                
                # 处理时间戳
                published_at = None
                if info.get('timestamp'):
                    published_at = datetime.fromtimestamp(info.get('timestamp'))
                elif info.get('upload_date'):
                    from datetime import datetime as dt
                    published_at = dt.strptime(info.get('upload_date'), '%Y%m%d')
                
                video_data = {
                    'video_id': video_id,
                    'channel_id': info.get('channel_id', ''),
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'published_at': published_at or datetime.now(),
                    'duration': info.get('duration', 0),
                    'views': info.get('view_count') or 0,
                    'likes': info.get('like_count') or 0,
                    'comments': info.get('comment_count') or 0,
                    'video_url': video_url,
                }
                
                return video_data
            except Exception as e:
                error_msg = str(e)
                # 简化错误信息
                if 'members-only' in error_msg or 'subscriber_only' in error_msg:
                    logger.warning(f"跳过会员专属视频: {video_id}")
                else:
                    logger.error(f"✗ 获取视频信息失败: {video_id}")
                raise
    
    @retry_on_failure()
    def get_recommended_videos(self, video_id, limit=10):
        """
        获取视频的推荐列表
        
        注意: yt-dlp不直接支持推荐视频API
        这里使用替代策略：通过搜索相关视频来模拟推荐
        
        返回: 推荐视频列表
        """
        self.rate_limiter.wait()
        
        try:
            # 策略1: 获取视频信息，然后基于标题搜索相关视频
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            opts = self.ydl_opts.copy()
            opts['extract_flat'] = False
            opts['quiet'] = True
            opts['no_warnings'] = True
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if not info:
                    return []
                
                # 提取视频标题中的关键词（取前3个词）
                title = info.get('title', '')
                keywords = ' '.join(title.split()[:3])
                
                # 基于关键词搜索相关视频
                if keywords:
                    search_query = f"ytsearch{limit}:{keywords}"
                    search_result = ydl.extract_info(search_query, download=False)
                    recommended = search_result.get('entries', [])
                    
                    # 过滤掉原视频
                    recommended = [v for v in recommended if v and v.get('id') != video_id]
                    
                    logger.debug(f"通过搜索找到 {len(recommended)} 个相关视频: {video_id}")
                    return recommended[:limit]
                
        except Exception as e:
            logger.debug(f"获取推荐视频失败: {video_id}, {str(e)}")
        
        return []
    
    def extract_channel_id(self, video_info):
        """从视频信息中提取频道ID"""
        return video_info.get('channel_id', video_info.get('uploader_id', ''))
