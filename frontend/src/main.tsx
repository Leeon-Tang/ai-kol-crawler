import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import { useAppStore } from './stores/useAppStore'
import { lightTheme, darkTheme } from './styles/theme'
import './styles/theme-variables.css'
import './index.css'
import './styles/light.css'
import './styles/dark.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function ThemedApp() {
  const theme = useAppStore((state) => state.theme)

  useEffect(() => {
    // 更新 body 的 class 和 data-theme 属性
    document.body.className = `${theme}-theme`
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <ConfigProvider
      locale={zhCN}
      theme={theme === 'dark' ? darkTheme : lightTheme}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemedApp />
    </QueryClientProvider>
  </React.StrictMode>,
)
