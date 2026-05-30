// 主题配置

export type ThemeColor = 'BLUE' | 'PURPLE' | 'GREEN' | 'ORANGE'

export interface ThemeConfig {
  name: ThemeColor
  displayName: string
  primary: string
  secondary: string
  work: string
  shortBreak: string
  longBreak: string
  paused: string
}

export const THEME_COLORS: Record<ThemeColor, ThemeConfig> = {
  BLUE: {
    name: 'BLUE',
    displayName: '蓝色',
    primary: '#1890ff',
    secondary: '#40a9ff',
    work: '#1890ff',
    shortBreak: '#52c41a',
    longBreak: '#faad14',
    paused: '#bfbfbf',
  },
  PURPLE: {
    name: 'PURPLE',
    displayName: '紫色',
    primary: '#722ed1',
    secondary: '#9254de',
    work: '#722ed1',
    shortBreak: '#13c2c2',
    longBreak: '#eb2f96',
    paused: '#bfbfbf',
  },
  GREEN: {
    name: 'GREEN',
    displayName: '绿色',
    primary: '#52c41a',
    secondary: '#73d13d',
    work: '#52c41a',
    shortBreak: '#1890ff',
    longBreak: '#faad14',
    paused: '#bfbfbf',
  },
  ORANGE: {
    name: 'ORANGE',
    displayName: '橙色',
    primary: '#fa8c16',
    secondary: '#ffa940',
    work: '#fa8c16',
    shortBreak: '#52c41a',
    longBreak: '#f5222d',
    paused: '#bfbfbf',
  },
}

export const getThemeConfig = (theme: ThemeColor = 'BLUE'): ThemeConfig => {
  return THEME_COLORS[theme]
}

export type TimerState = 'work' | 'short_break' | 'long_break' | 'paused' | 'idle'

export const getStateColor = (state: TimerState, theme: ThemeColor = 'BLUE'): string => {
  const config = getThemeConfig(theme)
  switch (state) {
    case 'work':
      return config.work
    case 'short_break':
      return config.shortBreak
    case 'long_break':
      return config.longBreak
    case 'paused':
      return config.paused
    default:
      return config.primary
  }
}

export const BUILT_IN_BACKGROUNDS = [
  {
    id: 'bg1',
    name: '背景图1',
    path: '/assets/images/bg1.jpg',
  },
  {
    id: 'bg2',
    name: '背景图2',
    path: '/assets/images/bg2.jpg',
  },
  {
    id: 'none',
    name: '无背景',
    path: '',
  },
]

export const BUILT_IN_SOUNDS = [
  {
    id: 'sound1',
    name: '提示音1',
    path: '/assets/audio/sound1.mp3',
  },
  {
    id: 'sound2',
    name: '提示音2',
    path: '/assets/audio/sound2.mp3',
  },
  {
    id: 'sound3',
    name: '提示音3',
    path: '/assets/audio/sound3.mp3',
  },
  {
    id: 'alert',
    name: '紧急提醒音',
    path: '/assets/audio/alert.mp3',
  },
]
