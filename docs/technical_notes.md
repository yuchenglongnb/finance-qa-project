# 技术实现笔记（与当前代码同步）

## 1. 数据采集层

### 1.1 总体设计
- 统一抽象：`BaseCrawler.run()`（fetch -> parse -> save）
- 新闻源：`NewsCrawler`
- 公告源：`AnnouncementCrawler`

### 1.2 公告采集（关键修复）

#### P1: 指定股票返回 0 条
- 问题：
  - `ak.stock_notice_report(symbol=...)` 在当前环境不支持该参数
  - 全量过滤时未覆盖上游真实字段（如 `代码`）
  - cninfo fallback 未传 `stock`，导致回退成全市场数据
- 修复：
  - 优先尝试 `ak.stock_notice_report_em(symbol=stock_code)`（若当前 akshare 版本不存在该接口，自动降级）
  - `_get_stock_code` 补充 `代码` / `stockCode` 等字段
  - 新增 `_fetch_cninfo_stock_announcements`，payload 传 `stock: "002594,"`
  - cninfo 返回后强制二次过滤 `stock_code == 目标代码`，避免混入全市场数据
  - `fetch()` 在有 `stock_codes` 时 fallback 逐代码查询，不再全市场覆盖

#### P2: 节假日连续 WARNING 噪声
- 问题：节假日空数据时 AKShare 可能触发 `KeyError('代码')`，与真异常混在一起
- 修复：`_fetch_all_announcements` 中 `KeyError` 单独降级为 `DEBUG`，其余异常保留 `WARNING`

#### P5: 公告类型全是 PDF
- 问题：cninfo 字段 `announcementTypeName/announcementType` 未完整映射
- 修复：
  - `_get_type` candidates 补充 `announcementTypeName` / `announcementType`
  - 新增 `_map_cninfo_type_code()` 把常见 6 位类型码映射成可读类别

## 2. 数据处理层

### 2.1 清洗去重
- 脚本：`scripts/clean_and_prepare_data.py`
- 规则：
  - 关键字段空值过滤
  - 最小长度过滤
  - 稳定主键（sha1）去重

### 2.2 公告正文增强
- 脚本：`scripts/enrich_announcement_content.py`
- 流程：
  - 仅处理 `content` 为空的公告
  - 优先 `pdf_url`，其次 `url`
  - 定期 checkpoint 落盘（`save-every`）

#### P4: enrich 成功率与内容质量可见性
- 修复：
  - `announcement_content_extractor.py` 增加 `clean_replacement_chars()`
  - U+FFFD 比例过高的行直接丢弃，其他行移除替换字符
  - enrich 报告新增：
    - `content_len_avg`
    - `content_len_min`
    - `content_len_max`
    - `content_len_p50`

## 3. 检索层

### 3.1 语料构建
- 脚本：`scripts/build_retrieval_corpus.py`
- 策略：公告优先使用较新的 `announcements_enriched.jsonl`；否则回退 `announcements_cleaned.jsonl`

### 3.2 混合检索
- 模块：`src/retrieval/hybrid_retriever.py`
- 评分：
  - `bm25_score`
  - `overlap_score`（IDF 加权版）
  - `entity_boost`

#### P3: 查询“比亚迪最近公告”结果不相关
- 根因：语料里没有目标实体时，检索退化为全量匹配
- 修复：
  - 预加载常见实体到 jieba 词典，避免切词拆散
  - overlap 改为 IDF 加权，降低“公告”等高频词干扰
  - 增加实体过滤（股票代码/公司名命中时只在子集检索）
  - 输出 `entity_filter_applied` / `entity_filter_hits` 便于排查

## 4. 运行诊断建议

### 4.1 先看数据是否包含目标实体
- 若 `entity_filter_hits=0`，先判定是“语料缺失”而不是“检索算法问题”

### 4.2 公告增强后看长度分布
- 若 `content_len_p50` 过低，说明虽然成功率高，但正文信息量不足

### 4.3 节假日日志
- `KeyError('代码')` 在节假日期间归为正常空数据，不应作为故障处理

## 5. 下一步建议
1. 增加向量召回（embedding + 向量库）
2. 与当前混合检索融合（BM25 + vector + entity boost）
3. 引入 reranker 做最终排序
4. 增加按实体的数据覆盖率报告（公司名/代码维度）
