# FINAL REPORT STYLE AUDIT

审计时间：2026-06-11

## 1. 被检查的 LaTeX 文件清单

- `report/main.tex`
- `report/chapters/01_intro_planning.tex`
- `report/chapters/02_requirements.tex`
- `report/chapters/03_conceptual_design.tex`
- `report/chapters/04_logical_design.tex`
- `report/chapters/05_normalization.tex`
- `report/chapters/06_constraints_triggers.tex`
- `report/chapters/07_transaction_locks.tex`
- `report/chapters/08_physical_design.tex`
- `report/chapters/09_operation_maintenance.tex`
- `report/chapters/10_conclusion.tex`
- `report/chapters/appendix_sql_tests.tex`
- `report/FINAL_COMPLETION_AUDIT.md`

## 2. 关键词审计范围

使用 `rg` 检查了以下过程性、开发日志式或讲义式关键词：

`本轮`、`本次`、`这一轮`、`这次`、`上一轮`、`前一轮`、`当前改造`、`当前设计中仍`、`已经修正`、`已修正`、`新增了`、`补充了`、`修改了`、`删除了`、`迁移前`、`迁移后`、`旧版本`、`之前`、`现在`、`freeze`、`本章`、`本节`、`下文`、`上一章`、`下一章`。

## 3. 发现的过程性表述

清理前主要集中在以下位置：

- 第 2 章：使用“本轮数据库优化后”描述同课跨班限制。
- 第 5 章：使用“本轮新增”“本章小结”“当前设计中仍”等表达规范化优化。
- 第 6 章：使用“本轮新增”“本章说明”描述触发器和约束实现。
- 第 7 章：使用“本轮改造后”“本章小结”描述事务与锁。
- 第 9 章：使用“本轮执行结果”“本轮新增”描述测试脚本和权限脚本。
- 附录：使用“本轮运行”“本轮回滚型测试输出”描述测试证据。
- `FINAL_COMPLETION_AUDIT.md`：使用“本轮实际验证结果”“本次审计”等过程性表达。

## 4. 发现的教材式表述

主要包括：

- “本章对应……”
- “本章重点……”
- “本章小结”
- “本节将……”

这些表达容易让报告显得像课堂讲义。修改后改为“第 X 章”“规范化分析”“完整性机制小结”“事务与锁机制小结”等更正式的课程报告表达。

## 5. 修改原则

- 从“开发过程叙述”改为“最终系统状态叙述”。
- 从“做了什么”改为“系统如何设计、如何实现、如何验证”。
- 保留真实 SQL、后端代码和测试证据，不把未实现内容写成已实现。
- 保留“后续改进”表达，因为第 10 章需要说明不足与扩展方向。
- 技术词“事务上下文”“审计上下文”改为“事务环境”“审计变量”，避免误触发“下文”关键词。

## 6. 修改后的整体风格

报告现在以冻结后的最终系统为对象进行陈述。第 1--10 章仍按数据库设计流程组织，但语言从开发日志式表达改为课程报告式表达。规范化、触发器、事务、锁、视图、测试验证等内容均围绕最终 SQL、后端服务和测试脚本展开。

## 7. 复查结果

对正式 LaTeX 文件和 `FINAL_COMPLETION_AUDIT.md` 再次执行关键词检查，未发现上述过程性关键词命中。该审计文件自身保留关键词列表和问题归类，属于审计说明，不属于正文报告。

## 8. 仍需人工确认的句子

- 第 9 章界面截图小节只插入了已经真实存在的 4 张截图；其余页面列入 `report/UI_SCREENSHOT_TODO.md`。
- 如果后续人工补齐课程选课、课表、成绩录入和审计日志截图，需要同步更新 `report/UI_SCREENSHOT_INDEX.md` 并重新编译 PDF。
