# Unified Model Evaluation Report

- Generated At: 2026-05-08T02-34-21Z
- Models: 1
- Suites: 3

## Summary By Model

| Model | Overall Avg | Overall Pass Rate | Data Processing | Job Creation | Diff Analysis |
| --- | ---: | ---: | ---: | ---: | ---: |
| deepseek-v3.1 | 83.96 | 0.5957 | 100.0 | 77.83 | 80.28 |

## Data Processing Template Identification

| Case ID | Title | deepseek-v3.1 |
| --- | --- | --- |
| DP001 | Payment invoice standard US clean headers | 100 (passed) |
| DP002 | Payment invoice US variant headers | 100 (passed) |
| DP003 | Payment invoice US similar headers v2 | 100 (passed) |
| DP004 | Customs declaration CN clean headers | 100 (passed) |
| DP005 | Customs declaration CN similar headers v2 | 100 (passed) |
| DP006 | Vendor settlement EU variant headers | 100 (passed) |
| DP007 | Vendor settlement EU similar headers v2 | 100 (passed) |
| DP008 | Order fulfillment JP 22-column variant | 100 (passed) |
| DP009 | Rebate MX similar headers v2 | 100 (passed) |
| DP010 | Channel rebate MX 22 unrelated headers | 100 (passed) |
| DP011 | Ambiguous trade document | 100 (passed) |

### Data Processing Template Identification Notes

#### deepseek-v3.1

| Case ID | Score | Outcome | Notes |
| --- | ---: | --- | --- |
| DP001 | 100 | passed | Template, scene, and country matched expected values. |
| DP002 | 100 | passed | Template, scene, and country matched expected values. |
| DP003 | 100 | passed | Template, scene, and country matched expected values. |
| DP004 | 100 | passed | Template, scene, and country matched expected values. |
| DP005 | 100 | passed | Template, scene, and country matched expected values. |
| DP006 | 100 | passed | Template, scene, and country matched expected values. |
| DP007 | 100 | passed | Template, scene, and country matched expected values. |
| DP008 | 100 | passed | Template, scene, and country matched expected values. |
| DP009 | 100 | passed | Template, scene, and country matched expected values. |
| DP010 | 100 | passed | Template, scene, and country matched expected values. |
| DP011 | 100 | passed | Ambiguous case correctly stayed unresolved. |


## Reconciliation Job Creation From Existing Scene

| Case ID | Title | deepseek-v3.1 |
| --- | --- | --- |
| JC001 | 电商订单与支付流水日对账 | 65 (needs_review) |
| JC002 | ERP 应收与总账月末对账 | 70 (needs_review) |
| JC003 | 银行回单与 ERP 收款核销 | 100 (passed) |
| JC004 | 退款单与支付退款流水 | 62 (needs_review) |
| JC005 | 仓储出库与订单履约 | 90 (passed) |
| JC006 | 跨币种结算对账 | 70 (needs_review) |
| JC007 | 海关申报与 ERP 报关单 | 67 (needs_review) |
| JC008 | 税局发票与 ERP 销项 | 70 (needs_review) |
| JC009 | POS 与总账汇总核对 | 73 (needs_review) |
| JC010 | 模糊来源系统 | 85 (passed) |
| JC011 | 缺少匹配键 | 100 (passed) |
| JC012 | 自然语言同义表达 | 65 (needs_review) |
| JC013 | 中英文混输 | 100 (passed) |
| JC014 | 包含过滤条件 | 62 (needs_review) |
| JC015 | 日期容差窗口 | 75 (needs_review) |
| JC016 | 多键匹配和费用比较 | 70 (needs_review) |
| JC017 | 冲突指令 | 97 (passed) |
| JC018 | 明确要求不要创建 | 80 (passed) |

### Reconciliation Job Creation From Existing Scene Notes

#### deepseek-v3.1

| Case ID | Score | Outcome | Notes |
| --- | ---: | --- | --- |
| JC001 | 65 | needs_review | - |
| JC002 | 70 | needs_review | - |
| JC003 | 100 | passed | - |
| JC004 | 62 | needs_review | - |
| JC005 | 90 | passed | - |
| JC006 | 70 | needs_review | - |
| JC007 | 67 | needs_review | - |
| JC008 | 70 | needs_review | - |
| JC009 | 73 | needs_review | - |
| JC010 | 85 | passed | - |
| JC011 | 100 | passed | - |
| JC012 | 65 | needs_review | - |
| JC013 | 100 | passed | - |
| JC014 | 62 | needs_review | - |
| JC015 | 75 | needs_review | - |
| JC016 | 70 | needs_review | - |
| JC017 | 97 | passed | - |
| JC018 | 80 | passed | - |


## Diff Analysis From Result And SOP

| Case ID | Title | deepseek-v3.1 |
| --- | --- | --- |
| DA001 | 源端缺失 | 100 (passed) |
| DA002 | 重复流水 | 100 (passed) |
| DA003 | 主键错位 | 73 (needs_review) |
| DA004 | 四舍五入误差 | 88 (passed) |
| DA005 | 税率口径不一致 | 100 (passed) |
| DA006 | 状态时点差 | 85 (passed) |
| DA007 | 人工调账 | 80 (passed) |
| DA008 | 字段映射错误 | 85 (passed) |
| DA009 | 过滤范围不一致 | 70 (needs_review) |
| DA010 | 退款冲抵 | 70 (needs_review) |
| DA011 | 跨期截断 | 83 (passed) |
| DA012 | 上游程序缺陷 | 78 (needs_review) |
| DA013 | 证据不足 | 83 (passed) |
| DA014 | 数量一致但状态不一致 | 45 (needs_review) |
| DA015 | 发票主键口径混用 | 70 (needs_review) |
| DA016 | 多次导入导致重复 | 65 (needs_review) |
| DA017 | 站点范围与状态过滤同时不一致 | 70 (needs_review) |
| DA018 | 币种一致但汇率表版本不同 | 100 (passed) |

### Diff Analysis From Result And SOP Notes

#### deepseek-v3.1

| Case ID | Score | Outcome | Notes |
| --- | ---: | --- | --- |
| DA001 | 100 | passed | - |
| DA002 | 100 | passed | - |
| DA003 | 73 | needs_review | - |
| DA004 | 88 | passed | - |
| DA005 | 100 | passed | - |
| DA006 | 85 | passed | - |
| DA007 | 80 | passed | - |
| DA008 | 85 | passed | - |
| DA009 | 70 | needs_review | - |
| DA010 | 70 | needs_review | - |
| DA011 | 83 | passed | - |
| DA012 | 78 | needs_review | - |
| DA013 | 83 | passed | - |
| DA014 | 45 | needs_review | - |
| DA015 | 70 | needs_review | - |
| DA016 | 65 | needs_review | - |
| DA017 | 70 | needs_review | - |
| DA018 | 100 | passed | - |
