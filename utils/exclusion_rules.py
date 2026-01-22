"""
排除规则 - 通用的内容过滤规则
"""
import json
from utils.logger import setup_logger
from utils.config_loader import get_absolute_path

logger = setup_logger()


class ExclusionRules:
    """排除规则管理器"""
    
    def __init__(self, config_path='config/config.json'):
        config_path = get_absolute_path(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 从配置加载排除规则
        self.rules = config.get('exclusion_rules', {})
        
        # 默认规则
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认排除规则"""
        
        # 课程/教学类关键词
        if 'course_keywords' not in self.rules:
            self.rules['course_keywords'] = [
                '第', '講', '课', '第一', '第二', '第三', '第四', '第五',
                'lecture', 'lesson', 'course', 'tutorial series',
                '导论', '導論', '入门', '入門', '基础', '基礎',
                '教程', '教學', '系列课', '系列課', '课程', '課程'
            ]
        
        # 学术机构关键词
        if 'academic_keywords' not in self.rules:
            self.rules['academic_keywords'] = [
                'university', '大学', '大學', 'college', '学院', '學院',
                'institute', '研究所', '研究院', 'academy', '学术', '學術'
            ]
        
        # 新闻媒体关键词
        if 'news_keywords' not in self.rules:
            self.rules['news_keywords'] = [
                'news', '新闻', '新聞', 'media', '媒体', '媒體',
                'press', '报道', '報導', 'daily', '日报', '日報'
            ]
        
        # 企业官方账号关键词
        if 'corporate_keywords' not in self.rules:
            self.rules['corporate_keywords'] = [
                'official', '官方', 'corp', 'inc', 'ltd',
                'company', '公司', 'enterprise', '企业', '企業'
            ]
    
    def is_course_channel(self, channel_name, video_titles):
        """
        判断是否是课程/教学频道
        
        Args:
            channel_name: 频道名称
            video_titles: 视频标题列表
        
        Returns:
            bool: 是否应该排除
        """
        channel_lower = channel_name.lower()
        
        # 检查频道名是否包含学术机构关键词
        for keyword in self.rules['academic_keywords']:
            if keyword.lower() in channel_lower:
                logger.info(f"  └─ 排除原因: 学术机构频道 (关键词: {keyword})")
                return True
        
        # 检查视频标题模式
        course_pattern_count = 0
        for title in video_titles[:5]:  # 只检查前5个
            for keyword in self.rules['course_keywords']:
                if keyword in title:
                    course_pattern_count += 1
                    break
        
        # 如果超过60%的视频都是课程模式
        if len(video_titles) > 0 and course_pattern_count / min(len(video_titles), 5) >= 0.6:
            logger.info(f"  └─ 排除原因: 课程系列频道 ({course_pattern_count}/5 个视频包含课程关键词)")
            return True
        
        return False
    
    def is_news_channel(self, channel_name):
        """
        判断是否是新闻媒体频道
        
        Args:
            channel_name: 频道名称
        
        Returns:
            bool: 是否应该排除
        """
        channel_lower = channel_name.lower()
        
        for keyword in self.rules['news_keywords']:
            if keyword.lower() in channel_lower:
                logger.info(f"  └─ 排除原因: 新闻媒体频道 (关键词: {keyword})")
                return True
        
        return False
    
    def is_corporate_channel(self, channel_name):
        """
        判断是否是企业官方账号
        
        Args:
            channel_name: 频道名称
        
        Returns:
            bool: 是否应该排除
        """
        channel_lower = channel_name.lower()
        
        for keyword in self.rules['corporate_keywords']:
            if keyword.lower() in channel_lower:
                # 企业官方账号不一定要排除，可以根据需求调整
                # logger.info(f"  └─ 检测到: 企业官方账号 (关键词: {keyword})")
                pass
        
        return False
    
    def should_exclude_channel(self, channel_name, video_titles=None):
        """
        综合判断是否应该排除该频道
        
        Args:
            channel_name: 频道名称
            video_titles: 视频标题列表（可选）
        
        Returns:
            bool: 是否应该排除
        """
        # 检查新闻媒体
        if self.is_news_channel(channel_name):
            return True
        
        # 检查课程频道
        if video_titles and self.is_course_channel(channel_name, video_titles):
            return True
        
        # 可以继续添加其他规则
        
        return False
    
    def add_exclusion_keyword(self, category, keyword):
        """
        添加排除关键词
        
        Args:
            category: 类别 (course_keywords, academic_keywords, etc.)
            keyword: 关键词
        """
        if category not in self.rules:
            self.rules[category] = []
        
        if keyword not in self.rules[category]:
            self.rules[category].append(keyword)
            logger.info(f"添加排除关键词: {category} - {keyword}")
    
    def remove_exclusion_keyword(self, category, keyword):
        """
        移除排除关键词
        
        Args:
            category: 类别
            keyword: 关键词
        """
        if category in self.rules and keyword in self.rules[category]:
            self.rules[category].remove(keyword)
            logger.info(f"移除排除关键词: {category} - {keyword}")
    
    def get_all_rules(self):
        """获取所有规则"""
        return self.rules
