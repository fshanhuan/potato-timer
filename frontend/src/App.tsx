import React, { useEffect } from 'react'
import { ConfigProvider, Modal } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { MainLayout } from '@/components/Layout/MainLayout'
import { TaskList } from '@/components/Task/TaskList'
import { TimerPage } from '@/components/Timer/TimerPage'
import { SettingsPage } from '@/components/Settings/SettingsPage'
import { AIPage } from '@/components/AI/AIPage'
import { StatsPage } from '@/components/Stats/StatsPage'
import { useAppStore } from '@/store'
import { playAudio } from '@/utils/audio'
import './App.css'

const CriticalAlertModal: React.FC = () => {
  const { showCriticalAlert, alertTask, setShowCriticalAlert } = useAppStore()

  useEffect(() => {
    if (showCriticalAlert) {
      playAudio('/assets/audio/alert.mp3')
    }
  }, [showCriticalAlert])

  const handleOK = () => {
    setShowCriticalAlert(false)
  }

  if (!showCriticalAlert || !alertTask) return null

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <img
            src="/assets/icons/alert-icon.png"
            alt="警告"
            style={{ width: 24, height: 24 }}
          />
          紧急提醒
        </div>
      }
      open={showCriticalAlert}
      onOk={handleOK}
      onCancel={handleOK}
      okText="我知道了"
      cancelButtonProps={{ style: { display: 'none' } }}
      centered
      width={480}
    >
      <div className="critical-alert-content">
        <img
          src="/assets/icons/alert-icon.png"
          alt="警告"
          style={{ width: 64, height: 64, marginBottom: 16 }}
        />
        <p style={{ fontSize: 16, marginBottom: 8 }}>
          事件 "<strong>{alertTask.title}</strong>" 即将到期！
        </p>
        <p style={{ color: '#666', fontSize: 14 }}>
          请尽快完成或调整优先级
        </p>
      </div>
    </Modal>
  )
}

const App: React.FC = () => {
  const { timer } = useAppStore()

  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  const renderContent = () => {
    if (timer.state !== 'idle') {
      return <TimerPage />
    }

    switch (useAppStore.getState().currentPage) {
      case 'tasks':
        return <TaskList />
      case 'settings':
        return <SettingsPage />
      case 'ai':
        return <AIPage />
      case 'stats':
        return <StatsPage />
      default:
        return <TaskList />
    }
  }

  return (
    <ConfigProvider locale={zhCN}>
      <MainLayout>
        {renderContent()}
      </MainLayout>
      <CriticalAlertModal />
    </ConfigProvider>
  )
}

export default App
