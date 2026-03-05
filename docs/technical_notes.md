# 技术实现笔记（随代码同步）

## 1. 数据层

### 1.1 采集
- 统一抽象：`BaseCrawler.run()` 定义采集标准流程。
- 子模块：
  - `NewsCrawler`：财经新闻采集与标准化字段映射。
  - `AnnouncementCrawler`：公告采集、日期过滤、类型分类。
- 已修复：
  - 公告无 `stock_codes` 时未写入总列表的问题。
  - `collect_data.py` 的 `--output-dir` 参数贯通。

### 1.2 质量验证
- 脚本：`scripts/verify_data_quality.py`
- 关键指标：
  - `valid_rate`
  - 字段覆盖率（news: title/publish_time/content/url；announcement: title/stock_code/publish_date）

### 1.3 清洗去重
- 脚本：`scripts/clean_and_prepare_data.py`
- 规则：
  - 空值过滤（关键字段缺失剔除）
  - 最小长度过滤（`min_content_len`）
  - 稳定 ID（`sha1`）去重，替代 Python `hash()`

## 2. 检索层（当前版本）

### 2.1 文本分块
- 模块：`src/data_processing/text_splitter.py`
- 默认参数：
  - `chunk_size=400`
  - `chunk_overlap=50`
  - `min_chunk_len=30`
- 产物：`data/processed/chunks/retrieval_chunks.jsonl`
- 特殊处理：
  - 公告源常缺失 `content`，当前回退为 `title` 参与分块，确保可检索。

### 2.2 混合检索
- BM25：`src/retrieval/bm25_retriever.py`
- Hybrid：`src/retrieval/hybrid_retriever.py`
- 融合打分：
  - `final_score = 0.7 * bm25_score + 0.3 * overlap_score`
  - `overlap_score = |Q ∩ D| / |Q|`
- 当前已知限制：
  - 新闻样本量较小（当前仅 8 条）时，检索稳定性有限。
  - 公告多数为标题级检索，语义深度受限；后续应补公告正文解析（PDF/HTML）。

### 2.3 检索执行
- 脚本：`scripts/run_retrieval.py`
- 输入：自然语言查询
- 输出：Top-K chunk（score、来源、时间、URL）

## 3. 设计取舍

### 3.1 为什么先做规则混合检索
- 先验证链路正确性和数据质量，避免过早引入重依赖。
- 在小样本阶段，先保证稳定性和可解释性，再做深度优化。

### 3.2 为什么先不做向量召回
- 当前数据规模与阶段目标允许先用 BM25/规则融合打底。
- 下一阶段会接入 embedding + 向量库后评估收益。

## 4. 下一步开发清单
1. 增加向量化脚本（embedding 生成 + 本地缓存）。
2. 接入向量数据库（Qdrant）并与 BM25 做召回融合。
3. 增加公告正文抽取（公告链接/PDF）。
4. 增加 reranker，比较融合前后 Top-K 相关性。
5. 完成答案组装模块（证据引用 + 风险提示）。
