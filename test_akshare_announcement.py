import akshare as ak
from datetime import datetime, timedelta
import pandas as pd

print("测试 akshare 股票公告接口...")
try:
    # 方法1: 测试另一个常用公告接口（东方财富）
    # 注意：接口名称可能变化，请以最新akshare文档为准
    df = ak.stock_notice_report(date="20250305") # 尝试获取最近一天
    # 或 df = ak.stock_notice_report(start_date="20250301", end_date="20250305")
    if df is not None and not df.empty:
        print(f"✅ 接口 'stock_notice_report' 调用成功！获取到 {len(df)} 条数据。")
        print("前几行数据：")
        print(df.head())
        print("\n列名：", df.columns.tolist())
    else:
        print("⚠️ 接口调用成功，但返回数据为空。可能该日期无公告。")
except Exception as e:
    print(f"❌ 接口 'stock_notice_report' 调用失败: {e}")

print("\n" + "="*50 + "\n")

try:
    # 方法2: 测试您日志中可能用到的另一个接口（需查看您的源码确认）
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
    df2 = ak.stock_news_em(symbol="全部", start_date=start_date, end_date=end_date)
    if df2 is not None and not df2.empty:
        print(f"✅ 接口 'stock_news_em' 调用成功！获取到 {len(df2)} 条数据。")
        print("前几行数据：")
        print(df2.head())
    else:
        print("⚠️ 接口 'stock_news_em' 调用成功，但返回数据为空。")
except Exception as e:
    print(f"❌ 接口 'stock_news_em' 调用失败: {e}")