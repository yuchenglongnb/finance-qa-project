"""
统一数据采集脚本
一键运行所有数据采集任务
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collection.news_crawler import NewsCrawler, StockNewsCrawler
from src.data_collection.announcement_crawler import AnnouncementCrawler


def setup_logger():
    """配置日志"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"data_collection_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger.add(
        log_file,
        rotation="500 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )


def collect_news(days: int = 30, max_news: int = 10000, output_dir: str = "data/raw"):
    """采集新闻数据"""
    logger.info("=" * 60)
    logger.info("📰 开始采集新闻数据")
    logger.info("=" * 60)
    
    crawler = NewsCrawler(output_dir=str(Path(output_dir) / "news"))
    news_data = crawler.run(days=days, max_news=max_news)
    
    logger.info(f"✅ 新闻采集完成: {len(news_data)} 条")
    return news_data


def collect_announcements(
    days: int = 90, 
    max_announcements: int = 5000,
    stock_codes: list = None,
    output_dir: str = "data/raw"
):
    """采集公告数据"""
    logger.info("=" * 60)
    logger.info("📄 开始采集公告数据")
    logger.info("=" * 60)
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    crawler = AnnouncementCrawler(output_dir=str(Path(output_dir) / "announcements"))
    announcements = crawler.run(
        stock_codes=stock_codes,
        start_date=start_date,
        end_date=end_date,
        max_announcements=max_announcements
    )
    
    logger.info(f"✅ 公告采集完成: {len(announcements)} 条")
    return announcements


def collect_stock_news(stock_codes: list, days: int = 30, output_dir: str = "data/raw"):
    """采集个股新闻"""
    logger.info("=" * 60)
    logger.info(f"📈 开始采集个股新闻: {stock_codes}")
    logger.info("=" * 60)
    
    crawler = StockNewsCrawler(output_dir=str(Path(output_dir) / "news"))
    all_news = []
    
    for stock_code in stock_codes:
        try:
            news = crawler.run(stock_code=stock_code, days=days)
            all_news.extend(news)
            logger.info(f"✅ {stock_code}: {len(news)} 条新闻")
        except Exception as e:
            logger.error(f"❌ {stock_code} 采集失败: {e}")
    
    logger.info(f"✅ 个股新闻采集完成: {len(all_news)} 条")
    return all_news


def generate_statistics(news_data: list, announcement_data: list):
    """生成统计信息"""
    logger.info("=" * 60)
    logger.info("📊 数据统计")
    logger.info("=" * 60)
    
    # 新闻统计
    logger.info(f"新闻总数: {len(news_data)}")
    if news_data:
        categories = {}
        for news in news_data:
            cat = news.get('category', '未分类')
            categories[cat] = categories.get(cat, 0) + 1
        
        logger.info("新闻分类分布:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {cat}: {count}")
    
    # 公告统计
    logger.info(f"\n公告总数: {len(announcement_data)}")
    if announcement_data:
        ann_types = {}
        for ann in announcement_data:
            ann_type = ann.get('announcement_type', '未分类')
            ann_types[ann_type] = ann_types.get(ann_type, 0) + 1
        
        logger.info("公告类型分布:")
        for ann_type, count in sorted(ann_types.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {ann_type}: {count}")
    
    logger.info("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='金融资讯数据采集工具')
    
    # 采集类型
    parser.add_argument(
        '--type',
        choices=['news', 'announcement', 'stock', 'all'],
        default='all',
        help='采集类型: news(新闻), announcement(公告), stock(个股), all(全部)'
    )
    
    # 时间范围
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='采集最近N天的数据 (默认30天)'
    )
    
    # 数量限制
    parser.add_argument(
        '--max-news',
        type=int,
        default=10000,
        help='最大新闻数量 (默认10000)'
    )
    
    parser.add_argument(
        '--max-announcements',
        type=int,
        default=5000,
        help='最大公告数量 (默认5000)'
    )
    
    # 股票代码
    parser.add_argument(
        '--stocks',
        nargs='+',
        help='股票代码列表,如: 600000 000001'
    )
    
    # 输出路径
    parser.add_argument(
        '--output-dir',
        default='data/raw',
        help='输出目录 (默认: data/raw)'
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logger()
    
    logger.info("🚀 开始数据采集任务")
    logger.info(f"采集类型: {args.type}")
    logger.info(f"时间范围: 最近 {args.days} 天")
    
    news_data = []
    announcement_data = []
    
    try:
        # 采集新闻
        if args.type in ['news', 'all']:
            news_data = collect_news(
                days=args.days,
                max_news=args.max_news,
                output_dir=args.output_dir
            )
        
        # 采集公告
        if args.type in ['announcement', 'all']:
            announcement_data = collect_announcements(
                days=args.days,
                max_announcements=args.max_announcements,
                stock_codes=args.stocks,
                output_dir=args.output_dir
            )
        
        # 采集个股新闻
        if args.type == 'stock' and args.stocks:
            news_data = collect_stock_news(
                stock_codes=args.stocks,
                days=args.days,
                output_dir=args.output_dir
            )
        
        # 生成统计
        generate_statistics(news_data, announcement_data)
        
        logger.info("✅ 所有采集任务完成!")
        
        # 输出文件位置
        logger.info("\n📁 数据文件位置:")
        logger.info(f"  新闻: {Path(args.output_dir) / 'news' / '*.jsonl'}")
        logger.info(f"  公告: {Path(args.output_dir) / 'announcements' / '*.jsonl'}")
        
    except Exception as e:
        logger.error(f"❌ 采集过程出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


"""
使用示例:

1. 采集所有数据 (新闻+公告)
   python scripts/collect_data.py --type all --days 30

2. 只采集新闻
   python scripts/collect_data.py --type news --days 7 --max-news 5000

3. 只采集公告
   python scripts/collect_data.py --type announcement --days 90

4. 采集特定股票新闻
   python scripts/collect_data.py --type stock --stocks 600000 000001 --days 30

5. 自定义输出目录
   python scripts/collect_data.py --output-dir my_data
"""
