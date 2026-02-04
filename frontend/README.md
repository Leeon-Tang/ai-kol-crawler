# 多平台爬虫系统 - 前端

基于 React + TypeScript + Ant Design 的现代化前端界面

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design** - UI 组件库
- **TanStack Query** - 数据请求和缓存
- **Zustand** - 状态管理
- **React Router** - 路由管理

## 开发

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

前端将运行在 `http://localhost:3000`，API 代理到 `http://localhost:8501`

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `frontend/dist` 目录

## 项目结构

```
frontend/
├── src/
│   ├── components/       # 可复用组件
│   │   └── Layout/       # 布局组件
│   ├── pages/            # 页面组件
│   │   ├── Dashboard.tsx
│   │   ├── Crawler.tsx
│   │   ├── DataBrowser.tsx
│   │   ├── Logs.tsx
│   │   └── Settings.tsx
│   ├── services/         # API 服务
│   │   └── api.ts
│   ├── stores/           # 状态管理
│   │   └── useAppStore.ts
│   ├── App.tsx           # 主应用
│   ├── main.tsx          # 入口文件
│   └── index.css         # 全局样式
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 功能特性

### 已实现
- ✅ 基础布局（侧边栏 + 顶部栏）
- ✅ 路由系统
- ✅ API 服务层
- ✅ 状态管理
- ✅ Dashboard 页面（统计数据展示）

### 待实现
- ⏳ 爬虫控制页面（启动/停止任务）
- ⏳ 数据浏览页面（表格展示 + 筛选）
- ⏳ 日志查看页面（实时日志 + WebSocket）
- ⏳ 设置页面（配置管理）
- ⏳ 数据导出功能
- ⏳ 响应式设计优化

## 自定义主题

在 `src/main.tsx` 中修改 Ant Design 主题：

```tsx
<ConfigProvider
  theme={{
    token: {
      colorPrimary: '#1890ff',  // 主色
      borderRadius: 6,           // 圆角
    },
  }}
>
```

## API 接口

所有 API 请求通过 `src/services/api.ts` 统一管理：

```typescript
import { apiService } from '@/services/api'

// 获取统计数据
const stats = await apiService.getStatistics('youtube')

// 启动爬虫
await apiService.startCrawler({
  platform: 'youtube',
  task_type: 'discovery',
  params: { keyword_limit: 5 }
})
```

## 开发建议

1. **组件化开发**：将可复用的 UI 抽取为独立组件
2. **类型安全**：充分利用 TypeScript 的类型系统
3. **状态管理**：使用 Zustand 管理全局状态
4. **数据请求**：使用 TanStack Query 处理异步数据
5. **样式定制**：使用 Ant Design 的主题系统和 CSS Modules

## 注意事项

- 开发时确保后端 API 服务（`api.py`）已启动
- WebSocket 连接用于实时日志推送
- 生产环境需要构建前端并由后端提供静态文件服务
