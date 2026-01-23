"""
联系方式提取工具
从频道描述、关于页面等提取联系信息
"""
import re
from typing import Dict, List, Optional


class ContactExtractor:
    """联系方式提取器"""
    
    def __init__(self):
        # 邮箱正则
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # 社交媒体模式
        self.social_patterns = {
            'twitter': re.compile(r'(?:twitter\.com/|@)([A-Za-z0-9_]{1,15})', re.IGNORECASE),
            'instagram': re.compile(r'(?:instagram\.com/|ig:|insta:)\s*([A-Za-z0-9_.]{1,30})', re.IGNORECASE),
            'discord': re.compile(r'discord\.gg/([A-Za-z0-9]+)', re.IGNORECASE),
            'telegram': re.compile(r'(?:t\.me/|telegram:)\s*([A-Za-z0-9_]{5,32})', re.IGNORECASE),
            'linkedin': re.compile(r'linkedin\.com/in/([A-Za-z0-9-]+)', re.IGNORECASE),
            'facebook': re.compile(r'facebook\.com/([A-Za-z0-9.]+)', re.IGNORECASE),
            'tiktok': re.compile(r'tiktok\.com/@([A-Za-z0-9_.]+)', re.IGNORECASE),
            'github': re.compile(r'github\.com/([A-Za-z0-9-]+)', re.IGNORECASE),
        }
        
        # 网站链接模式
        self.website_pattern = re.compile(
            r'https?://(?:www\.)?([A-Za-z0-9-]+\.[A-Za-z]{2,}(?:/[^\s]*)?)',
            re.IGNORECASE
        )
    
    def extract_email(self, text: str) -> Optional[str]:
        """提取邮箱地址"""
        if not text:
            return None
        
        matches = self.email_pattern.findall(text)
        if matches:
            # 过滤掉一些常见的无效邮箱
            valid_emails = [
                email for email in matches 
                if not any(invalid in email.lower() for invalid in [
                    'example.com', 'test.com', 'noreply', 'no-reply'
                ])
            ]
            return valid_emails[0] if valid_emails else None
        return None
    
    def extract_social_media(self, text: str) -> Dict[str, str]:
        """提取社交媒体账号"""
        if not text:
            return {}
        
        social_accounts = {}
        
        for platform, pattern in self.social_patterns.items():
            matches = pattern.findall(text)
            if matches:
                # 取第一个匹配
                social_accounts[platform] = matches[0]
        
        return social_accounts
    
    def extract_website(self, text: str) -> Optional[str]:
        """提取网站链接"""
        if not text:
            return None
        
        matches = self.website_pattern.findall(text)
        if matches:
            # 过滤掉YouTube和常见的社交媒体链接
            valid_sites = [
                site for site in matches 
                if not any(domain in site.lower() for domain in [
                    'youtube.com', 'youtu.be', 'twitter.com', 'instagram.com',
                    'facebook.com', 'tiktok.com', 'discord.gg', 't.me'
                ])
            ]
            return f"https://{valid_sites[0]}" if valid_sites else None
        return None
    
    def extract_all_contacts(self, description: str, channel_description: str = None) -> str:
        """
        从描述中提取所有联系方式
        返回格式化的联系方式字符串
        优先显示email，如果没有email则显示其他社交媒体
        """
        # 合并所有文本
        all_text = description or ""
        if channel_description:
            all_text += " " + channel_description
        
        if not all_text.strip():
            return ""
        
        # 提取邮箱（优先）
        email = self.extract_email(all_text)
        if email:
            return email
        
        # 如果没有邮箱，提取社交媒体
        social_media = self.extract_social_media(all_text)
        if social_media:
            # 优先级：Twitter > Instagram > Telegram > Discord > 其他
            priority_order = ['twitter', 'instagram', 'telegram', 'discord', 'linkedin', 'facebook', 'tiktok', 'github']
            
            for platform in priority_order:
                if platform in social_media:
                    username = social_media[platform]
                    # 返回完整链接格式
                    platform_urls = {
                        'twitter': f'twitter.com/{username}',
                        'instagram': f'instagram.com/{username}',
                        'telegram': f't.me/{username}',
                        'discord': f'discord.gg/{username}',
                        'linkedin': f'linkedin.com/in/{username}',
                        'facebook': f'facebook.com/{username}',
                        'tiktok': f'tiktok.com/@{username}',
                        'github': f'github.com/{username}',
                    }
                    return platform_urls.get(platform, username)
        
        # 如果都没有，尝试提取网站
        website = self.extract_website(all_text)
        if website:
            return website
        
        return ""
    
    def extract_contact_dict(self, description: str, channel_description: str = None) -> Dict:
        """
        从描述中提取所有联系方式
        返回字典格式
        """
        all_text = description or ""
        if channel_description:
            all_text += " " + channel_description
        
        if not all_text.strip():
            return {}
        
        result = {}
        
        # 提取邮箱
        email = self.extract_email(all_text)
        if email:
            result['email'] = email
        
        # 提取社交媒体
        social_media = self.extract_social_media(all_text)
        if social_media:
            result['social'] = social_media
        
        # 提取网站
        website = self.extract_website(all_text)
        if website:
            result['website'] = website
        
        return result


def test_extractor():
    """测试联系方式提取"""
    extractor = ContactExtractor()
    
    test_cases = [
        "Contact me at john@example.com or follow @johndoe on Twitter",
        "Business inquiries: business@company.com | Instagram: @myhandle",
        "Join our Discord: discord.gg/abc123 | Website: https://mysite.com",
        "📧 contact@email.com | 🐦 twitter.com/username | 💬 t.me/channel",
    ]
    
    for text in test_cases:
        print(f"\n原文: {text}")
        print(f"提取结果: {extractor.extract_all_contacts(text)}")
        print(f"字典格式: {extractor.extract_contact_dict(text)}")


if __name__ == "__main__":
    test_extractor()
