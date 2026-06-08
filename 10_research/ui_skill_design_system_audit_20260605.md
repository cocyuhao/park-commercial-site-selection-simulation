# UI 技能设计系统审计（2026-06-05）

> 来源：本机已安装 `ui-ux-pro-max`，路径 `C:\Users\Yy199\.codex\skills\ui-ux-pro-max`。  
> 用途：约束下一版“AI 仿真决策系统”页面级重构，不作为最终视觉稿。

## 1. 本轮技能状态

- `playwright`、`playwright-interactive`、`ui-ux-pro-max`、`web-design-guidelines` 已存在于 `C:\Users\Yy199\.codex\skills`。
- 当前会话技能清单没有自动暴露其中一部分，因此后续新会话应重启 Codex 或按本文件手动读取技能目录。
- `skill-installer` 官方列表接口本轮返回 HTTP 403；没有强行安装第三方低可信技能。
- 直接安装 `openai/skills` 的 `playwright` 时提示本地已存在，说明问题不是缺技能，而是路由和会话暴露不稳定。

## 2. ui-ux-pro-max 查询

### 查询一：设计系统

命令：

```powershell
py -3.12 C:\Users\Yy199\.codex\skills\ui-ux-pro-max\scripts\search.py "AI simulation decision support dashboard human oversight data dense professional" --design-system -p "AI Simulation Decision System" -f markdown
```

关键结果：

- 推荐风格：`Data-Dense Dashboard`。
- 适用场景：商业智能、企业报表、运营工作台、数据可见性高的系统。
- 色彩：蓝色数据体系，琥珀色作为行动提示。
- 可访问性：强调 WCAG AA、焦点状态、减少颜色单独传达状态。
- 反模式：过度装饰、没有过滤能力。

### 查询二：UX 规则

命令：

```powershell
py -3.12 C:\Users\Yy199\.codex\skills\ui-ux-pro-max\scripts\search.py "dashboard accessibility state machine workflow" --domain ux -n 8
```

关键结果：

- 当前页面/区段必须有明确 active state。
- 动态状态最好支持 deep linking 或 hash，便于共享和恢复。
- 错误信息需要 `aria-live` 或 `role=alert`。
- 状态不能只靠颜色，必须有文字或图标辅助。
- 图标按钮必须有可访问名称。
- 全功能必须支持键盘访问。

### 查询三：布局与实现

命令：

```powershell
py -3.12 C:\Users\Yy199\.codex\skills\ui-ux-pro-max\scripts\search.py "data dashboard layout responsive controls" --stack html-tailwind
```

关键结果：

- 响应式 padding 需要分断点，不应一套间距打全屏。
- 移动/桌面可以隐藏显示同一内容结构，不应做两套内容导致状态分裂。
- 图片和地图资产要按设备尺寸处理，不能所有视口加载同一大图。

## 3. 对本项目的采用判断

采用：

- 下一版页面应走“高可读、强状态、少装饰、低废话”的数据工作台风格。
- 用户不是小白，所以界面不应幼稚化；但也不能把后端字段、门禁词、技术验证直接铺给用户。
- 状态应以对象链和任务推进表达，而不是用固定文案和裸分数表达。
- 颜色系统可以收紧为蓝色数据 / 琥珀行动 / 红色阻塞 / 绿色可推进，且每种颜色必须有文字标签。
- AI 工作台、对象池、资料池、仿真预检都要支持 active state、可恢复状态和可访问反馈。

暂不采用：

- `FAQ/Documentation Landing` 的结构不适合本项目首屏；首屏不应做帮助中心或营销式 FAQ。
- `Fira Code` 不适合作为业务工作台主标题字体，容易让页面像程序员工具；可以只在技术证据折叠区或代码/路径文本中使用。
- 不使用 Google Fonts 作为最终强依赖，避免本地/内网/录屏时字体加载不稳定。

## 4. 进入页面级重构的硬约束

1. 首屏必须是“任务编排 + 对象链状态”，不是说明页。
2. 旧导航可暂保留为迁移入口，但下一版应从并列页面切到流程型工作区。
3. 资料、对象、地图、AI、报告必须串联，不再分兵作战。
4. 所有阻塞项必须说明“为什么不能继续”和“下一步补什么”。
5. 用户可见区域不得出现 `debug/raw/payload/traceback/ConnectError/external_preview_only`。
6. 完整仿真未闭合时，按钮和报告都必须保持工作稿/预检口径。

