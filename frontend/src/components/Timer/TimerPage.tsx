import React, { useEffect, useState } from 'react'
import { Button, message } from 'antd'
import {
  PauseCircleOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { formatTimeMMSS } from '@/utils/timeFormat'
import { CountdownRing } from './CountdownRing'
import { THEME_COLORS } from '@/config/theme'
import { PomodoroPhase } from '@/types'
import { useAppStore } from '@/store'
import { playAudio, showNotification } from '@/utils/audio'
import './TimerPage.css'

export const TimerPage: React.FC = () => {
  const { timer, theme, pauseTimer, resumeTimer, completeTimer, stopTimer, nextPhase } =
    useAppStore()
  const [pauseStartTime, setPauseStartTime] = useState<number | null>(null)
  const [totalPaused, setTotalPaused] = useState(0)
  const themeConfig = THEME_COLORS[theme]

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null

    if (timer.state === 'running') {
      interval = setInterval(() => {
        useAppStore.getState().tickTimer()
      }, 1000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [timer.state])

  useEffect(() => {
    if (timer.state === 'finished') {
      handleFinish()
    }
  }, [timer.state])

  const handlePause = () => {
    setPauseStartTime(Date.now())
    pauseTimer()
  }

  const handleResume = () => {
    if (pauseStartTime) {
      setTotalPaused(totalPaused + (Date.now() - pauseStartTime) / 1000)
    }
    setPauseStartTime(null)
    resumeTimer()
  }

  const handleFinish = () => {
    if (timer.phase === 'work') {
      playAudio('/assets/audio/alert.mp3')
      showNotification('番茄完成', '恭喜完成一个番茄钟！')
      message.success('番茄钟完成，准备休息')
      nextPhase()
    } else {
      playAudio('/assets/audio/alert.mp3')
      showNotification('休息结束', '休息结束，准备开始新的番茄钟！')
      message.success('休息结束，开始工作')
      nextPhase()
    }
  }

  const handleComplete = () => {
    completeTimer()
    stopTimer()
  }

  const handleSkipBreak = () => {
    nextPhase()
  }

  const getPhaseText = (phase: PomodoroPhase | 'idle'): string => {
    switch (phase) {
      case 'work':
        return '专注时间'
      case 'short_break':
        return '短休息'
      case 'long_break':
        return '长休息'
      default:
        return ''
    }
  }

  const getMotto = (phase: PomodoroPhase | 'idle'): string => {
    switch (phase) {
      case 'work':
        return '专注当下，每一分钟都算数'
      case 'short_break':
        return '休息一下，喝杯水'
      case 'long_break':
        return '好好休息，为下一个番茄充能'
      default:
        return ''
    }
  }

  const getIconPath = (phase: PomodoroPhase | 'idle'): string => {
    switch (phase) {
      case 'work':
        return '/assets/icons/timer-icon.png'
      case 'short_break':
        return '/assets/icons/short-break.png'
      case 'long_break':
        return '/assets/icons/long-break.png'
      default:
        return '/assets/icons/timer-icon.png'
    }
  }

  const getCurrentPausedDuration = () => {
    if (!pauseStartTime) return 0
    return (Date.now() - pauseStartTime) / 1000
  }

  const totalPausedDisplay = totalPaused + getCurrentPausedDuration()

  if (timer.state === 'idle') {
    return null
  }

  return (
    <div className="timer-page">
      <div className="timer-container">
        <div className="timer-motto">{getMotto(timer.phase)}</div>

        <div className="timer-ring-wrapper">
          <CountdownRing
            remaining={timer.remaining}
            total={timer.total}
            theme={theme}
            phase={timer.phase}
            paused={timer.state === 'paused'}
          />
          <div className="timer-icon">
            <img src={getIconPath(timer.phase)} alt={getPhaseText(timer.phase)} />
          </div>
          <div className="timer-display">{formatTimeMMSS(timer.remaining)}</div>
        </div>

        <div className="timer-controls">
          {timer.state === 'running' ? (
            <Button
              type="primary"
              size="large"
              icon={<PauseCircleOutlined />}
              onClick={handlePause}
              style={{
                backgroundColor: themeConfig.primary,
                borderColor: themeConfig.primary,
                width: 120,
                height: 40,
                fontSize: 16,
              }}
            >
              暂停
            </Button>
          ) : (
            <div className="paused-controls">
              <Button
                type="primary"
                size="large"
                icon={<PlayCircleOutlined />}
                onClick={handleResume}
                style={{
                  backgroundColor: themeConfig.primary,
                  borderColor: themeConfig.primary,
                  width: 100,
                  height: 40,
                  fontSize: 16,
                }}
              >
                开始
              </Button>
              <Button
                type="default"
                size="large"
                icon={<CheckCircleOutlined />}
                onClick={handleComplete}
                style={{
                  width: 100,
                  height: 40,
                  fontSize: 16,
                }}
              >
                完成
              </Button>
            </div>
          )}
        </div>

        {timer.state === 'paused' && (
          <div className="timer-paused-info">
            已暂停: {formatTimeMMSS(totalPausedDisplay)}
          </div>
        )}

        {timer.phase !== 'work' && timer.state === 'running' && (
          <div className="timer-skip-break">
            <Button type="link" size="small" onClick={handleSkipBreak}>
              结束休息，继续工作
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
