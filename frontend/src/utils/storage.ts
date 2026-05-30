import { UserSettings, ThemeColor, ImagePaths, AudioPaths } from '@/types'

const STORAGE_KEYS = {
  USER_SETTINGS: 'focus_timer_user_settings',
  IMAGE_PATHS: 'focus_timer_image_paths',
  AUDIO_PATHS: 'focus_timer_audio_paths',
  THEME_COLOR: 'focus_timer_theme_color',
  BACKGROUND: 'focus_timer_background',
  ALERT_SOUND: 'focus_timer_alert_sound',
  ENABLE_ALERT: 'focus_timer_enable_alert',
  ENABLE_SOUND: 'focus_timer_enable_sound',
  ALERT_MINUTES: 'focus_timer_alert_minutes',
} as const

const DEFAULT_SETTINGS: UserSettings = {
  nickname: '',
  avatar: '/assets/images/default-avatar.jpg',
  theme: 'BLUE',
  background: '',
  alertSound: '/assets/audio/alert.mp3',
  enableAlert: true,
  enableSound: true,
  alertMinutes: 15,
}

const DEFAULT_IMAGE_PATHS: ImagePaths = {
  userAvatar: '/assets/images/default-avatar.jpg',
  alertIcon: '/assets/icons/alert-icon.png',
  timerIcon: '/assets/icons/timer-icon.png',
  shortBreakIcon: '/assets/icons/short-break.png',
  longBreakIcon: '/assets/icons/long-break.png',
}

const DEFAULT_AUDIO_PATHS: AudioPaths = {
  sound1: '/assets/audio/sound1.mp3',
  sound2: '/assets/audio/sound2.mp3',
  sound3: '/assets/audio/sound3.mp3',
  alert: '/assets/audio/alert.mp3',
}

const storage = {
  get: <T>(key: string, defaultValue: T): T => {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch (error) {
      console.error(`Error reading from localStorage:`, error)
      return defaultValue
    }
  },

  set: <T>(key: string, value: T): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error(`Error writing to localStorage:`, error)
    }
  },

  remove: (key: string): void => {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error(`Error removing from localStorage:`, error)
    }
  },
}

export const userSettingsStorage = {
  get: (): UserSettings => {
    return storage.get(STORAGE_KEYS.USER_SETTINGS, DEFAULT_SETTINGS)
  },

  set: (settings: Partial<UserSettings>): void => {
    const current = userSettingsStorage.get()
    const updated = { ...current, ...settings }
    storage.set(STORAGE_KEYS.USER_SETTINGS, updated)
  },

  reset: (): void => {
    storage.set(STORAGE_KEYS.USER_SETTINGS, DEFAULT_SETTINGS)
  },
}

export const imagePathsStorage = {
  get: (): ImagePaths => {
    return storage.get(STORAGE_KEYS.IMAGE_PATHS, DEFAULT_IMAGE_PATHS)
  },

  set: (paths: Partial<ImagePaths>): void => {
    const current = imagePathsStorage.get()
    const updated = { ...current, ...paths }
    storage.set(STORAGE_KEYS.IMAGE_PATHS, updated)
  },
}

export const audioPathsStorage = {
  get: (): AudioPaths => {
    return storage.get(STORAGE_KEYS.AUDIO_PATHS, DEFAULT_AUDIO_PATHS)
  },

  set: (paths: Partial<AudioPaths>): void => {
    const current = audioPathsStorage.get()
    const updated = { ...current, ...paths }
    storage.set(STORAGE_KEYS.AUDIO_PATHS, updated)
  },
}

export const themeStorage = {
  get: (): ThemeColor => {
    return storage.get(STORAGE_KEYS.THEME_COLOR, 'BLUE' as ThemeColor)
  },

  set: (theme: ThemeColor): void => {
    storage.set(STORAGE_KEYS.THEME_COLOR, theme)
  },
}

export const backgroundStorage = {
  get: (): string => {
    return storage.get(STORAGE_KEYS.BACKGROUND, '')
  },

  set: (background: string): void => {
    storage.set(STORAGE_KEYS.BACKGROUND, background)
  },
}

export const alertSoundStorage = {
  get: (): string => {
    return storage.get(STORAGE_KEYS.ALERT_SOUND, '/assets/audio/alert.mp3')
  },

  set: (sound: string): void => {
    storage.set(STORAGE_KEYS.ALERT_SOUND, sound)
  },
}

export const enableAlertStorage = {
  get: (): boolean => {
    return storage.get(STORAGE_KEYS.ENABLE_ALERT, true)
  },

  set: (enabled: boolean): void => {
    storage.set(STORAGE_KEYS.ENABLE_ALERT, enabled)
  },
}

export const enableSoundStorage = {
  get: (): boolean => {
    return storage.get(STORAGE_KEYS.ENABLE_SOUND, true)
  },

  set: (enabled: boolean): void => {
    storage.set(STORAGE_KEYS.ENABLE_SOUND, enabled)
  },
}

export const alertMinutesStorage = {
  get: (): number => {
    return storage.get(STORAGE_KEYS.ALERT_MINUTES, 15)
  },

  set: (minutes: number): void => {
    storage.set(STORAGE_KEYS.ALERT_MINUTES, minutes)
  },
}

export const clearAllStorage = (): void => {
  try {
    Object.values(STORAGE_KEYS).forEach((key) => {
      localStorage.removeItem(key)
    })
  } catch (error) {
    console.error('Error clearing localStorage:', error)
  }
}
