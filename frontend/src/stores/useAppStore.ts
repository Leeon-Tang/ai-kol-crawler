import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  // 当前选中的平台
  currentPlatform: 'youtube' | 'github' | 'twitter'
  setCurrentPlatform: (platform: 'youtube' | 'github' | 'twitter') => void

  // 爬虫运行状态
  crawlerRunning: boolean
  setCrawlerRunning: (running: boolean) => void

  // 侧边栏折叠状态
  sidebarCollapsed: boolean
  toggleSidebar: () => void

  // WebSocket 连接状态
  wsConnected: boolean
  setWsConnected: (connected: boolean) => void

  // 主题模式
  theme: 'light' | 'dark'
  toggleTheme: () => void
  setTheme: (theme: 'light' | 'dark') => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      currentPlatform: 'youtube',
      setCurrentPlatform: (platform) => set({ currentPlatform: platform }),

      crawlerRunning: false,
      setCrawlerRunning: (running) => set({ crawlerRunning: running }),

      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      wsConnected: false,
      setWsConnected: (connected) => set({ wsConnected: connected }),

      theme: 'light',
      toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({ 
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
)
