import React, { useEffect } from 'react'
import { Sidebar } from './Sidebar'
import { useAppStore } from '@/store'
import { THEME_COLORS } from '@/config/theme'
import './MainLayout.css'

interface MainLayoutProps {
  children: React.ReactNode
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { theme, background, showHighAlert, alertTask, setShowHighAlert, timer } =
    useAppStore()
  const themeConfig = THEME_COLORS[theme]

  useEffect(() => {
    const checkInterval = setInterval(() => {
      if (timer.state === 'idle') {
        useAppStore.getState().checkReminders()
      }
    }, 60000)

    return () => clearInterval(checkInterval)
  }, [timer.state])

  return (
    <div
      className="main-layout"
      style={
        {
          '--primary-color': themeConfig.primary,
          '--secondary-color': themeConfig.secondary,
          '--background-image': background ? `url(${background})` : 'none',
        } as React.CSSProperties
      }
    >
      <Sidebar />
      <div className="main-content">
        {showHighAlert && alertTask && (
          <div
            className="alert-bar alert-bar-high"
            style={{
              backgroundColor: '#fa8c16',
            }}
          >
            <span>⚠️ 任务 "{alertTask.title}" 即将到期！</span>
            <button onClick={() => setShowHighAlert(false)}>✕</button>
          </div>
        )}
        <div className="content-wrapper">{children}</div>
      </div>
    </div>
  )
}
