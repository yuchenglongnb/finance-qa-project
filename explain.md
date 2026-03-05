# 项目说明与学习导航

## 当前项目进度
- 已完成：采集、质量验证、清洗去重、BM25 检索演示
- 进行中：最小 RAG 闭环（证据检索 + 回答组装）
- 未完成：向量检索融合、重排、Agent 编排、API/前端

## 推荐学习顺序
1. 跑通采集：`python scripts/collect_data.py --type all --days 30`
2. 做质量检查：`python scripts/verify_data_quality.py --sample-size 100 --data-dir data/raw`
3. 做清洗去重：`python scripts/clean_and_prepare_data.py --data-dir data/raw --output-dir data/processed`
4. 构建分块语料：`python scripts/build_retrieval_corpus.py --processed-dir data/processed`
5. 跑混合检索：`python scripts/run_retrieval.py --query "比亚迪最近有什么公告？" --top-k 5`
6. 阅读技术文档：`docs/technical_notes.md`

## 项目技术主线
- 数据入口标准化：`BaseCrawler` 抽象统一流程
- 数据治理：字段有效性检查 + 清洗去重 + 稳定 ID
- 检索验证：分块 + BM25 + overlap 融合，再升级向量检索融合
- 输出合规：来源可追溯 + 风险提示 + 不给投资建议

## 面试表达建议
- 不强调“我用了很多框架”，要强调“我怎么控制风险和保证可验证”。
- 不强调“最终准确率很高”，要强调“我如何搭建评估和持续优化机制”。
- 主动讲已修复的问题：公告返回空、输出目录参数、依赖版本漂移。
