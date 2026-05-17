# GitHub 密钥配置指南

本指南详细介绍如何为腾讯云自动部署配置 GitHub Secrets。

## 访问 GitHub Secrets

1. 进入您的 GitHub 仓库
2. 点击 **Settings**（设置）选项卡
3. 在左侧边栏中，点击 **Secrets and variables** → **Actions**
4. 点击 **New repository secret** 添加每个必需的密钥

## 必需的密钥

### 服务器访问密钥

#### `TENCENT_SERVER_HOST`
- **描述**：腾讯云服务器的 IP 地址或域名
- **示例**：`123.456.789.012` 或 `your-domain.com`
- **获取方式**：从腾讯云控制台获取服务器的公网 IP 地址

#### `TENCENT_SERVER_USER`
- **描述**：连接服务器的 SSH 用户名
- **示例**：`ubuntu`、`root` 或您的自定义用户名
- **获取方式**：您用于 SSH 登录服务器的用户名

#### `TENCENT_SERVER_SSH_KEY`
- **描述**：服务器认证的 SSH 私钥
- **示例**：
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAA...
...
-----END OPENSSH PRIVATE KEY-----
  ```
- **生成方式**：
  ```bash
  # 在本地机器上生成新的 SSH 密钥对
  ssh-keygen -t ed25519 -C "github-actions@your-repo" -f github-actions-key

  # 将公钥添加到服务器的 authorized_keys
  ssh-copy-id -i github-actions-key.pub user@your-server

  # 复制私钥内容用于 GitHub Secrets
  cat github-actions-key
  ```

#### `TENCENT_PROJECT_PATH`（可选）
- **描述**：服务器上项目所在路径
- **示例**：`/app/ai-paper-writer`
- **默认值**：如果未设置，部署将使用 `/app/ai-paper-writer`

#### `TENCENT_SERVER_PORT`（可选）
- **描述**：SSH 端口号
- **示例**：`22`
- **默认值**：如果未设置，将使用端口 22

#### `APP_PORT`（可选）
- **描述**：FastAPI 应用程序运行的端口
- **示例**：`8000`
- **默认值**：如果未设置，健康检查将使用端口 8000

### API 密钥和服务凭据

#### `DASHSCOPE_API_KEY`
- **描述**：DashScope LLM 服务 API 密钥
- **获取方式**：
  1. 访问 [DashScope 控制台](https://dashscope.console.aliyun.com/)
  2. 创建或复制现有 API 密钥
  3. 粘贴密钥值

#### `TAVILY_API_KEY`
- **描述**：Tavily 搜索服务 API 密钥
- **获取方式**：
  1. 在 [Tavily](https://tavily.com/) 注册账号
  2. 进入账户设置
  3. 复制您的 API 密钥

#### `DATABASE_URL`
- **描述**：PostgreSQL 数据库连接 URL
- **格式**：`postgresql://用户名:密码@主机:端口/数据库名`
- **示例**：`postgresql://app:securepassword@localhost:5432/ai_paper_writer`
- **构建方式**：
  - `用户名`：PostgreSQL 用户名
  - `密码`：PostgreSQL 密码
  - `主机`：数据库服务器主机（同服务器通常为 `localhost`）
  - `端口`：数据库端口（通常为 `5432`）
  - `数据库名`：数据库名称

## 分步设置流程

### 1. 生成 SSH 密钥对

```bash
# 为 GitHub Actions 生成专用的 SSH 密钥对
ssh-keygen -t ed25519 -C "github-actions@ai-paper-writer" -f github-actions-deploy-key

# 这将创建两个文件：
# - github-actions-deploy-key（私钥 - 用于 GitHub Secrets）
# - github-actions-deploy-key.pub（公钥 - 用于服务器）
```

### 2. 配置服务器 SSH 访问

```bash
# 将公钥复制到腾讯云服务器
ssh-copy-id -i github-actions-deploy-key.pub your-user@your-server-ip

# 测试连接
test -f github-actions-deploy-key && ssh -i github-actions-deploy-key your-user@your-server-ip
```

### 3. 添加密钥到 GitHub

1. **导航到 GitHub Secrets**：
   - 仓库 → Settings → Secrets and variables → Actions

2. **添加每个密钥**：
   - 点击 "New repository secret"
   - 准确输入上述显示的密钥名称
   - 粘贴密钥值
   - 点击 "Add secret"

3. **验证所有密钥已添加**：
   - `TENCENT_SERVER_HOST`
   - `TENCENT_SERVER_USER`
   - `TENCENT_SERVER_SSH_KEY`
   - `TENCENT_PROJECT_PATH`（可选）
   - `TENCENT_SERVER_PORT`（可选）
   - `APP_PORT`（可选）
   - `DASHSCOPE_API_KEY`
   - `TAVILY_API_KEY`
   - `DATABASE_URL`

### 4. 测试配置

创建测试标签来验证部署是否正常工作：

```bash
# 创建测试标签
git tag v0.0.1-test
git push origin v0.0.1-test
```

监控 GitHub Actions 工作流确保所有步骤成功完成。

## 安全最佳实践

### SSH 密钥管理

1. **使用专用密钥**：仅为部署创建单独的 SSH 密钥
2. **限制权限**：部署密钥应具有最低必要权限
3. **定期轮换**：每 6-12 个月轮换 SSH 密钥
4. **需要时撤销**：如果密钥泄露立即删除

### API 密钥安全

1. **环境特定密钥**：为开发和生产使用不同的密钥
2. **密钥轮换**：定期轮换 API 密钥
3. **访问监控**：监控 API 使用情况的异常模式
4. **最小权限**：只授予 API 密钥必要权限

### GitHub Secrets 安全

1. **绝不提交密钥**：确保密钥永远不会提交到版本控制
2. **审计访问**：定期审查谁可以访问仓库密钥
3. **使用环境特定密钥**：考虑使用 GitHub Environments 管理不同部署目标

## 故障排除

### 常见问题

#### SSH 连接失败
- **错误**：`ssh: connect to host ... port 22: Connection refused`
- **解决方案**：
  - 验证服务器 IP 地址正确
  - 检查服务器上 SSH 服务是否运行
  - 验证防火墙允许端口 22

#### 认证失败
- **错误**：`Permission denied (publickey)`
- **解决方案**：
  - 验证 GitHub Secrets 中的 SSH 密钥格式正确
  - 检查公钥是否正确添加到服务器的 `authorized_keys`
  - 确保 SSH 密钥具有正确权限（私钥 `chmod 600`）

#### API 密钥问题
- **错误**：API 调用因认证错误失败
- **解决方案**：
  - 验证 API 密钥正确复制且无额外空格
  - 检查 API 密钥是否有足够配额/权限
  - 验证 API 端点可从服务器访问

### 本地测试密钥

在设置 GitHub Secrets 前可以本地测试配置：

```bash
# 测试 SSH 连接
ssh -i /path/to/private/key $TENCENT_SERVER_USER@$TENCENT_SERVER_HOST

# 测试 API 密钥（如果适用）
curl -H "Authorization: Bearer $DASHSCOPE_API_KEY" https://dashscope.aliyuncs.com/api/health
```

## 高级配置

### 使用 GitHub Environments

为了更好的安全性，考虑使用 GitHub Environments：

1. 进入 **Settings** → **Environments**
2. 创建如 `production`、`staging` 的环境
3. 添加环境特定的密钥
4. 更新工作流使用特定环境

### 多服务器部署

要部署到多个服务器，您可以：

1. 为每个服务器创建单独的密钥（如 `PROD_SERVER_HOST`、`STAGING_SERVER_HOST`）
2. 在工作流中创建单独的部署任务
3. 为不同环境使用不同的触发器

## 支持

如果遇到问题：

1. 检查 GitHub Actions 日志获取详细错误信息
2. 验证所有密钥格式正确
3. 首先手动测试 SSH 连接性
4. 查看服务器日志了解认证问题

---

*本指南是腾讯云自动部署 CICD 改进实施的一部分。*