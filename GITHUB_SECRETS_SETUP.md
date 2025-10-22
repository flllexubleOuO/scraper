# 🔐 GitHub Secrets 配置指南

## 问题
GitHub Actions 报错：`Error: missing server host`

**原因**：GitHub仓库中缺少必需的Secrets配置。

## ✅ 解决方案：添加GitHub Secrets

### 步骤1: 打开GitHub仓库设置

1. 访问你的GitHub仓库：
   ```
   https://github.com/flllexubleOuO/scraper
   ```

2. 点击仓库顶部的 **Settings** (设置) 标签

3. 在左侧菜单中找到：
   - **Security** 部分
   - 点击 **Secrets and variables**
   - 点击 **Actions**

4. 你会看到一个页面，标题为 "Actions secrets and variables"

### 步骤2: 添加第一个Secret - EC2_HOST

1. 点击绿色按钮 **New repository secret**

2. 填写信息：
   - **Name**: `EC2_HOST`
   - **Secret**: 输入你的EC2公网IP地址
   
   **如何获取EC2公网IP**：
   ```bash
   # 方法1: 在EC2上运行
   curl http://169.254.169.254/latest/meta-data/public-ipv4
   
   # 方法2: AWS控制台
   # EC2 Dashboard → Instances → 选择你的实例 → 查看 "Public IPv4 address"
   ```
   
   **示例**：
   ```
   54.123.45.67
   ```
   
   ⚠️ **注意**：只填写IP地址，不要包含 `http://` 或端口号

3. 点击 **Add secret** (添加密钥)

### 步骤3: 添加第二个Secret - EC2_USER

1. 再次点击 **New repository secret**

2. 填写信息：
   - **Name**: `EC2_USER`
   - **Secret**: 输入EC2用户名
   
   **根据你的系统选择**：
   - Amazon Linux 2023/2: `ec2-user`
   - Ubuntu: `ubuntu`
   - Red Hat: `ec2-user`
   - Debian: `admin`
   
   **如果不确定，在EC2上运行**：
   ```bash
   whoami
   ```

3. 点击 **Add secret**

### 步骤4: 添加第三个Secret - EC2_SSH_KEY

这是最重要的一步！

1. 点击 **New repository secret**

2. 填写信息：
   - **Name**: `EC2_SSH_KEY`
   - **Secret**: 你的SSH私钥的**完整内容**

**如何获取SSH私钥内容**：

```bash
# 在你的Mac上运行（替换成你的实际.pem文件路径）
cat /path/to/your-ec2-key.pem

# 例如：
cat ~/Downloads/my-ec2-key.pem
# 或
cat ~/.ssh/my-ec2-key.pem
```

**复制完整内容**，包括：
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...（很多行）...
...（很多行）...
-----END RSA PRIVATE KEY-----
```

⚠️ **重要提示**：
- 必须包含开头的 `-----BEGIN RSA PRIVATE KEY-----`
- 必须包含结尾的 `-----END RSA PRIVATE KEY-----`
- 中间所有行都要复制
- 不要有多余的空格或空行

3. 粘贴到 **Secret** 框中

4. 点击 **Add secret**

### 步骤5: 验证配置

配置完成后，你应该能看到3个Secrets：

```
EC2_HOST          Updated X seconds ago
EC2_USER          Updated X seconds ago  
EC2_SSH_KEY       Updated X seconds ago
```

⚠️ **注意**：Secret的值一旦保存就无法再查看，只能更新。

### 步骤6: 测试GitHub Actions

1. 返回仓库首页

2. 点击顶部的 **Actions** 标签

3. 你会看到之前失败的workflow

4. 有两种方式重新运行：

   **方法1: 重新触发已失败的workflow**
   - 点击失败的 "deploy" workflow
   - 点击右上角的 **Re-run all jobs** (重新运行所有任务)

   **方法2: 手动触发新的workflow**
   - 点击左侧的 "Deploy to EC2"
   - 点击右侧的 **Run workflow** 按钮
   - 确认分支是 `main`
   - 点击绿色的 **Run workflow** 按钮

5. 等待运行完成（约30-60秒）

6. 查看运行日志，确认没有错误

## 🔍 常见问题排查

### 问题1: 仍然显示 "missing server host"

**可能原因**：
- Secret名称拼写错误（必须是 `EC2_HOST`，大小写敏感）
- Secret值中包含空格或换行符

**解决方案**：
1. 删除现有的Secret
2. 重新创建，确保名称完全匹配
3. 确保值不包含多余的空格

### 问题2: "Permission denied (publickey)"

**可能原因**：
- `EC2_SSH_KEY` 的内容不完整
- 使用了错误的密钥文件

**解决方案**：
1. 确认密钥文件是否正确：
   ```bash
   # 在本地测试
   ssh -i your-key.pem ec2-user@<EC2_IP>
   ```
2. 如果本地能连接，重新复制密钥内容到GitHub Secret
3. 确保复制了完整内容（包括头尾）

### 问题3: "Host key verification failed"

**可能原因**：
- 第一次连接EC2，SSH需要确认指纹

**解决方案**：
在GitHub Actions中添加 `StrictHostKeyChecking=no`（已在我们的配置中处理）

或者，手动SSH到EC2一次，接受指纹：
```bash
ssh -i your-key.pem ec2-user@<EC2_IP>
# 输入 yes
```

### 问题4: "Connection timed out"

**可能原因**：
- EC2安全组没有开放SSH端口(22)
- EC2_HOST IP地址错误

**解决方案**：
1. 检查EC2安全组入站规则：
   - Type: SSH
   - Port: 22
   - Source: 0.0.0.0/0 (或 GitHub Actions IP范围)

2. 验证IP地址：
   ```bash
   ping <EC2_IP>
   ```

## 📝 配置清单

完成后，确认以下项目：

- [ ] GitHub Secrets已添加：
  - [ ] `EC2_HOST` - EC2公网IP
  - [ ] `EC2_USER` - SSH用户名
  - [ ] `EC2_SSH_KEY` - SSH私钥完整内容

- [ ] EC2安全组配置：
  - [ ] 端口22 (SSH) - 允许入站
  - [ ] 端口8080 (Web App) - 允许入站

- [ ] EC2上已准备：
  - [ ] 代码已克隆到 `~/scraper`
  - [ ] 依赖已安装
  - [ ] `.env` 文件已创建（包含OPENAI_API_KEY）

## 🎉 完成！

配置完成后，每次你推送代码到 `main` 分支，GitHub Actions都会自动：
1. 连接到EC2
2. 拉取最新代码
3. 检查并安装Chrome（如果需要）
4. 更新依赖（如果需要）
5. 重启服务

---

## 💡 安全提示

1. **永远不要**在代码中直接写入密钥
2. **定期轮换** SSH密钥
3. **限制安全组**规则，只允许必要的IP访问
4. **启用MFA**保护GitHub账户
5. 如果密钥泄露，**立即**在AWS中删除并创建新密钥对

---

需要帮助？参考：
- [GitHub Actions文档](https://docs.github.com/en/actions)
- [appleboy/ssh-action](https://github.com/appleboy/ssh-action)

