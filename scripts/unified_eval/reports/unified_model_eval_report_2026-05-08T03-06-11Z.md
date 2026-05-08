# 统一大模型评测报告

- 生成时间：2026-05-08T03-06-11Z
- 参评模型数：1
- 用例类型数：3

## 模型总览

| 模型 | 总体均分 | 总体通过率 | 数据加工模板识别 | 根据已有对账场景建作业 | 根据系统结果 + SOP 分析差异 |
| --- | ---: | ---: | ---: | ---: | ---: |
| deepseek-v3.1 | 83.23 | 0.617 | 100.0 | 76.89 | 79.33 |

## 数据加工模板识别

| 用例ID | 标题 | deepseek-v3.1 |
| --- | --- | --- |
| DP001 | Payment invoice standard US clean headers | 100（通过） |
| DP002 | Payment invoice US variant headers | 100（通过） |
| DP003 | Payment invoice US similar headers v2 | 100（通过） |
| DP004 | Customs declaration CN clean headers | 100（通过） |
| DP005 | Customs declaration CN similar headers v2 | 100（通过） |
| DP006 | Vendor settlement EU variant headers | 100（通过） |
| DP007 | Vendor settlement EU similar headers v2 | 100（通过） |
| DP008 | Order fulfillment JP 22-column variant | 100（通过） |
| DP009 | Rebate MX similar headers v2 | 100（通过） |
| DP010 | Channel rebate MX 22 unrelated headers | 100（通过） |
| DP011 | Ambiguous trade document | 100（通过） |

### 数据加工模板识别 明细说明

#### deepseek-v3.1

| 用例ID | 分数 | 结果 | 说明 |
| --- | ---: | --- | --- |
| DP001 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP002 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP003 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP004 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP005 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP006 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP007 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP008 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP009 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP010 | 100 | 通过 | Template, scene, and country matched expected values. |
| DP011 | 100 | 通过 | Ambiguous case correctly stayed unresolved. |


## 根据已有对账场景建作业

| 用例ID | 标题 | deepseek-v3.1 |
| --- | --- | --- |
| JC001 | 电商订单与支付流水日对账 | 65（待复核） |
| JC002 | ERP 应收与总账月末对账 | 45（待复核） |
| JC003 | 银行回单与 ERP 收款核销 | 100（通过） |
| JC004 | 退款单与支付退款流水 | 62（待复核） |
| JC005 | 仓储出库与订单履约 | 90（通过） |
| JC006 | 跨币种结算对账 | 70（待复核） |
| JC007 | 海关申报与 ERP 报关单 | 67（待复核） |
| JC008 | 税局发票与 ERP 销项 | 73（待复核） |
| JC009 | POS 与总账汇总核对 | 73（待复核） |
| JC010 | 模糊来源系统 | 85（通过） |
| JC011 | 缺少匹配键 | 100（通过） |
| JC012 | 自然语言同义表达 | 65（待复核） |
| JC013 | 中英文混输 | 100（通过） |
| JC014 | 包含过滤条件 | 62（待复核） |
| JC015 | 日期容差窗口 | 75（待复核） |
| JC016 | 多键匹配和费用比较 | 75（待复核） |
| JC017 | 冲突指令 | 97（通过） |
| JC018 | 明确要求不要创建 | 80（通过） |

### 根据已有对账场景建作业 明细说明

#### deepseek-v3.1

| 用例ID | 分数 | 结果 | 说明 |
| --- | ---: | --- | --- |
| JC001 | 65 | 待复核 | - |
| JC002 | 45 | 待复核 | - |
| JC003 | 100 | 通过 | - |
| JC004 | 62 | 待复核 | - |
| JC005 | 90 | 通过 | - |
| JC006 | 70 | 待复核 | - |
| JC007 | 67 | 待复核 | - |
| JC008 | 73 | 待复核 | - |
| JC009 | 73 | 待复核 | - |
| JC010 | 85 | 通过 | - |
| JC011 | 100 | 通过 | - |
| JC012 | 65 | 待复核 | - |
| JC013 | 100 | 通过 | - |
| JC014 | 62 | 待复核 | - |
| JC015 | 75 | 待复核 | - |
| JC016 | 75 | 待复核 | - |
| JC017 | 97 | 通过 | - |
| JC018 | 80 | 通过 | - |


## 根据系统结果 + SOP 分析差异

| 用例ID | 标题 | deepseek-v3.1 |
| --- | --- | --- |
| DA001 | 源端缺失 | 85（通过） |
| DA002 | 重复流水 | 100（通过） |
| DA003 | 主键错位 | 75（待复核） |
| DA004 | 四舍五入误差 | 88（通过） |
| DA005 | 税率口径不一致 | 100（通过） |
| DA006 | 状态时点差 | 85（通过） |
| DA007 | 人工调账 | 80（通过） |
| DA008 | 字段映射错误 | 85（通过） |
| DA009 | 过滤范围不一致 | 80（通过） |
| DA010 | 退款冲抵 | 40（待复核） |
| DA011 | 跨期截断 | 83（通过） |
| DA012 | 上游程序缺陷 | 71（待复核） |
| DA013 | 证据不足 | 83（通过） |
| DA014 | 数量一致但状态不一致 | 75（待复核） |
| DA015 | 发票主键口径混用 | 70（待复核） |
| DA016 | 多次导入导致重复 | 65（待复核） |
| DA017 | 站点范围与状态过滤同时不一致 | 63（待复核） |
| DA018 | 币种一致但汇率表版本不同 | 100（通过） |

### 根据系统结果 + SOP 分析差异 明细说明

#### deepseek-v3.1

| 用例ID | 分数 | 结果 | 说明 |
| --- | ---: | --- | --- |
| DA001 | 85 | 通过 | - |
| DA002 | 100 | 通过 | - |
| DA003 | 75 | 待复核 | - |
| DA004 | 88 | 通过 | - |
| DA005 | 100 | 通过 | - |
| DA006 | 85 | 通过 | - |
| DA007 | 80 | 通过 | - |
| DA008 | 85 | 通过 | - |
| DA009 | 80 | 通过 | - |
| DA010 | 40 | 待复核 | - |
| DA011 | 83 | 通过 | - |
| DA012 | 71 | 待复核 | - |
| DA013 | 83 | 通过 | - |
| DA014 | 75 | 待复核 | - |
| DA015 | 70 | 待复核 | - |
| DA016 | 65 | 待复核 | - |
| DA017 | 63 | 待复核 | - |
| DA018 | 100 | 通过 | - |
