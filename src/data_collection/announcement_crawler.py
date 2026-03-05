"""
公司公告爬虫
使用AKShare获取公司公告
"""
import akshare as ak
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
from .base_crawler import BaseCrawler


class AnnouncementCrawler(BaseCrawler):
    """公司公告爬虫"""
    
    def __init__(self, output_dir: str = "data/raw/announcements"):
        super().__init__(output_dir)
    
    def get_required_fields(self) -> List[str]:
        """必需字段"""
        return ['title', 'stock_code', 'publish_date']
    
    def fetch(
        self, 
        stock_codes: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_announcements: int = 5000
    ) -> List[Dict]:
        """
        获取公司公告
        
        Args:
            stock_codes: 股票代码列表,None表示获取所有
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            max_announcements: 最大公告数
            
        Returns:
            List[Dict]: 公告列表
        """
        all_announcements = []
        
        # 设置默认日期范围
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        logger.info(f"📄 获取公告: {start_date} 至 {end_date}")
        
        if stock_codes is None:
            # 获取所有公告
            announcements = self._fetch_all_announcements(start_date, end_date)
            all_announcements.extend(announcements)
        else:
            # 获取指定股票公告
            for stock_code in stock_codes:
                announcements = self._fetch_stock_announcements(
                    stock_code, start_date, end_date
                )
                all_announcements.extend(announcements)
                logger.info(f"✅ 获取 {stock_code} 的 {len(announcements)} 条公告")
        
        # 限制数量
        if len(all_announcements) > max_announcements:
            logger.info(f"⚠️ 公告数量超过限制,截断至 {max_announcements}")
            all_announcements = all_announcements[:max_announcements]
        
        logger.info(f"✅ 共获取 {len(all_announcements)} 条公告")
        return all_announcements
    
    def _fetch_all_announcements(
            self, 
            start_date: str, 
            end_date: str
        ) -> List[Dict]:
        """获取所有公告"""
        try:
            logger.info(f"📥 正在获取沪深市场公告... 日期范围：{start_date} 至 {end_date}")
            
            from datetime import datetime, timedelta
            
            # 将字符串日期转换为datetime对象
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            all_announcements = []
            
            # 循环遍历日期范围内的每一天
            current_date = start
            while current_date <= end:
                # 格式化日期为接口所需的格式：YYYYMMDD
                date_str = current_date.strftime("%Y%m%d")
                logger.debug(f"正在获取 {date_str} 的公告数据...")
                
                try:
                    # 调用接口，传入单日参数
                    df = ak.stock_notice_report(date=date_str)
                    
                    if df is not None and not df.empty:
                        # 转换为字典列表
                        daily_announcements = df.to_dict('records')
                        all_announcements.extend(daily_announcements)
                        logger.debug(f"  获取到 {len(daily_announcements)} 条")
                except Exception as e:
                    logger.warning(f"获取 {date_str} 的公告失败: {e}")
                    # 继续获取下一天的数据
                
                # 日期加一天
                current_date += timedelta(days=1)
            
            if not all_announcements:
                logger.info("ℹ️ 当前指定日期范围内未获取到公告数据")
                return []
            
            logger.info(f"✅ 共获取到 {len(all_announcements)} 条公告")
            return all_announcements
            
        except Exception as e:
            logger.error(f"❌ 获取所有公告失败: {e}")
            return []
    
    def _fetch_stock_announcements(
        self, 
        stock_code: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict]:
        """获取个股公告"""
        try:
            df = ak.stock_notice_report(symbol=stock_code)
            
            if df is None or df.empty:
                return []
            
            announcements = df.to_dict('records')
            filtered = self._filter_by_date(announcements, start_date, end_date)
            
            return filtered
            
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code} 公告失败: {e}")
            return []
    
    def _filter_by_date(
        self, 
        announcements: List[Dict], 
        start_date: str, 
        end_date: str
    ) -> List[Dict]:
        """按日期过滤"""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        filtered = []
        for ann in announcements:
            try:
                # 尝试解析日期
                date_str = self._extract_date(ann)
                if date_str:
                    date_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    if start_dt <= date_dt <= end_dt:
                        filtered.append(ann)
            except:
                # 无法解析日期,保留
                filtered.append(ann)
        
        return filtered
    
    def _extract_date(self, announcement: Dict) -> Optional[str]:
        """提取日期"""
        date_fields = ['公告日期', 'publish_date', '日期', 'date', 'announcement_date']
        
        for field in date_fields:
            if field in announcement and announcement[field]:
                date_str = str(announcement[field])
                # 标准化日期格式
                try:
                    # 尝试解析
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d']:
                        try:
                            dt = datetime.strptime(date_str.strip(), fmt)
                            return dt.strftime('%Y-%m-%d')
                        except:
                            continue
                except:
                    continue
        
        return None
    
    def parse(self, raw_data: List[Dict]) -> List[Dict]:
        """
        解析公告数据
        
        标准格式:
        {
            'id': str,
            'title': str,
            'stock_code': str,
            'stock_name': str,
            'announcement_type': str,
            'publish_date': str,
            'content': str,
            'url': str,
            'pdf_url': str
        }
        """
        parsed = []
        
        for announcement in raw_data:
            try:
                parsed_ann = self._parse_single_announcement(announcement)
                if parsed_ann:
                    parsed.append(parsed_ann)
            except Exception as e:
                logger.warning(f"⚠️ 解析公告失败: {e}")
                continue
        
        return parsed
    
    def _parse_single_announcement(self, ann: Dict) -> Dict:
        """解析单条公告"""
        # 标题
        title = (
            ann.get('公告标题') or 
            ann.get('title') or 
            ann.get('标题') or
            ''
        ).strip()
        
        # 股票代码
        stock_code = (
            ann.get('代码') or 
            ann.get('stock_code') or 
            ann.get('symbol') or
            ''
        ).strip()
        
        # 股票名称
        stock_name = (
            ann.get('简称') or 
            ann.get('stock_name') or 
            ann.get('name') or
            ''
        ).strip()
        
        # 公告类型
        ann_type = (
            ann.get('公告类型') or 
            ann.get('type') or 
            self._classify_type(title)
        )
        
        # 发布日期
        publish_date = self._extract_date(ann) or datetime.now().strftime('%Y-%m-%d')
        
        # URL
        url = (
            ann.get('公告链接') or 
            ann.get('url') or 
            ann.get('link') or
            ''
        )
        
        # PDF URL
        pdf_url = (
            ann.get('PDF链接') or 
            ann.get('pdf_url') or
            ''
        )
        
        # 生成ID
        ann_id = f"{stock_code}_{publish_date}_{hash(title)}"
        
        # 内容摘要 (如果有)
        content = (
            ann.get('公告内容') or 
            ann.get('content') or 
            ann.get('摘要') or
            ''
        ).strip()
        
        parsed = {
            'id': ann_id,
            'title': title,
            'stock_code': stock_code,
            'stock_name': stock_name,
            'announcement_type': ann_type,
            'publish_date': publish_date,
            'content': content,
            'url': url,
            'pdf_url': pdf_url,
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return parsed
    
    def _classify_type(self, title: str) -> str:
        """分类公告类型"""
        type_keywords = {
            '财报': ['年报', '半年报', '季报', '业绩', '财务'],
            '重组': ['重组', '并购', '收购', '出售'],
            '分红': ['分红', '派息', '送转'],
            '增发': ['增发', '配股', '定增'],
            '诉讼': ['诉讼', '仲裁'],
            '高管': ['董事', '高管', '任命', '辞职'],
            '股东': ['股东', '持股', '减持', '增持'],
            '风险': ['风险', '提示', '警示'],
        }
        
        for ann_type, keywords in type_keywords.items():
            if any(kw in title for kw in keywords):
                return ann_type
        
        return '其他'


# 快速测试
if __name__ == "__main__":
    # 测试公告爬虫
    crawler = AnnouncementCrawler()
    
    # 获取最近30天的公告 (前100条)
    announcements = crawler.run(
        start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        max_announcements=100
    )
    
    print(f"\n✅ 成功获取 {len(announcements)} 条公告")
    if announcements:
        import json
        print(f"📄 示例数据:")
        print(json.dumps(announcements[0], ensure_ascii=False, indent=2))
