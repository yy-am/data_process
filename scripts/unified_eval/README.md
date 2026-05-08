# 统一评测包

这个目录是统一评测入口，目标是让另一台电脑也能快速跑起来。

## 目录内容

- `run_unified_eval.ps1`
  运行统一评测
- `run_unified_eval.cmd`
  Windows 命令行入口
- `start_local_poc.ps1`
  启动本地 PoC 服务
- `start_local_poc.cmd`
  Windows 命令行入口
- `prepare_git_commit.ps1`
  提交前将主配置切回安全 example 配置
- `prepare_git_commit.cmd`
  Windows 命令行入口
- `unified_model_eval_config.json`
  可提交的安全主配置
- `unified_model_eval_config.local.json`
  本地开发配置，可写死明文 `apiKey`
- `unified_model_eval_config.example.json`
  配置样例
- `eval_cases/`
  三类测试用例和 `manifest`
- `reports/`
  统一评测输出目录

## 配置约定

- 日常本地开发：
  优先使用 `unified_model_eval_config.local.json`
- 提交到 Git：
  保持 `unified_model_eval_config.json` 为安全配置

运行脚本会优先读取：

1. `unified_model_eval_config.local.json`
2. 若不存在，再读取 `unified_model_eval_config.json`

### 模型兼容开关

- 对于兼容 OpenAI `response_format` 的模型，保持：
  `includeResponseFormat: true`
- 如果供应商文档里的请求体没有 `response_format`，或者调用时出现协议不兼容报错，可改成：
  `includeResponseFormat: false`
- 如果供应商要求的 `Authorization` 头不是 `Bearer + apiKey`，可直接配置：
  `authorizationHeader` 或 `authorizationHeaderEnv`

示例：

```json
{
  "label": "glm-5.1",
  "provider": "openai_compatible_chat",
  "endpointUrl": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
  "modelName": "glm-5.1",
  "authorizationHeader": "你的完整 Authorization 头值",
  "includeResponseFormat": false,
  "timeoutSeconds": 120,
  "enabled": true
}
```

说明：

- `apiKey` / `apiKeyEnv`
  适用于接口要求 `Authorization: Bearer <apiKey>` 的场景
- `authorizationHeader` / `authorizationHeaderEnv`
  适用于接口要求自定义 `Authorization` 值的场景
- 如果同时配置了两者，优先使用 `authorizationHeader`

## 首次运行检查

另一台电脑首次运行前，请先确认：

1. 仓库根目录下存在 `.venv\Scripts\python.exe`
2. 如果没有 `.venv`，系统里至少安装了 `python` 或 `py`
3. 数据加工模板识别 suite 依赖本地 `127.0.0.1:8000`

根目录的 `python.cmd` 现在会按下面顺序自动找 Python：

1. 仓库内 `.venv\Scripts\python.exe`
2. `PATH` 里的 `python`
3. `PATH` 里的 `py`

## 快速运行

### 1. 启动本地 PoC

```powershell
cd D:\你的路径\data_process\scripts\unified_eval
.\start_local_poc.ps1
```

### 2. 运行统一评测

本地如果已写好 `unified_model_eval_config.local.json`，无需再设置环境变量。

```powershell
.\run_unified_eval.ps1
```

### 3. 查看报告

报告会输出到当前目录下的 `reports/`：

- `unified_model_eval_report_*.json`
- `unified_model_eval_report_*.md`

## 提交前处理

如果你想在提交前显式把主配置切回安全配置，执行：

```powershell
.\prepare_git_commit.ps1
```

## 说明

- 当前统一 runner 代码仍复用仓库根目录的 `scripts/run_unified_model_eval.py`
- 这个目录负责聚合启动脚本、配置、测试用例和报告输出
- 迁移到另一台电脑时，只要保留整个仓库结构，这个目录即可直接复用
