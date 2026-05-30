import React from 'react'
import { Card, Tag, Button } from 'antd'
import { ClockCircleOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { Task, ImportanceLevel, TimerMode } from '@/types'
import { getTimeUntilDue } from '@/utils/timeFormat'
import { THEME_COLORS } from '@/config/theme'
import { useAppStore } from '@/store'
import './TaskCard.css'

interface TaskCardProps {
  task: Task
  onStart?: () => void
}

export const TaskCard: React.FC<TaskCardProps> = ({ task, onStart }) => {
  const { theme } = useAppStore()
  const themeConfig = THEME_COLORS[theme]

  const timeUntil = task.due_date ? getTimeUntilDue(task.due_date) : null
  const isUrgent = timeUntil?.isUrgent

  const getImportanceColor = (level: ImportanceLevel): string => {
    switch (level) {
      case ImportanceLevel.LOW:
        return 'default'
      case ImportanceLevel.MEDIUM:
        return 'blue'
      case ImportanceLevel.HIGH:
        return 'orange'
      case ImportanceLevel.CRITICAL:
        return 'red'
      default:
        return 'default'
    }
  }

  const getImportanceText = (level: ImportanceLevel): string => {
    switch (level) {
      case ImportanceLevel.LOW:
        return '普通'
      case ImportanceLevel.MEDIUM:
        return '重要'
      case ImportanceLevel.HIGH:
        return '很重要'
      case ImportanceLevel.CRITICAL:
        return '紧急'
      default:
        return '普通'
    }
  }

  const getModeText = (mode: TimerMode): string => {
    switch (mode) {
      case TimerMode.POMODORO:
        return '番茄钟'
      case TimerMode.COUNTDOWN:
        return '倒计时'
      case TimerMode.COUNTUP:
        return '正计时'
      default:
        return '番茄钟'
    }
  }

  return (
    <Card
      className={`task-card ${isUrgent ? 'urgent' : ''}`}
      style={{
        borderColor: isUrgent ? '#ff4d4f' : undefined,
      }}
      hoverable
    >
      <div className="task-card-header">
        <div className="task-title-row">
          <Tag color={getImportanceColor(task.importance)}>
            {getImportanceText(task.importance)}
          </Tag>
          <h3 className="task-title">{task.title}</h3>
        </div>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          size="small"
          onClick={onStart}
          style={{
            backgroundColor: themeConfig.primary,
            borderColor: themeConfig.primary,
          }}
        >
          开始
        </Button>
      </div>

      <p className="task-description">{task.description}</p>

      <div className="task-info">
        {task.due_date && timeUntil && (
          <div className="task-due-date">
            <ClockCircleOutlined />
            <span>
              {timeUntil.minutes <= 0
                ? '已到期'
                : `距离截止 ${timeUntil.text}`}
            </span>
            {timeUntil.minutes <= 0 && (
              <span className="expired-tag">已过期</span>
            )}
          </div>
        )}
        <div className="task-meta">
          <Tag>{getModeText(task.mode)}</Tag>
          <span>计划: {task.planned_minutes}分钟</span>
          {task.total_focused_minutes > 0 && (
            <span>已专注: {task.total_focused_minutes.toFixed(1)}分钟</span>
          )}
        </div>
      </div>
    </Card>
  )
}
