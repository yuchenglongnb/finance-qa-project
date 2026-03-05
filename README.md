# 🏦 金融资讯智能问答助手

基于 RAG + Agent 的A股信息整合系统 | 教育工具，非投资建议

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 项目简介

这是一个**合规、实用、可量化**的金融资讯问答系统，专注于：
- ✅ 新闻解读和信息整合
- ✅ 公告解析和关键信息提取  
- ✅ 行业分析和公司对比
- ❌ **不提供**投资建议和股价预测

## 🎯 核心特点

| 特点 | 说明 |
|-----|-----|
| **合规性强** | 仅做信息整合，不涉及买卖建议 |
| **数据易得** | 基于公开新闻和官方公告 |
| **效果可测** | 信息准确度可量化评估 |
| **实用价值** | 解决投资者信息获取痛点 |

## 🏗️ 技术架构

```
用户输入
   ↓
Agent 编排层 (LangChain + ReAct)
   ├─ 新闻检索工具
   ├─ 公告检索工具  
   ├─ 行情查询工具
   └─ 财务计算工具
   ↓
RAG 检索层 (BM25 + Vector + Rerank)
   ↓
数据存储层
   ├─ 新闻库 (Qdrant)
   ├─ 公告库 (Qdrant)
   └─ 行情数据 (SQLite)
   ↓
模型推理层 (Qwen2.5-7B + vLLM)
```

## 🔧 技术栈

```yaml
数据采集: akshare, beautifulsoup4, pdfplumber
向量检索: Qdrant, bge-large-zh-v1.5, bge-reranker-large, rank_bm25
Agent框架: LangChain, LangGraph
模型训练: LLaMA-Factory, QLoRA 4-bit, Qwen2.5-7B-Instruct
推理部署: vLLM, FastAPI, Streamlit
```

## 📦 文件说明

```
finance-qa-project/
├── PROJECT_STRUCTURE.md      # 完整项目结构和设计原则
├── SETUP_GUIDE.md            # 详细环境配置指南 (2-4小时)
├── QUICKSTART.md             # 快速开始教程 (当前重点)
├── requirements.txt          # Python依赖列表
├── .env.example              # 环境变量配置模板
│
├── src/data_collection/      # 数据采集模块
│   ├── base_crawler.py       # 爬虫基类
│   ├── news_crawler.py       # 新闻爬虫 (东方财富+金十数据)
│   └── announcement_crawler.py  # 公告爬虫
│
└── scripts/
    └── collect_data.py       # 统一数据采集脚本
```

## 🚀 快速开始

### 第一步：环境准备

```bash
# 1. 创建虚拟环境
conda create -n finance-qa python=3.10 -y
conda activate finance-qa

# 2. 安装依赖 (默认最小依赖，用于采集与验证)
pip install -r requirements.txt

# 如需完整栈（检索/训练/部署）
# pip install -r requirements-full.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必要配置

# 4. 启动Qdrant (Docker)
docker run -d -p 6333:6333 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    --name qdrant \
    qdrant/qdrant
```

### 第二步：数据采集 (当前任务)

```bash
# 快速测试 (获取最近3天100条新闻)
python -c "
from src.data_collection.news_crawler import NewsCrawler
crawler = NewsCrawler()
data = crawler.run(days=3, max_news=100)
print(f'✅ 成功: {len(data)} 条')
"

# 正式采集 (30天新闻 + 90天公告)
python scripts/collect_data.py \
    --type all \
    --days 30 \
    --max-news 10000 \
    --max-announcements 5000

# 查看结果
ls -lh data/raw/news/
ls -lh data/raw/announcements/

# 数据质量验证（默认抽样100条）
python scripts/verify_data_quality.py

# 清洗与去重（产出 processed 数据）
python scripts/clean_and_prepare_data.py \
    --data-dir data/raw \
    --output-dir data/processed

# 构建检索语料（分块）
python scripts/build_retrieval_corpus.py \
    --processed-dir data/processed \
    --chunk-size 400 \
    --chunk-overlap 50

# 运行混合检索（BM25 + token-overlap）
python scripts/run_retrieval.py \
    --query "比亚迪最近有什么公告？" \
    --top-k 5
```

### 数据目标

- ✅ 新闻: 5,000 - 30,000 条
- ✅ 公告: 2,000 - 5,000 条
- ✅ 总计: 7,000+ 条高质量数据

## 📚 详细文档

| 文档 | 内容 | 阅读时间 |
|-----|-----|---------|
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 完整架构设计和扩展方案 | 15分钟 |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 环境配置详细步骤 | 30分钟 |
| [QUICKSTART.md](QUICKSTART.md) | 快速开始实操指南 | 10分钟 |
| [docs/interview_playbook.md](docs/interview_playbook.md) | 面试技术细节与高频问答 | 20分钟 |

## 📊 开发时间线

### Week 1: 数据 + RAG (7天)
- ✅ Day 1: 环境配置 + 数据源调研
- 🔄 Day 2-3: **数据采集 (当前任务)**
- ✅ Day 4: 数据清洗 + 分块（已实现）
- ⏸️ Day 5: 向量化 + 建库
- 🔄 Day 6-7: 混合检索（规则融合版本已实现，后续接入向量召回与重排）

### Week 2: SFT + Agent (7天)
- ⏸️ Day 8-9: SFT数据生成
- ⏸️ Day 10-11: QLoRA微调
- ⏸️ Day 12-14: Agent工具开发

### Week 3: 部署 + Demo (7天)
- ⏸️ Day 15-17: vLLM + API + 前端
- ⏸️ Day 18-21: 测试 + 文档

## 🎯 核心功能

### P0 必做功能
1. **公司新闻问答** - "比亚迪最近有什么重要新闻？"
2. **公告解读** - "解读中国平安最新财报"
3. **行业分析** - "新能源汽车行业最近政策？"

### P1 增强功能
4. **多公司对比** - "对比宁德时代和比亚迪Q3业绩"
5. **历史事件查询** - "2023年哪些公司重大重组？"

## 🛠️ 使用示例

### 采集所有数据
```bash
python scripts/collect_data.py --type all --days 30
```

### 采集特定股票
```bash
python scripts/collect_data.py \
    --type stock \
    --stocks 600519 000858 002594 \
    --days 30
```

### 查看统计信息
```bash
python -c "
import json
from pathlib import Path

files = list(Path('data/raw/news').glob('*.jsonl'))
total = sum(1 for f in files for _ in open(f))
print(f'总计: {total} 条新闻')
"
```

## ⚠️ 合规声明

```
【风险提示】
本系统提供的所有信息仅供参考学习，不构成任何投资建议。
股市有风险，投资需谨慎。请根据自身情况做出独立判断。
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📧 联系方式

- GitHub Issues: [提交问题](https://github.com/your-repo/issues)
- Email: your-email@example.com

---

**当前状态**: 🔄 数据采集 PoC 阶段（已提供采集骨架与脚本）

**已实现**: 新闻/公告采集、统一采集入口、基础字段标准化与 JSONL 落盘
**已实现（新增）**: 数据清洗去重、稳定 ID、chunk 构建、混合检索基础版

**未实现（规划中）**: 向量化建库、向量召回融合、Reranker、Agent、API、前端与系统化测试

**下一步**: 接入向量召回与 reranker，完成最小可用 RAG 闭环

**当前数据限制**: 公告源多数仅有标题、正文缺失；当前检索先基于标题回退，后续会补公告正文抽取。

查看 [QUICKSTART.md](QUICKSTART.md) 了解详细步骤！
