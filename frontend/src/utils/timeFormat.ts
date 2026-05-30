import dayjs from 'dayjs'
import duration from 'dayjs/plugin/duration'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(duration)
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

export const formatTimeMMSS = (seconds: number): string => {
  const totalSeconds = Math.max(0, Math.floor(seconds))
  const minutes = Math.floor(totalSeconds / 60)
  const secs = totalSeconds % 60
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

export const formatTimeHHMMSS = (seconds: number): string => {
  const totalSeconds = Math.max(0, Math.floor(seconds))
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const secs = totalSeconds % 60
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

export const formatMinutes = (minutes: number): string => {
  return `${Math.round(minutes)}分钟`
}

export const getTimeUntilDue = (dueDate: string): { minutes: number; text: string; isUrgent: boolean } => {
  const now = dayjs()
  const due = dayjs(dueDate)
  const diffMinutes = due.diff(now, 'minute')

  let text = ''
  let isUrgent = false

  if (diffMinutes <= 0) {
    text = '已到期'
    isUrgent = true
  } else if (diffMinutes < 60) {
    text = `${diffMinutes}分钟`
    isUrgent = diffMinutes <= 15
  } else if (diffMinutes < 1440) {
    const hours = Math.floor(diffMinutes / 60)
    const mins = diffMinutes % 60
    text = mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
    isUrgent = false
  } else {
    const days = Math.floor(diffMinutes / 1440)
    text = `${days}天`
    isUrgent = false
  }

  return { minutes: diffMinutes, text, isUrgent }
}

export const getFriendlyDate = (date: string): string => {
  const d = dayjs(date)
  const today = dayjs()
  const tomorrow = today.add(1, 'day')

  if (d.isSame(today, 'day')) {
    return '今天'
  } else if (d.isSame(tomorrow, 'day')) {
    return '明天'
  } else {
    return d.format('MM-DD')
  }
}

export const getDateRange = (days: number = 7): { start: string; end: string } => {
  const end = dayjs()
  const start = end.subtract(days, 'day')
  return {
    start: start.format('YYYY-MM-DD'),
    end: end.format('YYYY-MM-DD'),
  }
}

export const getWeekRange = (date: dayjs.Dayjs = dayjs()): { start: string; end: string } => {
  const start = date.startOf('week')
  const end = date.endOf('week')
  return {
    start: start.format('YYYY-MM-DD'),
    end: end.format('YYYY-MM-DD'),
  }
}

export const getMonthRange = (date: dayjs.Dayjs = dayjs()): { start: string; end: string } => {
  const start = date.startOf('month')
  const end = date.endOf('month')
  return {
    start: start.format('YYYY-MM-DD'),
    end: end.format('YYYY-MM-DD'),
  }
}

export const formatDateTime = (date: string): string => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

export const formatDate = (date: Date | string): string => {
  return dayjs(date).format('YYYY-MM-DD')
}

export const calculateProgress = (elapsed: number, total: number): number => {
  if (total <= 0) return 0
  return Math.min(100, Math.max(0, (elapsed / total) * 100))
}

export const parseMMSS = (timeString: string): number => {
  const [minutes, seconds] = timeString.split(':').map(Number)
  return (minutes || 0) * 60 + (seconds || 0)
}
