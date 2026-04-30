from __future__ import annotations

from fastapi.responses import HTMLResponse


def render_index_page() -> HTMLResponse:
    return HTMLResponse(
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>数据加工控制台</title>
  <style>
    :root {
      --bg: #eef7ff;
      --bg-soft: #f7fbff;
      --panel: rgba(255, 255, 255, 0.95);
      --panel-strong: #ffffff;
      --line: #d7e8f8;
      --line-strong: #bdd8ef;
      --text: #18344f;
      --muted: #65819d;
      --primary: #4b99e6;
      --primary-deep: #2d78c4;
      --primary-soft: #e9f4ff;
      --success-bg: #eef8ff;
      --success-text: #236ba8;
      --error-bg: #fff1f5;
      --error-text: #b13f5d;
      --shadow: 0 18px 40px rgba(79, 128, 176, 0.12);
      --shadow-soft: 0 12px 28px rgba(79, 128, 176, 0.08);
      --radius-xl: 28px;
      --radius-lg: 22px;
      --radius-md: 16px;
      --radius-sm: 12px;
      --page-width: 1380px;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(123, 188, 245, 0.24), transparent 34%),
        radial-gradient(circle at right center, rgba(205, 231, 255, 0.72), transparent 28%),
        linear-gradient(180deg, #fbfdff 0%, var(--bg) 100%);
    }

    .page {
      width: min(var(--page-width), calc(100vw - 28px));
      margin: 18px auto 32px;
    }

    .hero,
    .card {
      background: var(--panel);
      border: 1px solid rgba(190, 216, 240, 0.9);
      box-shadow: var(--shadow-soft);
      backdrop-filter: blur(10px);
    }

    .hero {
      overflow: hidden;
      position: relative;
      padding: 34px 36px;
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow);
    }

    .hero::after {
      content: "";
      position: absolute;
      right: -80px;
      bottom: -90px;
      width: 280px;
      height: 280px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(162, 212, 255, 0.42), transparent 68%);
      pointer-events: none;
    }

    .hero-grid,
    .content-grid,
    .task-grid {
      display: grid;
      gap: 22px;
    }

    .hero-grid {
      grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.65fr);
      align-items: start;
    }

    .content-grid {
      grid-template-columns: minmax(0, 1.12fr) minmax(360px, 0.88fr);
      margin-top: 22px;
    }

    .task-grid {
      grid-template-columns: minmax(0, 0.9fr) minmax(380px, 1.1fr);
      align-items: start;
    }

    .stack {
      display: grid;
      gap: 22px;
    }

    .hero-title {
      margin: 0;
      font-size: clamp(30px, 3.8vw, 44px);
      line-height: 1.08;
      letter-spacing: -0.04em;
    }

    .hero-desc {
      margin: 16px 0 0;
      max-width: 780px;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.78;
    }

    .hero-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }

    .badge {
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid rgba(130, 186, 236, 0.45);
      background: var(--primary-soft);
      color: var(--primary-deep);
      font-size: 13px;
      font-weight: 700;
    }

    .hero-side {
      padding: 22px;
      border-radius: 24px;
      background: rgba(247, 252, 255, 0.95);
      border: 1px solid rgba(185, 214, 238, 0.75);
      box-shadow: var(--shadow-soft);
    }

    .hero-side h2,
    .card-title {
      margin: 0;
    }

    .hero-side h2 {
      font-size: 17px;
      margin-bottom: 12px;
    }

    .hero-side ul {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.9;
      font-size: 13px;
    }

    .card {
      border-radius: var(--radius-lg);
      padding: 24px;
    }

    .card-title {
      font-size: 20px;
      letter-spacing: -0.02em;
    }

    .card-subtitle {
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.72;
    }

    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 18px;
    }

    .section-head.compact {
      margin-bottom: 14px;
    }

    .chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chip {
      padding: 7px 11px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #f5fbff;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .form-grid.single {
      grid-template-columns: 1fr;
    }

    .field {
      display: grid;
      gap: 7px;
    }

    .field.span-2 {
      grid-column: span 2;
    }

    .field label {
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
      letter-spacing: 0.04em;
    }

    input,
    select,
    textarea,
    button {
      width: 100%;
      font: inherit;
      border-radius: var(--radius-sm);
    }

    input,
    select,
    textarea {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.98);
      padding: 12px 14px;
      font-size: 14px;
      color: var(--text);
      outline: none;
      transition: border-color 0.18s ease, box-shadow 0.18s ease;
    }

    input:focus,
    select:focus,
    textarea:focus {
      border-color: #8ebeee;
      box-shadow: 0 0 0 4px rgba(116, 177, 235, 0.14);
    }

    textarea {
      min-height: 120px;
      resize: vertical;
      line-height: 1.65;
    }

    button {
      border: none;
      cursor: pointer;
      padding: 12px 16px;
      font-size: 14px;
      font-weight: 700;
      transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
    }

    button:hover {
      transform: translateY(-1px);
    }

    .primary-btn {
      background: linear-gradient(135deg, var(--primary), #66afef);
      color: #fff;
      box-shadow: 0 14px 28px rgba(76, 147, 219, 0.24);
    }

    .secondary-btn {
      background: #f6fbff;
      color: var(--primary-deep);
      border: 1px solid var(--line-strong);
      box-shadow: 0 10px 22px rgba(131, 172, 214, 0.12);
    }

    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .button-row button {
      flex: 1 1 180px;
    }

    .status {
      display: none;
      margin-top: 14px;
      padding: 12px 14px;
      border-radius: 14px;
      background: var(--success-bg);
      border: 1px solid rgba(170, 214, 245, 0.68);
      color: var(--success-text);
      font-size: 13px;
      line-height: 1.7;
    }

    .status.error {
      background: var(--error-bg);
      border-color: rgba(240, 181, 198, 0.8);
      color: var(--error-text);
    }

    .sub-card,
    .note,
    .template-item {
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 251, 255, 0.96));
      border: 1px solid var(--line);
    }

    .sub-card {
      padding: 20px;
    }

    .note {
      padding: 15px 16px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.78;
    }

    .template-list {
      display: grid;
      gap: 14px;
    }

    .template-item {
      padding: 16px;
    }

    .template-item strong {
      display: block;
      margin-bottom: 10px;
      font-size: 15px;
    }

    .template-meta {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.65;
    }

    .template-path {
      color: #4d6d90;
      word-break: break-all;
    }

    .result-box {
      min-height: 760px;
      padding: 18px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(18, 48, 80, 0.98), rgba(21, 57, 93, 0.98));
      color: #e9f4ff;
      border: 1px solid rgba(95, 137, 182, 0.35);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
      font-family: Consolas, "SFMono-Regular", monospace;
      font-size: 12px;
      line-height: 1.72;
      white-space: pre-wrap;
      word-break: break-word;
      overflow: auto;
    }

    .viewer-label {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.04em;
    }

    .tiny {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.7;
    }

    @media (max-width: 1180px) {
      .hero-grid,
      .content-grid,
      .task-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 760px) {
      .page {
        width: min(var(--page-width), calc(100vw - 16px));
        margin: 10px auto 22px;
      }

      .hero,
      .card {
        padding: 18px;
        border-radius: 20px;
      }

      .form-grid {
        grid-template-columns: 1fr;
      }

      .field.span-2 {
        grid-column: span 1;
      }

      .button-row button {
        flex-basis: 100%;
      }

      .result-box {
        min-height: 440px;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <div class="hero-grid">
        <div>
          <h1 class="hero-title">数据加工控制台</h1>
          <p class="hero-desc">
            这个页面覆盖当前 PoC 的完整主链路：维护知识库、上传真实输入文件、配置大模型、触发模板识别或图片 OCR，
            并查看规则、预览与加工结果。界面默认围绕“真实调用模型”和“不要兜底逻辑”来设计。
          </p>
          <div class="hero-badges">
            <span class="badge">知识包上传</span>
            <span class="badge">模板目录查看</span>
            <span class="badge">Excel / 图片上传</span>
            <span class="badge">模板识别</span>
            <span class="badge">税局截图 OCR</span>
            <span class="badge">结果预览</span>
          </div>
        </div>
        <aside class="hero-side">
          <h2>当前使用建议</h2>
          <ul>
            <li>新增场景时，优先使用“知识包上传”，上传两行 Excel 自动生成模板目录和规则。</li>
            <li>Excel 主链路依赖模板目录和真实大模型识别，不做本地硬编码猜测。</li>
            <li>图片主链路适用于税局网站截图，当前只支持一套固定映射逻辑。</li>
            <li>建议先保存模型配置，再上传文件并执行后续步骤。</li>
          </ul>
        </aside>
      </div>
    </section>

    <section class="content-grid">
      <div class="stack">
        <section class="card">
          <div class="section-head">
            <div>
              <h2 class="card-title">知识库管理</h2>
              <p class="card-subtitle">
                当前正式维护方式是上传两行 Excel：第 1 行是目标字段，第 2 行是模板列。系统会更新模板目录，并在对应场景目录下生成规则文件。
              </p>
            </div>
            <div class="chip-row">
              <span class="chip">主流程</span>
              <span class="chip">中文界面</span>
            </div>
          </div>

          <div class="stack">
            <div class="sub-card">
              <div class="section-head compact">
                <div>
                  <h3 class="card-title" style="font-size:18px;">上传场景知识包</h3>
                  <p class="card-subtitle">
                    上传一个规则规格 Excel，并可追加自然语言补充说明。系统会自动更新模板目录与规则文件。
                  </p>
                </div>
              </div>
              <form id="bundleForm">
                <div class="form-grid">
                  <div class="field">
                    <label>场景标识</label>
                    <input name="scene" placeholder="例如：rebate" required />
                  </div>
                  <div class="field">
                    <label>国家标识</label>
                    <input name="country" placeholder="例如：mx" required />
                  </div>
                  <div class="field span-2">
                    <label>知识包 Excel</label>
                    <input type="file" name="specFile" accept=".xlsx" required />
                  </div>
                  <div class="field span-2">
                    <label>自然语言补充说明</label>
                    <textarea name="instructionText" placeholder="例如：在 REBATE / MX 场景下，金额转数字，币种转大写，日期统一转日期格式。"></textarea>
                  </div>
                </div>
                <div class="button-row" style="margin-top: 14px;">
                  <button class="primary-btn" type="submit">上传知识包</button>
                </div>
              </form>
              <div id="bundleStatus" class="status"></div>
            </div>

            <div class="sub-card">
              <div class="section-head compact">
                <div>
                  <h3 class="card-title" style="font-size:18px;">模板 Excel 调试导入</h3>
                  <p class="card-subtitle">
                    这个入口仅用于调试和回归验证。正式流程仍然建议用“知识包上传”维护模板目录。
                  </p>
                </div>
                <div class="chip-row">
                  <span class="chip">调试入口</span>
                </div>
              </div>
              <form id="kbForm">
                <div class="form-grid">
                  <div class="field">
                    <label>模板编码</label>
                    <input name="templateCode" placeholder="例如：PAYMENT_INVOICE_V2" required />
                  </div>
                  <div class="field">
                    <label>模板名称</label>
                    <input name="templateName" placeholder="例如：Payment Invoice V2" required />
                  </div>
                  <div class="field span-2">
                    <label>模板 Excel</label>
                    <input type="file" name="file" accept=".xlsx" required />
                  </div>
                </div>
                <div class="button-row" style="margin-top: 14px;">
                  <button class="secondary-btn" type="submit">导入模板</button>
                </div>
              </form>
              <div id="kbStatus" class="status"></div>
            </div>
          </div>
        </section>

        <section class="card">
          <div class="section-head">
            <div>
              <h2 class="card-title">当前模板目录</h2>
              <p class="card-subtitle">
                这里展示模板目录中的场景、国家、字段数量和来源路径，方便你快速核对知识库状态。
              </p>
            </div>
            <div class="button-row" style="margin-top: 0;">
              <button class="secondary-btn" id="refreshTemplatesBtn" type="button">刷新模板列表</button>
            </div>
          </div>
          <div id="templateList" class="template-list"></div>
        </section>
      </div>

      <div class="stack">
        <section class="card">
          <div class="section-head compact">
            <div>
              <h2 class="card-title">模型配置</h2>
              <p class="card-subtitle">
                Excel 模板识别、规则草稿、图片 OCR 互相独立配置，方便对比不同模型效果。
              </p>
            </div>
          </div>

          <div class="stack">
            <form id="templateModelForm" class="sub-card">
              <div class="section-head compact">
                <div>
                  <h3 class="card-title" style="font-size:18px;">模板识别模型</h3>
                  <p class="card-subtitle">用于 Excel 输入的模板、场景、国家识别。</p>
                </div>
              </div>
              <div class="form-grid">
                <div class="field span-2">
                  <label>模型名称</label>
                  <input name="model" value="deepseek-v3.1" required />
                </div>
                <div class="field">
                  <label>提供方</label>
                  <input name="provider" value="openai_compatible_chat" required />
                </div>
                <div class="field">
                  <label>超时时间（秒）</label>
                  <input name="timeoutSeconds" type="number" value="30" required />
                </div>
                <div class="field span-2">
                  <label>接口地址</label>
                  <input name="endpointUrl" value="https://jeniya.cn/v1/chat/completions" required />
                </div>
                <div class="field span-2">
                  <label>API Key</label>
                  <input name="apiKey" type="password" placeholder="请输入模型密钥" />
                </div>
              </div>
              <div class="button-row" style="margin-top: 14px;">
                <button class="primary-btn" type="submit">保存模板识别配置</button>
              </div>
              <div id="templateModelStatus" class="status"></div>
            </form>

            <form id="ruleModelForm" class="sub-card">
              <div class="section-head compact">
                <div>
                  <h3 class="card-title" style="font-size:18px;">规则草稿模型</h3>
                  <p class="card-subtitle">用于 Excel 场景下的规则草稿补充与结构化输出。</p>
                </div>
              </div>
              <div class="form-grid">
                <div class="field span-2">
                  <label>模型名称</label>
                  <input name="model" value="deepseek-v3.1" required />
                </div>
                <div class="field">
                  <label>提供方</label>
                  <input name="provider" value="openai_compatible_chat" required />
                </div>
                <div class="field">
                  <label>超时时间（秒）</label>
                  <input name="timeoutSeconds" type="number" value="30" required />
                </div>
                <div class="field span-2">
                  <label>接口地址</label>
                  <input name="endpointUrl" value="https://jeniya.cn/v1/chat/completions" required />
                </div>
                <div class="field span-2">
                  <label>API Key</label>
                  <input name="apiKey" type="password" placeholder="请输入模型密钥" />
                </div>
              </div>
              <div class="button-row" style="margin-top: 14px;">
                <button class="secondary-btn" type="submit">保存规则草稿配置</button>
              </div>
              <div id="ruleModelStatus" class="status"></div>
            </form>

            <form id="imageModelForm" class="sub-card">
              <div class="section-head compact">
                <div>
                  <h3 class="card-title" style="font-size:18px;">图片 OCR 模型</h3>
                  <p class="card-subtitle">用于税局网站截图识别，目前按固定映射逻辑输出结构化结果。</p>
                </div>
              </div>
              <div class="form-grid">
                <div class="field span-2">
                  <label>模型名称</label>
                  <input name="model" value="qwen2.5-vl-72b-instruct" required />
                </div>
                <div class="field">
                  <label>提供方</label>
                  <input name="provider" value="openai_compatible_chat" required />
                </div>
                <div class="field">
                  <label>超时时间（秒）</label>
                  <input name="timeoutSeconds" type="number" value="60" required />
                </div>
                <div class="field span-2">
                  <label>接口地址</label>
                  <input name="endpointUrl" value="https://jeniya.cn/v1/chat/completions" required />
                </div>
                <div class="field span-2">
                  <label>API Key</label>
                  <input name="apiKey" type="password" placeholder="请输入模型密钥" />
                </div>
              </div>
              <div class="button-row" style="margin-top: 14px;">
                <button class="primary-btn" type="submit">保存图片 OCR 配置</button>
              </div>
              <div id="imageModelStatus" class="status"></div>
            </form>
          </div>
        </section>

        <section class="card">
          <div class="section-head compact">
            <div>
              <h2 class="card-title">上传真实输入文件</h2>
              <p class="card-subtitle">
                Excel 会进入模板识别链路，图片会进入税局截图 OCR 链路。上传后会自动创建任务并回填任务 ID。
              </p>
            </div>
          </div>
          <form id="taskForm">
            <div class="form-grid single">
              <div class="field">
                <label>输入类型</label>
                <select name="inputType" id="inputTypeSelect">
                  <option value="EXCEL">Excel</option>
                  <option value="IMAGE">图片</option>
                </select>
              </div>
              <div class="field">
                <label>输入文件</label>
                <input type="file" name="file" required />
              </div>
            </div>
            <div class="button-row" style="margin-top: 14px;">
              <button class="primary-btn" type="submit">创建任务</button>
            </div>
          </form>
          <div id="taskStatus" class="status"></div>
          <div class="note" style="margin-top: 16px;">
            当前图片链路适用于税局网站截图。上传图片后会真实调用多模态模型提取字段，再通过固定映射逻辑生成预览数据。
          </div>
        </section>
      </div>
    </section>

    <section class="card" style="margin-top: 22px;">
      <div class="section-head">
        <div>
          <h2 class="card-title">任务执行台</h2>
          <p class="card-subtitle">
            这里统一操作 Excel 与图片任务。Excel 侧重点是模板识别和规则草稿；图片侧重点是运行加工并直接查看预览结果。
          </p>
        </div>
        <div class="chip-row">
          <span class="chip">任务链路</span>
          <span class="chip">结果查看</span>
        </div>
      </div>

      <div class="task-grid">
        <div class="stack">
          <div class="field">
            <label>任务 ID</label>
            <input id="taskIdInput" placeholder="创建任务后会自动回填到这里" />
          </div>

          <div class="sub-card">
            <div class="section-head compact">
              <div>
                <h3 class="card-title" style="font-size:18px;">基础查看</h3>
                <p class="card-subtitle">先确认输入快照和模板目录候选是否符合预期。</p>
              </div>
            </div>
            <div class="button-row">
              <button class="secondary-btn" type="button" id="loadTaskBtn">查看任务摘要</button>
              <button class="secondary-btn" type="button" id="loadSnapshotBtn">查看输入快照</button>
              <button class="secondary-btn" type="button" id="loadTemplateCandidatesBtn">查看模板目录候选</button>
            </div>
          </div>

          <div class="sub-card">
            <div class="section-head compact">
              <div>
                <h3 class="card-title" style="font-size:18px;">Excel 识别与规则</h3>
                <p class="card-subtitle">这一组主要用于 Excel 输入任务。</p>
              </div>
            </div>
            <div class="button-row">
              <button class="primary-btn" type="button" id="identifyTemplateBtn">触发模板识别</button>
              <button class="secondary-btn" type="button" id="loadRuleCandidatesBtn">查看规则候选</button>
              <button class="primary-btn" type="button" id="draftRuleBtn">触发规则草稿</button>
            </div>
          </div>

          <div class="sub-card">
            <div class="section-head compact">
              <div>
                <h3 class="card-title" style="font-size:18px;">运行加工与预览</h3>
                <p class="card-subtitle">图片任务可直接使用；Excel 任务后续也会走这条链路。</p>
              </div>
            </div>
            <div class="button-row">
              <button class="primary-btn" type="button" id="runTaskBtn">运行数据加工</button>
              <button class="secondary-btn" type="button" id="loadPreviewSummaryBtn">查看预览摘要</button>
              <button class="secondary-btn" type="button" id="loadPreviewRowsBtn">查看预览分页</button>
            </div>
          </div>

          <div class="note">
            说明：<br />
            1. Excel 主链路是“上传 → 输入快照 → 模板识别 → 规则候选 / 草稿”。<br />
            2. 图片主链路是“上传 → qwen-vl 提取字段 → 固定规则加工 → 预览结果”。<br />
            3. 右侧结果面板始终显示最近一次接口响应的完整 JSON。
          </div>

          <div id="consoleStatus" class="status"></div>
        </div>

        <div>
          <div class="viewer-label">
            <span>结果查看区</span>
            <span class="tiny">默认展示最近一次调用结果</span>
          </div>
          <div id="resultViewer" class="result-box">等待操作...</div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const viewer = document.getElementById("resultViewer");

    function showStatus(id, text, isError = false) {
      const el = document.getElementById(id);
      el.style.display = "block";
      el.className = isError ? "status error" : "status";
      el.textContent = text;
    }

    function showResult(title, data) {
      viewer.textContent = title + "\\n\\n" + JSON.stringify(data, null, 2);
    }

    async function parseResponse(response) {
      const json = await response.json();
      if (!response.ok) {
        throw new Error(json.message || "请求失败");
      }
      return json.data;
    }

    async function loadTemplates() {
      const response = await fetch("/api/v1/kb/templates");
      const data = await parseResponse(response);
      const list = document.getElementById("templateList");
      if (!data.length) {
        list.innerHTML = '<div class="template-item"><strong>当前没有模板</strong><div class="template-meta">请先上传知识包或导入调试模板。</div></div>';
        return;
      }

      list.innerHTML = data.map(item => `
        <div class="template-item">
          <strong>${item.templateName}</strong>
          <div class="template-meta">
            <div>模板编码：${item.templateCode}</div>
            <div>场景 / 国家：${item.scene || "-"} / ${item.country || "-"}</div>
            <div>来源类型：${item.sourceType}</div>
            <div>字段数 / 别名数：${item.fieldCount} / ${item.headerAliasCount}</div>
            <div class="template-path">路径：${item.templatePath || "-"}</div>
          </div>
        </div>
      `).join("");
    }

    async function saveConfig(formId, url, statusId, label) {
      const form = new FormData(document.getElementById(formId));
      const body = Object.fromEntries(form.entries());
      body.timeoutSeconds = Number(body.timeoutSeconds || 30);
      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await parseResponse(response);
        showStatus(statusId, `${label}已保存：${data.provider} / ${data.model}`);
        showResult(label + "保存结果", data);
      } catch (error) {
        showStatus(statusId, error.message, true);
      }
    }

    async function runTaskAction(urlBuilder, title, method = "GET") {
      const taskId = document.getElementById("taskIdInput").value.trim();
      if (!taskId) {
        showStatus("consoleStatus", "请先输入任务 ID。", true);
        return;
      }

      try {
        const response = await fetch(urlBuilder(taskId), { method });
        const data = await parseResponse(response);
        showStatus("consoleStatus", `${title}执行成功。`);
        showResult(title, data);
      } catch (error) {
        showStatus("consoleStatus", error.message, true);
      }
    }

    document.getElementById("refreshTemplatesBtn").addEventListener("click", async () => {
      try {
        await loadTemplates();
      } catch (error) {
        showStatus("kbStatus", error.message, true);
      }
    });

    document.getElementById("kbForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.target);
      try {
        const response = await fetch("/api/v1/kb/templates/import", { method: "POST", body: form });
        const data = await parseResponse(response);
        showStatus("kbStatus", `模板 ${data.templateName} 导入成功，共识别 ${data.fieldCount} 个字段。`);
        await loadTemplates();
        showResult("模板导入结果", data);
      } catch (error) {
        showStatus("kbStatus", error.message, true);
      }
    });

    document.getElementById("bundleForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.target);
      try {
        const response = await fetch("/api/v1/kb/templates/bundle", { method: "POST", body: form });
        const data = await parseResponse(response);
        showStatus("bundleStatus", `知识包已写入 ${data.scene}/${data.country}，并自动生成 ${data.mappingCount} 条基础映射。`);
        await loadTemplates();
        showResult("知识包上传结果", data);
      } catch (error) {
        showStatus("bundleStatus", error.message, true);
      }
    });

    document.getElementById("taskForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.target);
      try {
        const response = await fetch("/api/v1/tasks/upload", { method: "POST", body: form });
        const data = await parseResponse(response);
        document.getElementById("taskIdInput").value = data.task.taskId;
        showStatus("taskStatus", `任务创建成功，任务 ID：${data.task.taskId}`);
        showResult("任务上传结果", data);
      } catch (error) {
        showStatus("taskStatus", error.message, true);
      }
    });

    document.getElementById("templateModelForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      await saveConfig(
        "templateModelForm",
        "/api/v1/agents/template-identification/config",
        "templateModelStatus",
        "模板识别配置"
      );
    });

    document.getElementById("ruleModelForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      await saveConfig(
        "ruleModelForm",
        "/api/v1/agents/rule-draft/config",
        "ruleModelStatus",
        "规则草稿配置"
      );
    });

    document.getElementById("imageModelForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      await saveConfig(
        "imageModelForm",
        "/api/v1/agents/image-ocr/config",
        "imageModelStatus",
        "图片 OCR 配置"
      );
    });

    document.getElementById("loadTaskBtn").addEventListener("click", async () => {
      await runTaskAction(taskId => `/api/v1/tasks/${taskId}`, "GET 任务摘要");
    });

    document.getElementById("loadSnapshotBtn").addEventListener("click", async () => {
      await runTaskAction(taskId => `/api/v1/tasks/${taskId}/input-snapshot`, "GET 输入快照");
    });

    document.getElementById("loadTemplateCandidatesBtn").addEventListener("click", async () => {
      await runTaskAction(taskId => `/api/v1/tasks/${taskId}/template-candidates`, "GET 模板目录候选");
    });

    document.getElementById("identifyTemplateBtn").addEventListener("click", async () => {
      await runTaskAction(
        taskId => `/api/v1/agents/template-identification/tasks/${taskId}`,
        "POST 模板识别",
        "POST"
      );
    });

    document.getElementById("loadRuleCandidatesBtn").addEventListener("click", async () => {
      await runTaskAction(taskId => `/api/v1/tasks/${taskId}/rule-candidates`, "GET 规则候选");
    });

    document.getElementById("draftRuleBtn").addEventListener("click", async () => {
      await runTaskAction(
        taskId => `/api/v1/agents/rule-draft/tasks/${taskId}`,
        "POST 规则草稿",
        "POST"
      );
    });

    document.getElementById("runTaskBtn").addEventListener("click", async () => {
      await runTaskAction(
        taskId => `/api/v1/tasks/${taskId}/run`,
        "POST 运行数据加工",
        "POST"
      );
    });

    document.getElementById("loadPreviewSummaryBtn").addEventListener("click", async () => {
      await runTaskAction(taskId => `/api/v1/tasks/${taskId}/preview-summary`, "GET 预览摘要");
    });

    document.getElementById("loadPreviewRowsBtn").addEventListener("click", async () => {
      await runTaskAction(taskId => `/api/v1/tasks/${taskId}/preview-rows?page=1&pageSize=20`, "GET 预览分页");
    });

    loadTemplates().catch(() => {});
  </script>
</body>
</html>
        """
    )
