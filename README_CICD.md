# CICD 配置说明（腾讯云托管版本）

本项目已配置完整的CI/CD流水线，与腾讯云云托管深度集成，实现全自动部署。

## 🚀 功能特性

### 持续集成 (CI) - GitHub Actions
- **代码质量检查**: flake8 代码规范检查
- **真实 API 测试**: 使用真实 LLM API 进行端到端测试
- **数据库测试**: PostgreSQL 数据库集成测试
- **覆盖率报告**: 代码覆盖率统计和报告
- **成本控制**: 智能限制 API 使用成本
- **Docker 构建**: 自动构建和测试 Docker 镜像

### 持续部署 (CD) - 腾讯云托管
- **Webhook自动触发**: GitHub推送代码后自动通知腾讯云
- **CI门禁检查**: 只有测试通过的代码才会部署
- **自动镜像构建**: 腾讯云自动构建Docker镜像
- **零停机部署**: 自动滚动更新，服务不中断
- **自动健康检查**: 部署后自动验证服务状态
- **一键回滚**: 支持快速回滚到前一版本

## 📋 使用方法

### 1. 本地测试
```bash
# 运行完整测试套件（包含真实 API 测试）
./run_tests.sh

# 仅运行基础测试（免费）
python -m pytest tests/test_basic.py tests/test_models.py

# 仅运行真实 API 测试
python -m pytest tests/test_real_api.py
```

### 2. 自动化流程说明

#### 完整CI/CD流程

```
你本地开发 → git push → GitHub Actions CI → 腾讯云托管 CD → 生产环境更新
```

#### 详细流程

**第1步：代码推送**
- 执行 `git add . && git commit -m "更新说明" && git push origin main`

**第2步：GitHub Actions自动触发**
- 代码质量检查（flake8）
- 语法验证
- 综合测试套件执行
- 覆盖率报告生成
- Docker镜像构建测试

**第3步：Webhook通知腾讯云**
- GitHub自动给腾讯云发送部署通知
- 腾讯云检查CI结果：
  - ✅ CI通过（绿色）：继续部署
  - ❌ CI失败（红色）：取消部署

**第4步：腾讯云自动部署**
- 自动拉取最新代码
- 自动构建Docker镜像
- 自动停止旧容器
- 自动启动新容器
- 自动健康检查
- 自动清理旧镜像

**第5步：部署完成**
- 服务自动更新到最新版本
- 整个过程无需人工干预

## 🔧 配置说明

### API 密钥配置
项目已配置真实 API 密钥：
- `DASHSCOPE_API_KEY`: 通义千问 API
- `TAVILY_API_KEY`: Tavily 搜索 API

### 环境变量
生产环境环境变量：
```bash
DATABASE_URL=postgresql://用户名:密码@主机:端口/数据库
DASHSCOPE_API_KEY=您的密钥
TAVILY_API_KEY=您的密钥
```

## 📁 文件结构
```
.github/
└── workflows/
    └── ci.yml          # 持续集成工作流（腾讯云托管自动触发）
src/                    # 源代码目录
tests/
├── test_basic.py       # 基础导入测试
├── test_real_api.py    # 真实 API 测试
├── test_models.py      # 数据库模型测试
└── conftest.py         # 测试配置
run_tests.sh            # 测试执行脚本
docker-compose.yml      # Docker编排配置
Dockerfile              # Docker构建配置（腾讯云托管使用）
```

## 🔗 Webhook配置

在GitHub仓库中：
- **Settings** → **Webhooks** → 查看腾讯云自动创建的Webhook
- Webhook地址：`https://cloud.tencent.com/webhook/xxx`
- 触发事件：`push`、`pull_request`
- 状态：✅ 活跃

## 🔍 监控和调试

### 查看 GitHub Actions 状态
1. 访问仓库的 "Actions" 标签页
2. 查看 CI 和 Deploy 工作流运行状态
3. 点击运行查看详细日志和覆盖率报告

### 常见问题

**Q: 测试运行失败怎么办？**
A: 检查：
- API 密钥是否正确
- 网络连接是否正常
- API 余额是否充足

**Q: 测试运行失败怎么办？**
A: 检查：
- API 密钥是否正确设置
- 网络连接是否正常
- API 余额是否充足
- Python 依赖是否完整安装

**Q: 部署失败怎么办？**
A: 检查：
- GitHub Actions CI是否通过（绿色勾勾）
- 腾讯云托管部署日志
- Webhook连接状态
- Dockerfile是否正确
- 环境变量配置

## 🛡️ 安全特性

1. **密钥安全**: 使用环境变量，不在代码中硬编码
2. **SSH 认证**: 安全的服务器部署
3. **权限控制**: 最小权限原则
4. **审计日志**: 完整的操作记录

---

项目已完成腾讯云托管深度集成的CI/CD配置，实现真正的全自动部署！每次git push后，代码会自动经过CI检查并安全部署到生产环境。