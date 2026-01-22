"""
关键词匹配工具
"""
import json


class TextMatcher:
    """文本关键词匹配器"""
    
    def __init__(self, config_path='config/config.json'):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 合并所有优先级的关键词
        self.keywords = []
        for priority in ['priority_high', 'priority_medium', 'priority_low']:
            self.keywords.extend(config['keywords'][priority])
        
        # 转换为小写用于匹配
        self.keywords_lower = [kw.lower() for kw in self.keywords]
    
    def is_ai_related(self, title, description=''):
        """
        判断内容是否AI相关
        
        判断依据：
        1. 检查标题中是否包含AI关键词
        2. 检查描述中是否包含AI关键词
        3. 只要标题或描述中有任何一个关键词，就判定为AI相关
        
        返回: (是否相关, 匹配的关键词列表)
        """
        # 处理None值
        title = title or ''
        description = description or ''
        
        title_lower = title.lower()
        description_lower = description.lower()
        
        matched_in_title = []
        matched_in_description = []
        
        for i, keyword in enumerate(self.keywords_lower):
            if keyword in title_lower:
                matched_in_title.append(self.keywords[i])
            elif keyword in description_lower:
                matched_in_description.append(self.keywords[i])
        
        # 合并所有匹配的关键词
        all_matched = matched_in_title + matched_in_description
        
        return len(all_matched) > 0, all_matched
    
    def get_match_details(self, title, description=''):
        """
        获取详细的匹配信息
        
        返回: {
            'is_ai': bool,
            'matched_keywords': list,
            'title_matches': list,
            'description_matches': list,
            'match_count': int
        }
        """
        # 处理None值
        title = title or ''
        description = description or ''
        
        title_lower = title.lower()
        description_lower = description.lower()
        
        matched_in_title = []
        matched_in_description = []
        
        for i, keyword in enumerate(self.keywords_lower):
            if keyword in title_lower:
                matched_in_title.append(self.keywords[i])
            if keyword in description_lower:
                matched_in_description.append(self.keywords[i])
        
        all_matched = list(set(matched_in_title + matched_in_description))
        
        return {
            'is_ai': len(all_matched) > 0,
            'matched_keywords': all_matched,
            'title_matches': matched_in_title,
            'description_matches': matched_in_description,
            'match_count': len(all_matched)
        }
    
    def get_all_keywords(self):
        """获取所有关键词"""
        return self.keywords
    
    def get_keyword_count(self):
        """获取关键词总数"""
        return len(self.keywords)
