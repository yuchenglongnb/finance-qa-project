# 🚀 快速开始指南

## 第一步：环境配置 (预计 2-3 小时)

### 1. 克隆并创建目录结构

```bash
# 创建项目根目录
mkdir finance-qa-assistant
cd finance-qa-assistant

# 创建目录结构
mkdir -p {data/{raw/{news,announcements,reports},processed/{chunks,embeddings},sft_data},models/{base,finetuned,embeddings},logs,qdrant_storage,src/{data_collection,data_processing,retrieval,agent/{tools},training,inference,utils},backend/{routers,schemas},frontend/{components,static},scripts,tests,notebooks,docs}

# 创建__init__.py文件
touch src/__init__.py
touch src/data_collection/__init__.py
touch src/agent/tools/__init__.py
```

### 2. 配置Python环境

```bash
# 创建虚拟环境
conda create -n finance-qa python=3.10 -y
conda activate finance-qa

# 安装基础依赖
pip install -r requirements.txt

# 安装PyTorch (根据CUDA版本)
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu121
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
nano .env  # 或使用你喜欢的编辑器
```

必须配置的变量:
```bash
PROJECT_ROOT=/path/to/your/project
OPENAI_API_KEY=sk-xxx  # 用于生成SFT数据(可选)
```

### 4. 启动Qdrant向量数据库

```bash
# 使用Docker (推荐)
docker run -d -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    --name qdrant \
    qdrant/qdrant

# 验证
curl http://localhost:6333
```

### 5. 下载模型 (可选，后续再做)

```bash
# 暂时跳过，先专注数据采集
# 后续需要时再下载
```

## 第二步：数据采集 (当前重点)

### 快速测试采集

```bash
# 1. 测试新闻爬虫 (获取最近3天，100条)
python -c "
from src.data_collection.news_crawler import NewsCrawler
crawler = NewsCrawler()
data = crawler.run(days=3, max_news=100)
print(f'✅ 获取 {len(data)} 条新闻')
"

# 2. 测试公告爬虫 (获取最近7天，50条)
python -c "
from src.data_collection.announcement_crawler import AnnouncementCrawler
from datetime import datetime, timedelta
crawler = AnnouncementCrawler()
start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
data = crawler.run(start_date=start, max_announcements=50)
print(f'✅ 获取 {len(data)} 条公告')
"
```

### 正式采集数据

```bash
# 采集30天新闻 + 90天公告
python scripts/collect_data.py \
    --type all \
    --days 30 \
    --max-news 10000 \
    --max-announcements 5000

# 查看采集结果
ls -lh data/raw/news/
ls -lh data/raw/announcements/

# 数据质量验证（抽样100条）
python scripts/verify_data_quality.py --sample-size 100

# 查看数据样本
head -n 1 data/raw/news/*.jsonl | python -m json.tool
```

### 采集特定股票数据

```bash
# 采集几只明星股票的新闻
python scripts/collect_data.py \
    --type stock \
    --stocks 600519 000858 002594 300750 \
    --days 30

# 600519: 贵州茅台
# 000858: 五粮液
# 002594: 比亚迪
# 300750: 宁德时代
```

## 第三步：数据验证

### 验证数据质量

```python
# 运行验证脚本
python scripts/verify_data.py

# 或手动检查
python -c "
import json
from pathlib import Path

# 读取新闻数据
news_files = list(Path('data/raw/news').glob('*.jsonl'))
if news_files:
    with open(news_files[0], 'r', encoding='utf-8') as f:
        sample = json.loads(f.readline())
        print('新闻样本:')
        print(json.dumps(sample, ensure_ascii=False, indent=2))
        
    # 统计
    total = sum(1 for file in news_files for _ in open(file))
    print(f'\n总计: {total} 条新闻')
"
```

### 数据清洗

```bash
# 去重和清洗
python scripts/clean_data.py \
    --input data/raw/news/*.jsonl \
    --output data/processed/news_cleaned.jsonl
```

## 常见问题

### 1. AKShare 获取数据失败

```python
# 检查网络连接
import requests
response = requests.get('http://www.baidu.com')
print(response.status_code)  # 应该是200

# 检查AKShare
import akshare as ak
print(ak.__version__)  # 确认版本

# 测试接口
df = ak.stock_news_em()
print(df.head())
```

### 2. 数据量太少

```bash
# 方案1: 增加天数
python scripts/collect_data.py --days 90

# 方案2: 添加更多数据源
# 编辑 news_crawler.py 添加新源

# 方案3: 采集多只股票
python scripts/collect_data.py \
    --type stock \
    --stocks $(cat stock_list.txt)
```

### 3. 内存不足

```bash
# 分批采集
for i in {1..10}; do
    python scripts/collect_data.py \
        --days $((i*3)) \
        --max-news 1000
    sleep 60
done
```

## 检查点 ✅

完成第一步后，你应该有:

- [ ] ✅ Python环境配置完成
- [ ] ✅ Qdrant运行正常
- [ ] ✅ 成功采集到 5000+ 条新闻
- [ ] ✅ 成功采集到 2000+ 条公告
- [ ] ✅ 数据保存为JSONL格式
- [ ] ✅ 数据包含完整字段

**数据目标**:
- 新闻: 5,000 - 30,000 条
- 公告: 2,000 - 5,000 条
- 总计: 7,000+ 条

## 下一步

环境和数据配置完成后，进入:
- 📝 **Week 1 Day 4**: 数据清洗和分块
- 📝 **Week 1 Day 5**: 向量化和建库

---

## 参考命令速查

```bash
# 激活环境
conda activate finance-qa

# 采集所有数据
python scripts/collect_data.py --type all --days 30

# 查看日志
tail -f logs/data_collection_$(date +%Y%m%d).log

# 统计数据量
find data/raw -name "*.jsonl" -exec wc -l {} +

# 测试Qdrant
curl http://localhost:6333/collections

# 查看进程
ps aux | grep python

# 清理数据
rm -rf data/raw/*/
```

---

**当前任务状态**: ✅ 环境配置完成，开始数据采集
**预计完成时间**: 第一天 6-8小时

需要帮助? 查看 `docs/TROUBLESHOOTING.md`
