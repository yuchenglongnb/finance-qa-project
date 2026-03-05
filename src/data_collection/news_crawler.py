"""
新闻数据爬虫
使用AKShare获取财经新闻
"""
import akshare as ak
from typing import List, Dict
from datetime import datetime, timedelta
import time
from loguru import logger
from .base_crawler import BaseCrawler


class NewsCrawler(BaseCrawler):
    """财经新闻爬虫"""
    
    def __init__(self, output_dir: str = "data/raw/news"):
        super().__init__(output_dir)
        self.source_name = "东方财富"
    
    def get_required_fields(self) -> List[str]:
        """必需字段"""
        return ['title', 'publish_time', 'content', 'url']
    
    def fetch(self, days: int = 30, max_news: int = 10000) -> List[Dict]:
        """
        获取最近N天的新闻
        
        Args:
            days: 获取最近几天的新闻
            max_news: 最大新闻数量
            
        Returns:
            List[Dict]: 新闻列表
        """
        all_news = []
        
        try:
            # 方式1: 东方财富网新闻 (推荐)
            logger.info("📰 正在获取东方财富新闻...")
            df_em = ak.stock_news_em()
            
            if df_em is not None and not df_em.empty:
                # 转换为字典列表
                news_list = df_em.to_dict('records')
                all_news.extend(news_list)
                logger.info(f"✅ 获取到 {len(news_list)} 条东方财富新闻")
            
        except Exception as e:
            logger.warning(f"⚠️ 获取东方财富新闻失败: {e}")
        
        try:
            # 方式2: 金十数据快讯 (可选)
            logger.info("📰 正在获取金十数据快讯...")
            df_jinshi = ak.news_jinshi()
            
            if df_jinshi is not None and not df_jinshi.empty:
                news_list = df_jinshi.to_dict('records')
                all_news.extend(news_list)
                logger.info(f"✅ 获取到 {len(news_list)} 条金十数据")
                
        except Exception as e:
            logger.warning(f"⚠️ 获取金十数据失败: {e}")
        
        # 按时间过滤
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_news = []
        
        for news in all_news:
            try:
                # 尝试解析时间
                pub_time = self._parse_time(news)
                if pub_time and pub_time >= cutoff_date:
                    filtered_news.append(news)
            except:
                # 如果无法解析时间,保留该新闻
                filtered_news.append(news)
        
        # 限制数量
        if len(filtered_news) > max_news:
            logger.info(f"⚠️ 新闻数量 {len(filtered_news)} 超过限制 {max_news},进行截断")
            filtered_news = filtered_news[:max_news]
        
        logger.info(f"✅ 筛选后剩余 {len(filtered_news)} 条新闻")
        return filtered_news
    
    def _parse_time(self, news: Dict) -> datetime:
        """解析时间字段"""
        time_fields = ['发布时间', 'publish_time', '时间', 'datetime', 'date']
        
        for field in time_fields:
            if field in news and news[field]:
                try:
                    time_str = str(news[field])
                    # 尝试多种时间格式
                    for fmt in [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d',
                        '%Y/%m/%d %H:%M:%S',
                        '%Y/%m/%d',
                    ]:
                        try:
                            return datetime.strptime(time_str, fmt)
                        except:
                            continue
                except:
                    continue
        
        return None
    
    def parse(self, raw_data: List[Dict]) -> List[Dict]:
        """
        解析新闻数据,标准化字段
        
        标准格式:
        {
            'id': str,
            'title': str,
            'content': str,
            'summary': str,
            'publish_time': str,
            'source': str,
            'url': str,
            'keywords': List[str],
            'category': str
        }
        """
        parsed = []
        
        for news in raw_data:
            try:
                parsed_news = self._parse_single_news(news)
                if parsed_news:
                    parsed.append(parsed_news)
            except Exception as e:
                logger.warning(f"⚠️ 解析新闻失败: {e}")
                continue
        
        return parsed
    
    def _parse_single_news(self, news: Dict) -> Dict:
        """解析单条新闻"""
        # 标题
        title = (
            news.get('标题') or 
            news.get('title') or 
            news.get('新闻标题') or 
            ''
        ).strip()
        
        # 内容
        content = (
            news.get('内容') or 
            news.get('content') or 
            news.get('新闻内容') or 
            news.get('描述') or
            ''
        ).strip()
        
        # 时间
        publish_time = (
            news.get('发布时间') or 
            news.get('publish_time') or 
            news.get('时间') or
            news.get('datetime') or
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 来源
        source = (
            news.get('来源') or 
            news.get('source') or 
            news.get('新闻来源') or
            self.source_name
        )
        
        # URL
        url = (
            news.get('链接') or 
            news.get('url') or 
            news.get('新闻链接') or
            ''
        )
        
        # 生成ID
        news_id = f"{hash(title + str(publish_time))}"
        
        # 提取摘要 (取前200字)
        summary = content[:200] if len(content) > 200 else content
        
        parsed = {
            'id': news_id,
            'title': title,
            'content': content,
            'summary': summary,
            'publish_time': str(publish_time),
            'source': source,
            'url': url,
            'category': self._classify_category(title + content),
            'keywords': self._extract_keywords(title),
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return parsed
    
    def _classify_category(self, text: str) -> str:
        """简单的分类逻辑"""
        categories = {
            '宏观': ['货币', '利率', '政策', 'GDP', '经济', '央行'],
            '股市': ['股票', '上涨', '下跌', 'A股', '涨停', '跌停'],
            '行业': ['新能源', '半导体', '医药', '房地产', '互联网'],
            '公司': ['财报', '业绩', '重组', '并购', '分红'],
        }
        
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        
        return '综合'
    
    def _extract_keywords(self, title: str) -> List[str]:
        """提取关键词 (简化版)"""
        # 这里可以使用jieba分词
        import jieba
        words = jieba.lcut(title)
        # 过滤停用词和短词
        keywords = [w for w in words if len(w) >= 2 and w not in ['的', '了', '在', '是']]
        return keywords[:5]  # 返回前5个


class StockNewsCrawler(NewsCrawler):
    """个股新闻爬虫"""
    
    def __init__(self, output_dir: str = "data/raw/news"):
        super().__init__(output_dir)
    
    def fetch(self, stock_code: str, days: int = 30) -> List[Dict]:
        """
        获取个股新闻
        
        Args:
            stock_code: 股票代码 (如 600000)
            days: 获取最近几天
            
        Returns:
            List[Dict]: 新闻列表
        """
        logger.info(f"📰 正在获取股票 {stock_code} 的新闻...")
        
        try:
            df = ak.stock_news_em(symbol=stock_code)
            
            if df is not None and not df.empty:
                news_list = df.to_dict('records')
                logger.info(f"✅ 获取到 {len(news_list)} 条 {stock_code} 的新闻")
                return news_list
            
        except Exception as e:
            logger.error(f"❌ 获取股票 {stock_code} 新闻失败: {e}")
            return []
        
        return []


# 快速测试
if __name__ == "__main__":
    # 测试新闻爬虫
    crawler = NewsCrawler()
    
    # 获取最近3天的新闻
    news_data = crawler.run(days=3, max_news=100)
    
    print(f"\n✅ 成功获取 {len(news_data)} 条新闻")
    print(f"📄 示例数据:")
    if news_data:
        import json
        print(json.dumps(news_data[0], ensure_ascii=False, indent=2))
