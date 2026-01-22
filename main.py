"""
AI KOL爬虫系统 - 主入口
"""
import sys
from storage.database import Database
from storage.kol_repository import KOLRepository
from core.scraper import YouTubeScraper
from core.searcher import KeywordSearcher
from core.analyzer import KOLAnalyzer
from core.expander import KOLExpander
from core.filter import KOLFilter
from tasks.discovery_task import DiscoveryTask
from tasks.expand_task import ExpandTask
from tasks.update_task import UpdateTask
from tasks.export_task import ExportTask
from utils.logger import setup_logger


logger = setup_logger()


class AIKOLCrawler:
    """AI KOL爬虫主程序"""
    
    def __init__(self):
        # 初始化数据库
        self.db = Database()
        self.db.connect()
        self.db.init_tables()
        
        # 初始化仓库
        self.repository = KOLRepository(self.db)
        
        # 初始化核心模块
        self.scraper = YouTubeScraper()
        self.searcher = KeywordSearcher(self.scraper)
        self.analyzer = KOLAnalyzer(self.scraper)
        self.expander = KOLExpander(self.scraper)
        self.filter = KOLFilter(self.repository)
        
        # 初始化任务
        self.discovery_task = DiscoveryTask(
            self.searcher, self.analyzer, self.filter, self.repository
        )
        self.expand_task = ExpandTask(
            self.expander, self.analyzer, self.filter, self.repository
        )
        self.update_task = UpdateTask(
            self.scraper, self.analyzer, self.repository
        )
        self.export_task = ExportTask(self.repository)
    
    def show_menu(self):
        """显示菜单"""
        print("\n" + "=" * 60)
        print("           AI KOL 爬虫系统")
        print("=" * 60)
        print("1. 初始发现 - 关键词搜索")
        print("2. 扩散发现 - 从已有KOL扩散")
        print("3. 更新数据 - 更新已有KOL")
        print("4. 完整流程 - 搜索+扩散")
        print("5. 持续扩散 - 循环扩散直到达到上限")
        print("6. 导出Excel - 生成KOL报告")
        print("7. 查看统计 - 数据库统计信息")
        print("0. 退出")
        print("=" * 60)
    
    def show_statistics(self):
        """显示统计信息"""
        stats = self.repository.get_statistics()
        
        print("\n" + "=" * 60)
        print("           数据库统计")
        print("=" * 60)
        print(f"总KOL数:        {stats['total_kols']}")
        print(f"合格KOL数:      {stats['qualified_kols']}")
        print(f"待分析KOL数:    {stats['pending_kols']}")
        print(f"总视频数:       {stats['total_videos']}")
        print(f"待扩散队列:     {stats['pending_expansions']}")
        print("=" * 60)
    
    def run_discovery(self):
        """运行发现任务"""
        keyword_limit = input("使用多少个关键词搜索？(默认30): ").strip()
        keyword_limit = int(keyword_limit) if keyword_limit else 30
        
        self.discovery_task.run(keyword_limit)
    
    def run_expand(self):
        """运行扩散任务"""
        self.expand_task.run()
    
    def run_update(self):
        """运行更新任务"""
        self.update_task.run()
    
    def run_full_workflow(self):
        """运行完整流程"""
        logger.info("开始完整流程: 搜索 + 扩散")
        self.discovery_task.run(keyword_limit=30)
        self.expand_task.run()
    
    def run_continuous_expand(self):
        """持续扩散直到达到上限"""
        logger.info("开始持续扩散模式")
        
        iteration = 1
        while not self.filter.should_stop_discovery():
            logger.info(f"\n第 {iteration} 轮扩散")
            self.expand_task.run()
            
            # 检查扩散队列是否为空
            queue = self.repository.get_expansion_queue(limit=1)
            if not queue:
                logger.info("扩散队列为空，停止扩散")
                break
            
            iteration += 1
        
        logger.info("持续扩散完成")
    
    def run_export(self):
        """运行导出任务"""
        filepath = self.export_task.run()
        if filepath:
            print(f"\n导出成功: {filepath}")
    
    def run(self):
        """主运行循环"""
        try:
            while True:
                self.show_menu()
                choice = input("\n请选择操作: ").strip()
                
                if choice == "1":
                    self.run_discovery()
                elif choice == "2":
                    self.run_expand()
                elif choice == "3":
                    self.run_update()
                elif choice == "4":
                    self.run_full_workflow()
                elif choice == "5":
                    self.run_continuous_expand()
                elif choice == "6":
                    self.run_export()
                elif choice == "7":
                    self.show_statistics()
                elif choice == "0":
                    print("\n感谢使用，再见！")
                    break
                else:
                    print("\n无效选择，请重试")
        
        except KeyboardInterrupt:
            print("\n\n程序被中断")
        
        finally:
            self.db.close()
            logger.info("数据库连接已关闭")


if __name__ == "__main__":
    crawler = AIKOLCrawler()
    crawler.run()
