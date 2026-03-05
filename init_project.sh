#!/bin/bash
# 项目初始化脚本
# 一键创建完整目录结构

set -e

echo "🚀 开始初始化金融资讯问答助手项目..."

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目名称
PROJECT_NAME="finance-qa-assistant"

# 创建项目根目录
echo -e "${BLUE}📁 创建项目目录结构...${NC}"
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

# 数据目录
mkdir -p data/{raw/{news,announcements,reports},processed/{chunks,embeddings},sft_data}
echo -e "${GREEN}✅ 数据目录创建完成${NC}"

# 模型目录
mkdir -p models/{base,finetuned,embeddings}
echo -e "${GREEN}✅ 模型目录创建完成${NC}"

# 源代码目录
mkdir -p src/{data_collection,data_processing,retrieval,agent/{tools},training,inference,utils}
echo -e "${GREEN}✅ 源代码目录创建完成${NC}"

# 后端目录
mkdir -p backend/{routers,schemas}
echo -e "${GREEN}✅ 后端目录创建完成${NC}"

# 前端目录
mkdir -p frontend/{components,static}
echo -e "${GREEN}✅ 前端目录创建完成${NC}"

# 其他目录
mkdir -p {logs,scripts,tests,notebooks,docs,qdrant_storage}
echo -e "${GREEN}✅ 其他目录创建完成${NC}"

# 创建 __init__.py 文件
echo -e "${BLUE}📝 创建Python包文件...${NC}"
touch src/__init__.py
touch src/data_collection/__init__.py
touch src/data_processing/__init__.py
touch src/retrieval/__init__.py
touch src/agent/__init__.py
touch src/agent/tools/__init__.py
touch src/training/__init__.py
touch src/inference/__init__.py
touch src/utils/__init__.py
touch backend/__init__.py
touch backend/routers/__init__.py
touch backend/schemas/__init__.py
touch frontend/__init__.py
touch tests/__init__.py
echo -e "${GREEN}✅ Python包文件创建完成${NC}"

# 创建 .gitignore
echo -e "${BLUE}📝 创建 .gitignore...${NC}"
cat > .gitignore << 'EOF'
# Python
*.pyc
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 虚拟环境
venv/
ENV/
env/
.venv

# 日志
*.log
logs/

# 数据文件
data/raw/
data/processed/
*.jsonl
*.csv
*.db

# 模型文件
models/base/
models/finetuned/
*.bin
*.pt
*.pth
*.safetensors

# 向量数据库
qdrant_storage/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# 环境变量
.env
.env.local

# Jupyter
.ipynb_checkpoints/
*.ipynb

# 缓存
.cache/
*.cache

# 测试
.pytest_cache/
htmlcov/
.coverage
EOF
echo -e "${GREEN}✅ .gitignore 创建完成${NC}"

# 创建 README.md
echo -e "${BLUE}📝 创建 README.md...${NC}"
cat > README.md << 'EOF'
# 金融资讯智能问答助手

基于 RAG + Agent 的A股信息整合系统

## 快速开始

1. 复制项目文件到此目录
2. 参考 SETUP_GUIDE.md 配置环境
3. 参考 QUICKSTART.md 开始开发

## 目录结构

- `src/` - 源代码
- `data/` - 数据文件
- `models/` - 模型文件
- `scripts/` - 脚本工具
- `docs/` - 文档

更多详情请查看 PROJECT_STRUCTURE.md
EOF
echo -e "${GREEN}✅ README.md 创建完成${NC}"

# 设置权限
chmod 755 logs
chmod 755 data
chmod 755 scripts

# 显示目录结构
echo -e "\n${YELLOW}📦 项目结构:${NC}"
tree -L 2 -d --dirsfirst 2>/dev/null || ls -R

# 完成
echo -e "\n${GREEN}✅ 项目初始化完成!${NC}"
echo -e "\n${BLUE}下一步:${NC}"
echo "1. cd $PROJECT_NAME"
echo "2. 复制提供的配置文件和代码文件到对应目录"
echo "3. cp .env.example .env"
echo "4. 编辑 .env 文件配置环境变量"
echo "5. conda create -n finance-qa python=3.10"
echo "6. conda activate finance-qa"
echo "7. pip install -r requirements.txt"
echo "8. python scripts/collect_data.py --type all"
echo -e "\n${YELLOW}查看 QUICKSTART.md 了解详细步骤!${NC}"
