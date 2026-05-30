// ==================== 枚举类型 ====================

export enum TimerMode {
  POMODORO = 0,
  COUNTDOWN = 1,
  COUNTUP = 2,
}

export enum TimerState {
  IDLE = 'idle',
  RUNNING = 'running',
  PAUSED = 'paused',
  FINISHED = 'finished',
}

export enum PomodoroPhase {
  WORK = 'work',
  SHORT_BREAK = 'short_break',
  LONG_BREAK = 'long_break',
}

export enum TaskStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  ABANDONED = 'abandoned',
}

export enum ImportanceLevel {
  LOW = 1,
  MEDIUM = 2,
  HIGH = 3,
  CRITICAL = 4,
}

export type ThemeColor = 'BLUE' | 'PURPLE' | 'GREEN' | 'ORANGE'

// ==================== 任务相关类型 ====================

export interface Task {
  task_id: number
  title: string
  description: string
  motto: string
  due_date: string | null
  importance: ImportanceLevel
  planned_minutes: number
  reminder_at: string | null
  mode: TimerMode
  status: TaskStatus
  created_at: string
  completed_at: string | null
  total_focused_minutes: number
}

export interface CreateTaskDTO {
  title: string
  description: string
  due_date: string | null
  mode: TimerMode
  motto?: string
  importance?: ImportanceLevel
  planned_minutes?: number
  reminder_at?: string | null
}

export interface TaskReminder {
  task_id: number
  title: string
  importance: string
  due_date: string | null
  minutes_left: number | null
  reminder_degree: number
  level: 'none' | 'low' | 'medium' | 'high' | 'expired'
}

// ==================== 计时器相关类型 ====================

export interface TimerDisplay {
  minutes: number
  seconds: number
  formatted: string
}

export interface TimerStateResponse {
  status: PomodoroPhase | 'paused' | 'idle'
  remaining: number
  elapsed: number
  total: number
}

export interface PomodoroProgress {
  current_phase: string
  completed_pomodoros: number
  pomodoros_per_round: number
  next_is_long_break: boolean
  display_time: string
  state: string
}

// ==================== 统计相关类型 ====================

export interface SessionRecord {
  record_id: number
  task_id: number
  user_id: number
  mode: string
  started_at: string
  ended_at: string
  focused_seconds: number
  focused_minutes: number
  is_completed: boolean
  note: string | null
}

export interface DailyStats {
  date: string
  total_focused_minutes: number
  total_sessions: number
  completed_sessions: number
  pomodoro_count: number
}

export interface TaskReport {
  task_id: number
  title: string
  due_date: string | null
  planned_minutes: number
  actual_minutes: number
  difference_minutes: number
  status: string
  is_overdue: boolean
}

export interface TimeUsageReport {
  start_date: string
  end_date: string
  planned_minutes: number
  actual_minutes: number
  difference_minutes: number
  time_waste_minutes: number
  interrupted_minutes: number
  overdue_unfinished: number
  tasks: TaskReport[]
  suggestions: string[]
}

// ==================== 计划相关类型 ====================

export interface DayPlan {
  date: string
  total_planned_minutes: number
  items: DayPlanItem[]
}

export interface DayPlanItem {
  task_id: number
  title: string
  importance: string
  planned_minutes: number
  start_time: string
  end_time: string
  due_date: string | null
  status: string
}

export interface FocusPlan {
  plan_id: number
  title: string
  start_date: string
  end_date: string
  selected_dates: string[]
  daily_focus_minutes: number
  total_focus_minutes: number
  created_at: string
}

export interface CreatePlanDTO {
  title: string
  start_date: string
  end_date: string
  daily_focus_minutes?: number
  total_focus_minutes?: number
  selected_dates?: string[]
}

export interface PlanProgress {
  plan_id: number
  title: string
  start_date: string
  end_date: string
  selected_dates: string[]
  daily_focus_minutes: number
  total_focus_minutes: number
  actual_minutes: number
  expected_minutes_by_query_date: number
  gap_minutes: number
  remaining_minutes: number
  required_daily_minutes: number
  progress_percent: number
  expected_progress_percent: number
  status: 'completed' | 'on_track' | 'behind'
  status_message: string
  daily_reports: DailyReport[]
}

export interface DailyReport {
  date: string
  planned_minutes: number
  actual_minutes: number
  difference_minutes: number
  is_completed: boolean
}

// ==================== 用户相关类型 ====================

export interface User {
  user_id: number
  username: string
  avatar: string
  statistics_path?: string
  plans_path?: string
  tasks_path?: string
}

export interface UserSettings {
  nickname: string
  avatar: string
  theme: ThemeColor
  background: string
  alertSound: string
  enableAlert: boolean
  enableSound: boolean
  alertMinutes: number
}

// ==================== AI相关类型 ====================

export interface AIMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  plan?: FocusPlan
}

export interface AIResponse {
  message: string
  plan?: FocusPlan
  needsClarification?: boolean
}

// ==================== 排序和筛选类型 ====================

export type SortType = 'due_date' | 'priority'
export type FilterType = 'all' | 'pending' | 'completed' | 'abandoned'

// ==================== 通知类型 ====================

export interface AlertNotification {
  type: 'high' | 'critical'
  task: TaskReminder
  message: string
}

// ==================== 本地数据存储类型 ====================

export interface ImagePaths {
  userAvatar: string
  alertIcon: string
  timerIcon: string
  shortBreakIcon: string
  longBreakIcon: string
}

export interface AudioPaths {
  sound1: string
  sound2: string
  sound3: string
  alert: string
}
