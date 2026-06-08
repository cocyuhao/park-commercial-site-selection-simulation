# Web Interface Guidelines 审计记录（2026-06-05）

> 来源：`web-design-guidelines` 技能要求读取 Vercel 最新 Web Interface Guidelines。  
> 本轮已打开官方源：`https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`。  
> 目标：只做和当前页面级重构直接相关的轻量检查，不把它伪装成完整设计验收。

## 1. 本轮检查范围

文件：

- `90_p6_expert_dashboard/static/index.html`
- `90_p6_expert_dashboard/static/app.js`
- `90_p6_expert_dashboard/static/styles.css`

检查点：

- 焦点可见性
- 表单与按钮可访问名称
- 图片 alt
- 页面状态 deep link
- 后端词泄露
- 响应式和键盘使用的基础风险

## 2. 发现与处理

### 已处理

- CSS 中有多处 `outline: none`。这会让键盘用户难以看到当前焦点。
- 已在 `styles.css` 增加统一：

```css
button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
summary:focus-visible {
  outline: 3px solid rgba(29, 126, 119, .28);
  outline-offset: 2px;
}
```

### 已确认可接受

- `index.html` 没有 `user-scalable=no` 或 `maximum-scale`。
- 高德静态图有 `alt`。
- 图标/符号按钮中的关键按钮已有 `aria-label`，例如关闭资料池、地图放大/缩小、上传资料、发送。
- 视图切换已经写入 hash，具备基础 deep linking：`window.location.hash`。

### 仍需在页面级重构中继续处理

- 当前页面仍有大量动态 `innerHTML`。多数已使用 `esc()` 或受控数据，但下一版重构应减少大段模板拼接，或集中到渲染 helper，降低漏转义和可访问性遗漏风险。
- 当前导航仍是旧 view 并列，不是完整流程型信息架构。
- 搜索、资料池、对象池、AI 对话、报告生成等关键状态后续应进一步映射到 URL/hash 或可恢复状态。

## 3. 对 DEC-087 的影响

本轮 Web Guidelines 审计强化了同一个判断：

- 当前页面可以作为过渡基线继续运行。
- 它不是最终信息架构。
- 下一步页面级重构时，必须把 active state、focus-visible、aria-live、deep linking 和状态恢复作为基础约束，而不是最后补丁。

