# CI/CD 配置说明

本项目已配置完整的CI/CD流水线，支持自动测试、构建和部署。

## 🚀 功能特性

### 自动测试 (CI)
- **代码语法检查**: 自动检查Python代码语法
- **依赖安装验证**: 验证requirements.txt中的依赖能正确安装
- **基础模块导入测试**: 确保主要模块能正常导入
- **PostgreSQL服务集成**: 在测试环境中自动启动PostgreSQL

### 自动构建和推送 (CD)
- **Docker镜像构建**: 自动构建优化的Docker镜像
- **GitHub Container Registry**: 自动推送到GHCR
- **智能缓存**: 使用GitHub Actions缓存加速构建
- **版本标签**: 自动生成语义化版本标签

### 生产部署
- **标签触发**: 推送`v*.*.*`格式的标签时自动部署
- **环境管理**: 支持多环境部署配置
- **部署通知**: 自动发送部署成功通知

## 📋 使用方法

### 1. 本地测试
```bash
# 运行基础测试
python -m pytest tests/ -v

# 构建Docker镜像
docker build -t ai-paper-writer .

# 使用docker-compose启动
docker-compose up -d
```

### 2. 生产部署
```bash
# 设置环境变量
export OPENAI_API_KEY="你的OpenAI密钥"
export TAVILY_API_KEY="你的Tavily密钥"

# 运行部署脚本
./deploy.sh
```

### 3. GitHub Actions 触发

#### 自动触发条件：
- **推送代码到main/develop分支**: 触发CI测试和构建
- **创建Pull Request到main分支**: 触发CI测试
- **推送版本标签(v*.*.*)**: 触发生产部署

#### 手动触发版本发布：
```bash
# 创建版本标签
git tag v1.0.0
git push origin v1.0.0
```

## 🔧 配置说明

### GitHub Secrets (可选)
如果需要额外的安全配置，可以在GitHub仓库设置中添加：
- `OPENAI_API_KEY`: OpenAI API密钥
- `TAVILY_API_KEY`: Tavily API密钥

### 环境变量
生产环境需要设置以下环境变量：
```bash
DATABASE_URL=postgresql://app:local@db:5432/appdb
OPENAI_API_KEY=你的OpenAI密钥
TAVILY_API_KEY=你的Tavily密钥
```

## 📁 文件结构
```
.github/
└── workflows/
    ├── ci.yml          # 持续集成工作流
    └── deploy.yml      # 生产部署工作流
tests/
└── test_basic.py       # 基础测试用例
deploy.sh               # 生产部署脚本
docker-compose.yml      # Docker编排配置
```

## 🔍 监控和调试

### 查看GitHub Actions运行状态
1. 访问仓库的 "Actions" 标签页
2. 查看最新的工作流运行
3. 点击具体运行查看详细日志

### 常见问题

**Q: 工作流运行失败怎么办？**
A: 检查Actions日志，常见问题包括：
- 环境变量未设置
- 依赖安装失败
- 测试用例失败

**Q: 如何回滚版本？**
A: 可以通过GHCR拉取之前的镜像版本：
```bash
docker pull ghcr.io/用户名/ai-paper-writer:v1.0.0
docker tag ghcr.io/用户名/ai-paper-writer:v1.0.0 ai-paper-writer:latest
docker-compose up -d
```

## 🛡️ 安全建议

1. **敏感信息**: API密钥等敏感信息通过环境变量传递
2. **镜像安全**: 使用官方基础镜像，定期更新依赖
3. **访问控制**: 限制生产环境的访问权限
4. **备份策略**: 定期备份PostgreSQL数据库

---

如需更多帮助，请查看GitHub Actions官方文档或联系项目维护者。