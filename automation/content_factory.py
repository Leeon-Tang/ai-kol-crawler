"""
AI Content Factory - 自动化内容生成系统
基于 KOL 数据分析，自动生成社交媒体内容

工作流程：
1. 从数据库获取高互动 KOL 内容
2. 分析获胜内容模式（话题、风格、时间）
3. 使用 AI 生成类似内容
4. 自动化发布到社交媒体
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sqlite3
from pathlib import Path


class ContentFactory:
    """AI 内容工厂核心类"""
    
    def __init__(self, db_path: str = "data/ai_kol_crawler.db"):
        self.db_path = db_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """加载配置"""
        config_path = Path("automation/content_factory_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "ai_provider": "gemini",  # gemini, openai, claude
            "api_key": "",
            "content_types": ["short_video", "image_post", "text_post"],
            "posting_schedule": ["09:00", "18:00"],  # 每天发布时间
            "niches": [],  # 目标细分市场
            "min_engagement_rate": 0.05,  # 最小互动率
            "lookback_days": 30  # 分析最近 N 天的数据
        }
    
    def analyze_winning_patterns(self) -> List[Dict[str, Any]]:
        """分析获胜内容模式"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取高互动内容
        lookback_date = (datetime.now() - timedelta(days=self.config['lookback_days'])).strftime('%Y-%m-%d')
        
        query = """
        SELECT 
            name,
            platform,
            followers_count,
            engagement_rate,
            topics,
            last_post_date,
            avg_likes,
            avg_comments
        FROM kols
        WHERE engagement_rate >= ?
        AND last_post_date >= ?
        ORDER BY engagement_rate DESC
        LIMIT 50
        """
        
        cursor.execute(query, (self.config['min_engagement_rate'], lookback_date))
        results = cursor.fetchall()
        conn.close()
        
        patterns = []
        for row in results:
            patterns.append({
                'name': row[0],
                'platform': row[1],
                'followers': row[2],
                'engagement_rate': row[3],
                'topics': row[4],
                'post_date': row[5],
                'avg_likes': row[6],
                'avg_comments': row[7]
            })
        
        return patterns
    
    def extract_content_themes(self, patterns: List[Dict]) -> Dict[str, Any]:
        """提取内容主题和风格"""
        themes = {
            'hot_topics': {},
            'best_posting_times': {},
            'content_styles': [],
            'engagement_triggers': []
        }
        
        # 分析热门话题
        for pattern in patterns:
            if pattern['topics']:
                topics = pattern['topics'].split(',')
                for topic in topics:
                    topic = topic.strip()
                    if topic:
                        themes['hot_topics'][topic] = themes['hot_topics'].get(topic, 0) + 1
        
        # 排序热门话题
        themes['hot_topics'] = dict(sorted(
            themes['hot_topics'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        return themes
    
    def generate_content_ideas(self, themes: Dict[str, Any], count: int = 10) -> List[Dict]:
        """生成内容创意"""
        ideas = []
        hot_topics = list(themes['hot_topics'].keys())
        
        for i in range(count):
            topic = hot_topics[i % len(hot_topics)] if hot_topics else "AI技术"
            ideas.append({
                'id': f'idea_{datetime.now().strftime("%Y%m%d")}_{i+1}',
                'topic': topic,
                'content_type': self.config['content_types'][i % len(self.config['content_types'])],
                'created_at': datetime.now().isoformat(),
                'status': 'pending'
            })
        
        return ideas
    
    def create_content_prompt(self, idea: Dict) -> str:
        """创建 AI 生成提示词"""
        prompt = f"""
请为以下内容创意生成社交媒体内容：

主题: {idea['topic']}
内容类型: {idea['content_type']}

要求：
1. 内容要吸引人，有互动性
2. 适合短视频/图文形式
3. 包含明确的 CTA（行动号召）
4. 风格轻松、易懂
5. 长度适中（50-150字）

请生成：
- 标题/开场白
- 主要内容
- 结尾/CTA
- 建议的视觉元素描述
- 推荐标签（3-5个）
"""
        return prompt
    
    def generate_content_with_ai(self, prompt: str) -> Dict[str, Any]:
        """使用 AI 生成内容"""
        # 这里需要集成实际的 AI API
        # 示例返回结构
        return {
            'title': '生成的标题',
            'content': '生成的内容正文',
            'cta': '生成的行动号召',
            'visual_description': '视觉元素描述',
            'hashtags': ['#AI', '#科技', '#创新'],
            'generated_at': datetime.now().isoformat()
        }
    
    def schedule_posts(self, contents: List[Dict]) -> List[Dict]:
        """安排发布时间表"""
        schedule = []
        posting_times = self.config['posting_schedule']
        
        for i, content in enumerate(contents):
            days_offset = i // len(posting_times)
            time_slot = posting_times[i % len(posting_times)]
            
            post_date = datetime.now() + timedelta(days=days_offset)
            post_datetime = datetime.strptime(
                f"{post_date.strftime('%Y-%m-%d')} {time_slot}", 
                '%Y-%m-%d %H:%M'
            )
            
            schedule.append({
                'content': content,
                'scheduled_time': post_datetime.isoformat(),
                'status': 'scheduled'
            })
        
        return schedule
    
    def run_content_factory(self) -> Dict[str, Any]:
        """运行完整的内容工厂流程"""
        print("🏭 启动 AI 内容工厂...")
        
        # 1. 分析获胜模式
        print("📊 分析高互动内容模式...")
        patterns = self.analyze_winning_patterns()
        print(f"   找到 {len(patterns)} 个高互动 KOL")
        
        # 2. 提取主题
        print("🎯 提取内容主题...")
        themes = self.extract_content_themes(patterns)
        print(f"   识别出 {len(themes['hot_topics'])} 个热门话题")
        
        # 3. 生成创意
        print("💡 生成内容创意...")
        ideas = self.generate_content_ideas(themes, count=14)  # 一周的内容
        print(f"   生成 {len(ideas)} 个内容创意")
        
        # 4. AI 生成内容
        print("🤖 使用 AI 生成内容...")
        generated_contents = []
        for idea in ideas[:5]:  # 先生成 5 个示例
            prompt = self.create_content_prompt(idea)
            content = self.generate_content_with_ai(prompt)
            content['idea_id'] = idea['id']
            generated_contents.append(content)
        print(f"   生成 {len(generated_contents)} 个内容")
        
        # 5. 安排发布
        print("📅 安排发布时间表...")
        schedule = self.schedule_posts(generated_contents)
        print(f"   安排 {len(schedule)} 个发布任务")
        
        result = {
            'patterns_analyzed': len(patterns),
            'themes': themes,
            'ideas_generated': len(ideas),
            'contents_created': len(generated_contents),
            'posts_scheduled': len(schedule),
            'schedule': schedule,
            'run_time': datetime.now().isoformat()
        }
        
        # 保存结果
        self._save_result(result)
        
        print("✅ 内容工厂运行完成！")
        return result
    
    def _save_result(self, result: Dict):
        """保存运行结果"""
        output_dir = Path("automation/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"content_factory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"📁 结果已保存到: {filepath}")


def main():
    """主函数"""
    factory = ContentFactory()
    result = factory.run_content_factory()
    
    print("\n" + "="*50)
    print("📊 运行摘要:")
    print(f"   分析模式: {result['patterns_analyzed']} 个")
    print(f"   热门话题: {len(result['themes']['hot_topics'])} 个")
    print(f"   生成创意: {result['ideas_generated']} 个")
    print(f"   创建内容: {result['contents_created']} 个")
    print(f"   安排发布: {result['posts_scheduled']} 个")
    print("="*50)


if __name__ == "__main__":
    main()
