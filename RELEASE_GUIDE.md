# PyPI 发布指南

## 前置要求

1. PyPI 账号：https://pypi.org/account/register/
2. GitHub 账号（已配置）
3. API Token（见下文）

## 步骤 1：创建 API Token

### PyPI
1. 访问 https://pypi.org/manage/account/
2. 点击 "Add API token"
3. 创建token，Scope选择 "Entire account"
4. 复制token

### Test PyPI（可选，用于测试）
1. 访问 https://test.pypi.org/manage/account/
2. 同上创建token

## 步骤 2：添加到 GitHub Secrets

1. 访问 https://github.com/zcyisiee/ieeU/settings/secrets/actions
2. 添加以下Secrets：
   - `PYPI_API_TOKEN`: 你的PyPI token
   - `TEST_PYPI_API_TOKEN`: 你的Test PyPI token（可选）

## 步骤 3：发布到 Test PyPI（测试）

### 方式一：手动触发 Workflow
1. 访问 https://github.com/zcyisiee/ieeU/actions/workflows/publish.yml
2. 点击 "Run workflow"
3. 选择 "test-publish" 分支
4. 点击 "Run workflow"

### 方式二：本地测试
```bash
# 安装twine
pip install twine

# 上传到Test PyPI
twine upload --repository testpypi dist/*
```

### 验证安装
```bash
pip install --index-url https://test.pypi.org/simple/ ieeU
```

## 步骤 4：发布到 PyPI

### 方式一：GitHub Release（推荐）
1. 访问 https://github.com/zcyisiee/ieeU/releases/new
2. Tag version: `v1.0.0`
3. Release title: `Release v1.0.0`
4. 点击 "Publish release"
5. GitHub Actions 将自动构建并发布

### 方式二：手动发布
```bash
# 上传到PyPI
twine upload dist/*
```

### 验证安装
```bash
pip install ieeU
```

## 步骤 5：验证发布

```bash
# 检查PyPI页面
open https://pypi.org/project/ieeU/

# 验证安装
pip show ieeU

# 测试命令
ieeU --version
```

## 常见问题

### Q: 上传失败 "File already exists"
A: 更新版本号后重试

### Q: Token权限不足
A: 确保选择 "Entire account" scope

### Q: 构建失败
A: 本地运行 `python -m build` 调试

## 版本号规则

使用语义化版本：主版本.次版本.修订号

- 主版本：不兼容的API更改
- 次版本：向后兼容的新功能
- 修订号：向后兼容的bug修复

## 下次发布

```bash
# 更新版本号在 pyproject.toml
# 创建新标签
git tag v1.0.1
git push origin v1.0.1
```
