import { create } from 'zustand'
import {
  Task,
  TimerMode,
  TaskStatus,
  PomodoroPhase,
  ThemeColor,
  UserSettings,
  SortType,
  FilterType,
} from '@/types'
import { mockAPI } from '@/api'
import { userSettingsStorage, themeStorage, backgroundStorage } from '@/utils/storage'

interface TimerStore {
  mode: TimerMode
  phase: PomodoroPhase | 'idle'
  state: 'idle' | 'running' | 'paused' | 'finished'
  remaining: number
  total: number
  elapsed: number
  taskId: number | null
}

interface AppState {
  // 用户设置
  settings: UserSettings
  updateSettings: (settings: Partial<UserSettings>) => void

  // 任务列表
  tasks: Task[]
  filteredTasks: Task[]
  searchKeyword: string
  sortType: SortType
  filterType: FilterType
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  removeTask: (taskId: number) => void
  updateTask: (taskId: number, data: Partial<Task>) => void
  setSearchKeyword: (keyword: string) => void
  setSortType: (type: SortType) => void
  setFilterType: (type: FilterType) => void
  refreshTasks: () => Promise<void>
  applyFiltersAndSort: () => void

  // 计时器状态
  timer: TimerStore
  setTimerState: (state: Partial<TimerStore>) => void
  startTimer: (taskId: number, mode: TimerMode) => void
  pauseTimer: () => void
  resumeTimer: () => void
  completeTimer: () => void
  stopTimer: () => void
  nextPhase: () => void
  tickTimer: () => void

  // 当前选中的任务
  currentTask: Task | null
  setCurrentTask: (task: Task | null) => void

  // 紧急提醒
  showHighAlert: boolean
  showCriticalAlert: boolean
  alertTask: Task | null
  setShowHighAlert: (show: boolean) => void
  setShowCriticalAlert: (show: boolean) => void
  setAlertTask: (task: Task | null) => void
  checkReminders: () => void

  // 主题
  theme: ThemeColor
  setTheme: (theme: ThemeColor) => void

  // 背景图
  background: string
  setBackground: (background: string) => void

  // 页面导航
  currentPage: 'tasks' | 'settings' | 'ai' | 'stats'
  setCurrentPage: (page: 'tasks' | 'settings' | 'ai' | 'stats') => void
}

export const useAppStore = create<AppState>((set, get) => ({
  // ========== 用户设置 ==========
  settings: userSettingsStorage.get(),
  updateSettings: (settings) => {
    set((state) => ({
      settings: { ...state.settings, ...settings },
    }))
    userSettingsStorage.set(settings)
  },

  // ========== 任务列表 ==========
  tasks: [],
  filteredTasks: [],
  searchKeyword: '',
  sortType: 'due_date',
  filterType: 'all',
  setTasks: (tasks) => {
    set({ tasks })
    get().applyFiltersAndSort()
  },
  addTask: (task) => {
    set((state) => ({ tasks: [...state.tasks, task] }))
    get().applyFiltersAndSort()
  },
  removeTask: (taskId) => {
    set((state) => ({
      tasks: state.tasks.filter((t) => t.task_id !== taskId),
    }))
    get().applyFiltersAndSort()
  },
  updateTask: (taskId, data) => {
    set((state) => ({
      tasks: state.tasks.map((t) => (t.task_id === taskId ? { ...t, ...data } : t)),
    }))
    get().applyFiltersAndSort()
  },
  setSearchKeyword: (keyword) => {
    set({ searchKeyword: keyword })
    get().applyFiltersAndSort()
  },
  setSortType: (type) => {
    set({ sortType: type })
    get().applyFiltersAndSort()
  },
  setFilterType: (type) => {
    set({ filterType: type })
    get().applyFiltersAndSort()
  },
  refreshTasks: async () => {
    const tasks = await mockAPI.getTasks()
    set({ tasks })
    get().applyFiltersAndSort()
  },
  applyFiltersAndSort: () => {
    const state = get()
    let filtered = [...state.tasks]

    // 搜索过滤
    if (state.searchKeyword) {
      const keyword = state.searchKeyword.toLowerCase()
      filtered = filtered.filter(
        (t) =>
          t.title.toLowerCase().includes(keyword) ||
          t.description.toLowerCase().includes(keyword)
      )
    }

    // 状态过滤
    if (state.filterType !== 'all') {
      filtered = filtered.filter((t) => t.status === state.filterType)
    }

    // 排序
    if (state.sortType === 'due_date') {
      filtered.sort((a, b) => {
        if (!a.due_date) return 1
        if (!b.due_date) return -1
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
      })
    } else if (state.sortType === 'priority') {
      filtered.sort((a, b) => {
        if (a.importance !== b.importance) {
          return b.importance - a.importance
        }
        if (!a.due_date) return 1
        if (!b.due_date) return -1
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
      })
    }

    set({ filteredTasks: filtered })
  },

  // ========== 计时器状态 ==========
  timer: {
    mode: TimerMode.POMODORO,
    phase: 'idle',
    state: 'idle',
    remaining: 25 * 60,
    total: 25 * 60,
    elapsed: 0,
    taskId: null,
  },
  setTimerState: (newState) => {
    set((state) => ({
      timer: { ...state.timer, ...newState },
    }))
  },
  startTimer: (taskId, mode) => {
    const total = mode === TimerMode.POMODORO ? 25 * 60 : 45 * 60
    set({
      timer: {
        mode,
        phase: PomodoroPhase.WORK,
        state: 'running',
        remaining: total,
        total,
        elapsed: 0,
        taskId,
      },
      currentPage: 'tasks',
    })
  },
  pauseTimer: () => {
    set((state) => ({
      timer: { ...state.timer, state: 'paused' },
    }))
  },
  resumeTimer: () => {
    set((state) => ({
      timer: { ...state.timer, state: 'running' },
    }))
  },
  completeTimer: () => {
    set((state) => ({
      timer: { ...state.timer, state: 'finished' },
    }))
  },
  stopTimer: () => {
    const taskId = get().timer.taskId
    set({
      timer: {
        mode: TimerMode.POMODORO,
        phase: 'idle',
        state: 'idle',
        remaining: 25 * 60,
        total: 25 * 60,
        elapsed: 0,
        taskId: null,
      },
      currentTask: null,
    })
    if (taskId) {
      get().updateTask(taskId, { status: TaskStatus.COMPLETED })
    }
  },
  nextPhase: () => {
    const state = get()
    const currentPhase = state.timer.phase
    let nextPhase: PomodoroPhase | 'idle' = 'idle' as const
    let total = 25 * 60

    if (currentPhase === PomodoroPhase.WORK) {
      const completedPomodoros = state.timer.elapsed / (25 * 60)
      const pomodoroCount = Math.floor(completedPomodoros) + 1
      if (pomodoroCount % 4 === 0) {
        nextPhase = PomodoroPhase.LONG_BREAK
        total = 15 * 60
      } else {
        nextPhase = PomodoroPhase.SHORT_BREAK
        total = 5 * 60
      }
    } else {
      nextPhase = PomodoroPhase.WORK
      total = 25 * 60
    }

    set({
      timer: {
        ...state.timer,
        phase: nextPhase,
        remaining: total,
        total,
        elapsed: 0,
        state: 'running',
      },
    })
  },
  tickTimer: () => {
    set((state) => {
      if (state.timer.state !== 'running') {
        return state
      }

      const newElapsed = state.timer.elapsed + 1
      const newRemaining = Math.max(0, state.timer.total - newElapsed)

      if (newRemaining <= 0) {
        return {
          timer: {
            ...state.timer,
            elapsed: newElapsed,
            remaining: 0,
            state: 'finished',
          },
        }
      }

      return {
        timer: {
          ...state.timer,
          elapsed: newElapsed,
          remaining: newRemaining,
        },
      }
    })
  },

  // ========== 当前选中任务 ==========
  currentTask: null,
  setCurrentTask: (task) => {
    set({ currentTask: task })
  },

  // ========== 紧急提醒 ==========
  showHighAlert: false,
  showCriticalAlert: false,
  alertTask: null,
  setShowHighAlert: (show) => {
    set({ showHighAlert: show })
  },
  setShowCriticalAlert: (show) => {
    set({ showCriticalAlert: show })
  },
  setAlertTask: (task) => {
    set({ alertTask: task })
  },
  checkReminders: () => {
    const now = new Date()
    const tasks = get().tasks.filter(
      (t) =>
        t.status === TaskStatus.PENDING &&
        t.due_date &&
        new Date(t.due_date) > now
    )

    for (const task of tasks) {
      const minutesUntilDue =
        (new Date(task.due_date!).getTime() - now.getTime()) / (1000 * 60)

      if (minutesUntilDue <= 15 && task.importance >= 3) {
        set({
          showCriticalAlert: true,
          alertTask: task,
        })
        break
      } else if (minutesUntilDue <= 60 && task.importance >= 3) {
        set({
          showHighAlert: true,
          alertTask: task,
        })
      }
    }
  },

  // ========== 主题 ==========
  theme: themeStorage.get(),
  setTheme: (theme) => {
    set({ theme })
    themeStorage.set(theme)
  },

  // ========== 背景图 ==========
  background: backgroundStorage.get(),
  setBackground: (background) => {
    set({ background })
    backgroundStorage.set(background)
  },

  // ========== 页面导航 ==========
  currentPage: 'tasks',
  setCurrentPage: (page) => {
    set({ currentPage: page })
  },
}))
