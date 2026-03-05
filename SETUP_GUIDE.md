# 🚀 环境配置指南 - 第一步

## 一、硬件要求

### 最低配置
- **CPU**: 8核及以上
- **内存**: 32GB
- **硬盘**: 200GB可用空间
- **GPU**: NVIDIA RTX 3090 (24GB) 或更高

### 推荐配置
- **GPU**: NVIDIA A100 (40GB) 或 RTX 4090 (24GB)
- **内存**: 64GB
- **硬盘**: SSD 500GB

## 二、软件环境

### 1. 操作系统
```bash
# Ubuntu 22.04 LTS (推荐)
# 或 Ubuntu 20.04 LTS
```

### 2. CUDA环境
```bash
# 检查NVIDIA驱动
nvidia-smi

# 安装CUDA 12.1
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run

# 配置环境变量 (~/.bashrc)
export CUDA_HOME=/usr/local/cuda-12.1
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

source ~/.bashrc
```

### 3. Python环境
```bash
# 安装Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 创建项目虚拟环境
conda create -n finance-qa python=3.10 -y
conda activate finance-qa
```

## 三、依赖安装

### 1. 创建 requirements.txt
```txt
# 核心框架
torch==2.1.0
transformers==4.36.0
langchain==0.1.0
langchain-community==0.0.10

# 数据采集
akshare==1.12.0
beautifulsoup4==4.12.0
requests==2.31.0
lxml==4.9.3
pdfplumber==0.10.3

# 向量检索
qdrant-client==1.7.0
sentence-transformers==2.2.2
rank-bm25==0.2.2
faiss-cpu==1.7.4

# 模型训练
llama-factory==0.3.0
peft==0.7.0
bitsandbytes==0.41.3
accelerate==0.25.0
deepspeed==0.12.0

# 推理部署
vllm==0.2.6
fastapi==0.108.0
uvicorn==0.25.0
streamlit==1.29.0

# 数据处理
pandas==2.1.4
numpy==1.26.2
scikit-learn==1.3.2
jieba==0.42.1

# 工具库
python-dotenv==1.0.0
loguru==0.7.2
tqdm==4.66.1
pyyaml==6.0.1
pytest==7.4.3

# API相关
httpx==0.25.2
aiohttp==3.9.1
openai==1.6.1  # OpenAI API兼容

# 可视化
matplotlib==3.8.2
plotly==5.18.0
```

### 2. 安装依赖
```bash
# 基础依赖
pip install -r requirements.txt

# PyTorch (根据CUDA版本选择)
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121

# Flash Attention (可选,加速训练)
pip install flash-attn --no-build-isolation
```

## 四、模型下载

### 1. 创建模型下载脚本
```bash
#!/bin/bash
# scripts/download_models.sh

set -e

MODEL_DIR="models"
mkdir -p $MODEL_DIR/{base,embeddings}

echo "📥 开始下载模型..."

# 1. 基座模型 Qwen2.5-7B-Instruct (约15GB)
echo "下载 Qwen2.5-7B-Instruct..."
cd $MODEL_DIR/base
git lfs install
git clone https://huggingface.co/Qwen/Qwen2.5-7B-Instruct

# 如果网络不好,使用镜像站
# git clone https://hf-mirror.com/Qwen/Qwen2.5-7B-Instruct

# 2. 嵌入模型 bge-large-zh-v1.5 (约1.3GB)
echo "下载 bge-large-zh-v1.5..."
cd ../embeddings
git clone https://huggingface.co/BAAI/bge-large-zh-v1.5

# 3. 重排模型 bge-reranker-large (约1.3GB)
echo "下载 bge-reranker-large..."
git clone https://huggingface.co/BAAI/bge-reranker-large

echo "✅ 模型下载完成!"
```

```bash
# 执行下载
chmod +x scripts/download_models.sh
./scripts/download_models.sh
```

### 2. 国内镜像加速 (可选)
```bash
# 使用 HF-Mirror
export HF_ENDPOINT=https://hf-mirror.com

# 或使用 ModelScope
pip install modelscope
modelscope download --model Qwen/Qwen2.5-7B-Instruct --local_dir models/base/Qwen2.5-7B-Instruct
```

## 五、数据库配置

### 1. Qdrant 向量数据库
```bash
# 方式1: Docker部署 (推荐)
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant

# 方式2: 本地安装
pip install qdrant-client
# 使用内存模式,数据保存到本地文件
```

### 2. SQLite (行情数据)
```python
# 自动创建,无需额外配置
import sqlite3
conn = sqlite3.connect('data/market_data.db')
```

## 六、环境变量配置

### 1. 创建 .env 文件
```bash
# .env
# 项目基础配置
PROJECT_NAME="金融资讯问答助手"
VERSION="1.0.0"
DEBUG=True

# 路径配置
PROJECT_ROOT=/path/to/finance-qa-assistant
DATA_DIR=${PROJECT_ROOT}/data
MODEL_DIR=${PROJECT_ROOT}/models
LOG_DIR=${PROJECT_ROOT}/logs

# 模型配置
BASE_MODEL_PATH=${MODEL_DIR}/base/Qwen2.5-7B-Instruct
EMBEDDING_MODEL_PATH=${MODEL_DIR}/embeddings/bge-large-zh-v1.5
RERANKER_MODEL_PATH=${MODEL_DIR}/embeddings/bge-reranker-large

# 向量数据库配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NEWS=finance_news
QDRANT_COLLECTION_ANNOUNCEMENT=finance_announcement

# API配置
OPENAI_API_KEY=your_key_here  # 用于SFT数据生成
OPENAI_API_BASE=https://api.openai.com/v1

# 爬虫配置
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# 训练配置
BATCH_SIZE=2
GRADIENT_ACCUMULATION_STEPS=8
LEARNING_RATE=5e-5
NUM_EPOCHS=2

# 推理配置
VLLM_PORT=8000
API_PORT=8001
STREAMLIT_PORT=8501
```

### 2. 加载环境变量
```python
# config/settings.py
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # 路径
    PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "."))
    DATA_DIR = PROJECT_ROOT / "data"
    MODEL_DIR = PROJECT_ROOT / "models"
    LOG_DIR = PROJECT_ROOT / "logs"
    
    # 模型
    BASE_MODEL_PATH = os.getenv("BASE_MODEL_PATH")
    EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH")
    
    # 数据库
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    
    # API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

settings = Settings()
```

## 七、验证安装

### 1. 创建测试脚本
```python
# scripts/verify_setup.py
import sys
import torch
import transformers
from qdrant_client import QdrantClient

def verify_cuda():
    print("🔍 检查CUDA...")
    if torch.cuda.is_available():
        print(f"✅ CUDA可用: {torch.version.cuda}")
        print(f"✅ GPU数量: {torch.cuda.device_count()}")
        print(f"✅ GPU型号: {torch.cuda.get_device_name(0)}")
    else:
        print("❌ CUDA不可用")
        return False
    return True

def verify_models():
    print("\n🔍 检查模型文件...")
    from pathlib import Path
    
    models = {
        "Qwen2.5-7B": "models/base/Qwen2.5-7B-Instruct",
        "BGE-Embedding": "models/embeddings/bge-large-zh-v1.5",
        "BGE-Reranker": "models/embeddings/bge-reranker-large"
    }
    
    all_ok = True
    for name, path in models.items():
        if Path(path).exists():
            print(f"✅ {name}: {path}")
        else:
            print(f"❌ {name}: {path} 不存在")
            all_ok = False
    
    return all_ok

def verify_qdrant():
    print("\n🔍 检查Qdrant...")
    try:
        client = QdrantClient(host="localhost", port=6333)
        print("✅ Qdrant连接成功")
        return True
    except Exception as e:
        print(f"❌ Qdrant连接失败: {e}")
        return False

def verify_dependencies():
    print("\n🔍 检查依赖包...")
    packages = {
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "langchain": None,
        "akshare": None,
        "qdrant-client": None
    }
    
    for pkg, version in packages.items():
        try:
            if version is None:
                __import__(pkg)
                print(f"✅ {pkg}: 已安装")
            else:
                print(f"✅ {pkg}: {version}")
        except ImportError:
            print(f"❌ {pkg}: 未安装")

if __name__ == "__main__":
    print("=" * 50)
    print("环境验证工具")
    print("=" * 50)
    
    results = []
    results.append(verify_cuda())
    results.append(verify_models())
    results.append(verify_qdrant())
    verify_dependencies()
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ 环境配置完成!")
    else:
        print("❌ 部分配置有问题,请检查")
        sys.exit(1)
```

```bash
# 运行验证
python scripts/verify_setup.py
```

## 八、目录初始化

```bash
# 创建项目目录结构
mkdir -p {data/{raw/{news,announcements,reports},processed/{chunks,embeddings},sft_data},models/{base,finetuned,embeddings},logs,qdrant_storage}

# 创建空的__init__.py
touch src/{__init__,data_collection/__init__,data_processing/__init__,retrieval/__init__,agent/__init__,training/__init__,inference/__init__,utils/__init__}.py

# 设置日志目录权限
chmod 755 logs

# 初始化Git (可选)
git init
echo "*.pyc
__pycache__/
*.log
.env
data/raw/
models/
qdrant_storage/
.vscode/
.idea/" > .gitignore
```

## 九、常见问题

### 1. CUDA out of memory
```bash
# 解决方案:
# - 减小batch_size
# - 使用gradient_checkpointing
# - 使用4-bit量化
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### 2. 模型下载慢
```bash
# 使用镜像站
export HF_ENDPOINT=https://hf-mirror.com
# 或使用代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

### 3. Qdrant连接失败
```bash
# 检查Docker是否运行
docker ps | grep qdrant

# 检查端口占用
lsof -i :6333

# 重启Qdrant
docker restart qdrant
```

## 十、下一步

环境配置完成后,进入数据采集阶段:
```bash
# 1. 运行数据采集脚本
python scripts/collect_data.py

# 2. 查看采集的数据
ls -lh data/raw/news/
head -n 5 data/raw/news/news_20240228.jsonl

# 3. 进入下一阶段...
```

---

**配置完成检查清单**:
- [ ] CUDA环境正常
- [ ] Python虚拟环境创建
- [ ] 依赖包安装完成
- [ ] 模型文件下载完成
- [ ] Qdrant启动正常
- [ ] 环境变量配置完成
- [ ] 目录结构创建完成
- [ ] 验证脚本通过

**预计耗时**: 2-4小时 (取决于网络速度)
