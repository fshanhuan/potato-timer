import {
  CreateTaskDTO,
  Task,
  TaskReminder,
  TaskStatus,
  ImportanceLevel,
  TimeUsageReport,
  CreatePlanDTO,
  FocusPlan,
  PlanProgress,
  SessionRecord,
  DailyStats,
} from '@/types'

// ========== Mock API ==========
// 用于前端演示和测试，接入后端时替换为真实 fetch 调用

export const mockAPI = {
  // Mock 任务数据
  tasks: [
    {
      task_id: 1,
      title: '学习 Python 后端开发',
      description: '完成番茄钟项目的后端逻辑开发',
      motto: '专注当下，每一分钟都算数',
      due_date: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
      importance: 3 as const,
      planned_minutes: 45,
      reminder_at: null,
      mode: 0 as const,
      status: TaskStatus.PENDING,
      created_at: new Date().toISOString(),
      completed_at: null,
      total_focused_minutes: 0,
    },
    {
      task_id: 2,
      title: '编写前端组件',
      description: '使用 React + TypeScript 开发 UI 组件',
      motto: '先完成最小的一步，再完成下一步',
      due_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      importance: ImportanceLevel.MEDIUM,
      planned_minutes: 60,
      reminder_at: null,
      mode: 0 as const,
      status: TaskStatus.PENDING,
      created_at: new Date().toISOString(),
      completed_at: null,
      total_focused_minutes: 15,
    },
  ] as Task[],

  getTasks: async (): Promise<Task[]> => {
    await new Promise((resolve) => setTimeout(resolve, 100))
    return [...mockAPI.tasks]
  },

  createTask: async (data: CreateTaskDTO): Promise<Task> => {
    await new Promise((resolve) => setTimeout(resolve, 100))
    const newTask: Task = {
      task_id: mockAPI.tasks.length + 1,
      title: data.title,
      description: data.description,
      motto: data.motto || '专注当下，每一分钟都算数',
      due_date: data.due_date,
      importance: data.importance || 2,
      planned_minutes: data.planned_minutes || 25,
      reminder_at: data.reminder_at || null,
      mode: data.mode,
      status: TaskStatus.PENDING,
      created_at: new Date().toISOString(),
      completed_at: null,
      total_focused_minutes: 0,
    }
    mockAPI.tasks.push(newTask)
    return newTask
  },

  getReminders: async (): Promise<TaskReminder[]> => {
    await new Promise((resolve) => setTimeout(resolve, 100))
    return []
  },
}

/*
// ========== 后端接口（接入后端时取消注释） ==========

export const timerAPI = {
  start: async (taskId: number, mode: string): Promise<TimerStateResponse> => {
    const res = await fetch('/api/timer/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ taskId, mode }),
    })
    if (!res.ok) throw new Error('Failed to start timer')
    return res.json()
  },

  tick: async (): Promise<TimerStateResponse> => {
    const res = await fetch('/api/timer/tick')
    if (!res.ok) throw new Error('Failed to tick timer')
    return res.json()
  },

  pause: async (): Promise<{ paused_at: string }> => {
    const res = await fetch('/api/timer/pause', { method: 'POST' })
    if (!res.ok) throw new Error('Failed to pause timer')
    return res.json()
  },

  resume: async (): Promise<{ resumed_at: string }> => {
    const res = await fetch('/api/timer/resume', { method: 'POST' })
    if (!res.ok) throw new Error('Failed to resume timer')
    return res.json()
  },

  complete: async (): Promise<TimerStateResponse> => {
    const res = await fetch('/api/timer/complete', { method: 'POST' })
    if (!res.ok) throw new Error('Failed to complete timer')
    return res.json()
  },

  stop: async (): Promise<{ focused_seconds: number }> => {
    const res = await fetch('/api/timer/stop', { method: 'POST' })
    if (!res.ok) throw new Error('Failed to stop timer')
    return res.json()
  },

  nextPhase: async (): Promise<TimerStateResponse> => {
    const res = await fetch('/api/timer/next_phase', { method: 'POST' })
    if (!res.ok) throw new Error('Failed to go to next phase')
    return res.json()
  },
}

export const taskAPI = {
  create: async (data: CreateTaskDTO): Promise<Task> => {
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to create task')
    return res.json()
  },

  list: async (): Promise<Task[]> => {
    const res = await fetch('/api/tasks')
    if (!res.ok) throw new Error('Failed to fetch tasks')
    return res.json()
  },

  get: async (taskId: number): Promise<Task> => {
    const res = await fetch(`/api/tasks/${taskId}`)
    if (!res.ok) throw new Error('Failed to fetch task')
    return res.json()
  },

  update: async (taskId: number, data: Partial<Task>): Promise<Task> => {
    const res = await fetch(`/api/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to update task')
    return res.json()
  },

  delete: async (taskId: number): Promise<void> => {
    const res = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete task')
  },

  search: async (keyword: string): Promise<Task[]> => {
    const res = await fetch(`/api/tasks/search?q=${encodeURIComponent(keyword)}`)
    if (!res.ok) throw new Error('Failed to search tasks')
    return res.json()
  },

  sort: async (by: 'due_date' | 'priority'): Promise<Task[]> => {
    const res = await fetch(`/api/tasks/sort?by=${by}`)
    if (!res.ok) throw new Error('Failed to sort tasks')
    return res.json()
  },

  getReminders: async (): Promise<TaskReminder[]> => {
    const res = await fetch('/api/tasks/reminders')
    if (!res.ok) throw new Error('Failed to fetch reminders')
    return res.json()
  },

  complete: async (taskId: number): Promise<Task> => {
    const res = await fetch(`/api/tasks/${taskId}/complete`, { method: 'POST' })
    if (!res.ok) throw new Error('Failed to complete task')
    return res.json()
  },

  abandon: async (taskId: number): Promise<Task> => {
    const res = await fetch(`/api/tasks/${taskId}/abandon`, { method: 'POST' })
    if (!res.ok) throw new Error('Failed to abandon task')
    return res.json()
  },
}

export const statsAPI = {
  getTimeUsageReport: async (params: {
    start_date: string
    end_date: string
  }): Promise<TimeUsageReport> => {
    const res = await fetch('/api/stats/time-usage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })
    if (!res.ok) throw new Error('Failed to fetch time usage report')
    return res.json()
  },

  getDaily: async (date: string): Promise<DailyStats | null> => {
    const res = await fetch(`/api/stats/daily?date=${date}`)
    if (!res.ok) throw new Error('Failed to fetch daily stats')
    const data = await res.json()
    return data || null
  },

  getWeekly: async (date: string): Promise<DailyStats[]> => {
    const res = await fetch(`/api/stats/weekly?date=${date}`)
    if (!res.ok) throw new Error('Failed to fetch weekly stats')
    return res.json()
  },

  getMonthly: async (year: number, month: number): Promise<DailyStats[]> => {
    const res = await fetch(`/api/stats/monthly?year=${year}&month=${month}`)
    if (!res.ok) throw new Error('Failed to fetch monthly stats')
    return res.json()
  },

  getRecordsBetween: async (startDate: string, endDate: string): Promise<SessionRecord[]> => {
    const res = await fetch(`/api/stats/records?start=${startDate}&end=${endDate}`)
    if (!res.ok) throw new Error('Failed to fetch records')
    return res.json()
  },

  getTotalFocusedToday: async (): Promise<number> => {
    const res = await fetch('/api/stats/today')
    if (!res.ok) throw new Error('Failed to fetch today stats')
    return res.json()
  },
}

export const planAPI = {
  create: async (data: CreatePlanDTO): Promise<FocusPlan> => {
    const res = await fetch('/api/plans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to create plan')
    return res.json()
  },

  list: async (): Promise<FocusPlan[]> => {
    const res = await fetch('/api/plans')
    if (!res.ok) throw new Error('Failed to fetch plans')
    return res.json()
  },

  get: async (planId: number): Promise<FocusPlan> => {
    const res = await fetch(`/api/plans/${planId}`)
    if (!res.ok) throw new Error('Failed to fetch plan')
    return res.json()
  },

  update: async (planId: number, data: Partial<FocusPlan>): Promise<FocusPlan> => {
    const res = await fetch(`/api/plans/${planId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to update plan')
    return res.json()
  },

  delete: async (planId: number): Promise<void> => {
    const res = await fetch(`/api/plans/${planId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete plan')
  },

  getProgress: async (planId: number, queryDate?: string): Promise<PlanProgress> => {
    const url = queryDate
      ? `/api/plans/${planId}/progress?date=${queryDate}`
      : `/api/plans/${planId}/progress`
    const res = await fetch(url)
    if (!res.ok) throw new Error('Failed to fetch plan progress')
    return res.json()
  },
}

export const aiAPI = {
  generatePlan: async (prompt: string): Promise<{
    message: string
    plan?: FocusPlan
    needsClarification?: boolean
  }> => {
    const res = await fetch('/api/ai/generate-plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    })
    if (!res.ok) throw new Error('Failed to generate plan')
    return res.json()
  },

  chat: async (messages: AIMessage[]): Promise<AIMessage> => {
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages }),
    })
    if (!res.ok) throw new Error('Failed to chat with AI')
    return res.json()
  },
}

export const userAPI = {
  create: async (nickname: string): Promise<{
    user_id: number
    username: string
  }> => {
    const res = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nickname }),
    })
    if (!res.ok) throw new Error('Failed to create user')
    return res.json()
  },

  get: async (): Promise<{
    user_id: number
    username: string
  }> => {
    const res = await fetch('/api/users/me')
    if (!res.ok) throw new Error('Failed to fetch user')
    return res.json()
  },

  update: async (data: { username?: string; avatar?: string }): Promise<void> => {
    const res = await fetch('/api/users/me', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to update user')
  },
}
*/
