# 金融资讯问答助手 - 项目架构

## 📁 目录结构（目标规划）

> 说明：以下为目标结构蓝图，当前代码仓库仅实现了其中的数据采集相关模块。

```
finance-qa-assistant/
├── README.md                     # 项目说明
├── requirements.txt              # Python依赖
├── .env.example                  # 环境变量模板
├── .gitignore                   # Git忽略配置
│
├── config/                      # 配置文件目录
│   ├── __init__.py
│   ├── settings.py              # 全局配置
│   ├── model_config.yaml        # 模型配置
│   └── data_sources.yaml        # 数据源配置
│
├── data/                        # 数据目录
│   ├── raw/                     # 原始数据
│   │   ├── news/               # 新闻数据
│   │   ├── announcements/      # 公告数据
│   │   └── reports/            # 研报数据
│   ├── processed/               # 处理后数据
│   │   ├── chunks/             # 分块后的文本
│   │   └── embeddings/         # 向量文件
│   └── sft_data/               # 微调数据
│       ├── train.jsonl
│       └── test.jsonl
│
├── models/                      # 模型文件目录
│   ├── base/                    # 基座模型
│   ├── finetuned/              # 微调后模型
│   └── embeddings/             # 嵌入模型
│
├── src/                        # 源代码
│   ├── __init__.py
│   │
│   ├── data_collection/        # 数据采集模块
│   │   ├── __init__.py
│   │   ├── news_crawler.py     # 新闻爬虫
│   │   ├── announcement_crawler.py  # 公告爬虫
│   │   ├── quote_fetcher.py    # 行情数据
│   │   └── data_cleaner.py     # 数据清洗
│   │
│   ├── data_processing/        # 数据处理模块
│   │   ├── __init__.py
│   │   ├── text_splitter.py    # 文本分块
│   │   ├── embedder.py         # 向量化
│   │   └── deduplicator.py     # 去重
│   │
│   ├── retrieval/              # 检索模块
│   │   ├── __init__.py
│   │   ├── vector_store.py     # 向量数据库
│   │   ├── bm25_retriever.py   # BM25检索
│   │   ├── hybrid_retriever.py # 混合检索
│   │   └── reranker.py         # 重排模型
│   │
│   ├── agent/                  # Agent模块
│   │   ├── __init__.py
│   │   ├── tools/              # 工具定义
│   │   │   ├── __init__.py
│   │   │   ├── news_tool.py
│   │   │   ├── announcement_tool.py
│   │   │   ├── quote_tool.py
│   │   │   └── calculator_tool.py
│   │   ├── agent_executor.py   # Agent执行器
│   │   └── prompts.py          # Prompt模板
│   │
│   ├── training/               # 训练模块
│   │   ├── __init__.py
│   │   ├── data_generator.py   # SFT数据生成
│   │   ├── trainer.py          # 训练脚本
│   │   └── evaluator.py        # 评估脚本
│   │
│   ├── inference/              # 推理模块
│   │   ├── __init__.py
│   │   ├── model_loader.py     # 模型加载
│   │   └── inference_engine.py # 推理引擎
│   │
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       ├── logger.py           # 日志工具
│       ├── validators.py       # 验证器
│       └── helpers.py          # 辅助函数
│
├── backend/                    # 后端服务
│   ├── __init__.py
│   ├── app.py                  # FastAPI应用
│   ├── routers/                # 路由
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── health.py
│   └── schemas/                # 数据模型
│       ├── __init__.py
│       └── request_models.py
│
├── frontend/                   # 前端界面
│   ├── app.py                  # Streamlit主程序
│   ├── components/             # UI组件
│   │   ├── __init__.py
│   │   ├── chat_interface.py
│   │   └── visualizations.py
│   └── static/                 # 静态资源
│       ├── styles.css
│       └── logo.png
│
├── scripts/                    # 脚本目录
│   ├── setup_env.sh            # 环境配置脚本
│   ├── download_models.sh      # 模型下载
│   ├── collect_data.py         # 数据采集
│   ├── build_vector_db.py      # 构建向量库
│   └── run_training.sh         # 训练脚本
│
├── tests/                      # 测试目录
│   ├── __init__.py
│   ├── test_retrieval.py
│   ├── test_agent.py
│   └── test_api.py
│
├── notebooks/                  # Jupyter笔记本
│   ├── 01_data_exploration.ipynb
│   ├── 02_rag_testing.ipynb
│   └── 03_agent_demo.ipynb
│
└── docs/                       # 文档目录
    ├── API.md                  # API文档
    ├── DEPLOYMENT.md           # 部署指南
    └── DEVELOPMENT.md          # 开发指南
```

## 🏗️ 架构设计原则

### 1. 模块化设计
- 每个模块职责单一,高内聚低耦合
- 通过接口/抽象类定义标准
- 便于单独测试和替换

### 2. 配置化管理
- 所有配置集中在config目录
- 使用环境变量管理敏感信息
- 支持不同环境(dev/test/prod)

### 3. 可扩展性
- 数据源:新增crawler只需继承BaseCrawler
- 工具:新增tool只需实现Tool接口
- 模型:支持热切换不同LLM

### 4. 错误处理
- 统一异常处理机制
- 详细日志记录
- 优雅降级策略

## 🔌 核心接口设计

### BaseCrawler (数据采集基类)
```python
class BaseCrawler(ABC):
    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict]:
        """获取数据"""
        pass
    
    @abstractmethod
    def parse(self, raw_data) -> List[Dict]:
        """解析数据"""
        pass
    
    @abstractmethod
    def save(self, data: List[Dict], output_path: str):
        """保存数据"""
        pass
```

### BaseRetriever (检索基类)
```python
class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> List[Document]:
        """检索相关文档"""
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[Document]):
        """添加文档"""
        pass
```

### BaseTool (Agent工具基类)
```python
class BaseTool(ABC):
    name: str
    description: str
    
    @abstractmethod
    def run(self, **kwargs) -> str:
        """执行工具"""
        pass
```

## 📊 数据流图

```
用户输入
  ↓
Agent解析意图
  ↓
决策调用工具
  ├─→ 新闻检索 → 混合检索 → Qdrant/BM25 → 重排
  ├─→ 公告检索 → 混合检索 → Qdrant/BM25 → 重排
  ├─→ 行情查询 → AKShare API
  └─→ 计算工具 → Python eval
  ↓
整合检索结果
  ↓
调用LLM生成回答
  ↓
后处理(添加来源/免责声明)
  ↓
返回用户
```

## 🔄 可扩展点

1. **新增数据源**: 在`data_collection/`添加新crawler
2. **新增检索策略**: 在`retrieval/`实现新retriever
3. **新增Agent工具**: 在`agent/tools/`添加新tool
4. **新增LLM后端**: 在`inference/`适配新模型API
5. **新增评估指标**: 在`training/evaluator.py`添加
