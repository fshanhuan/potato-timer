let audioElement: HTMLAudioElement | null = null
let isPlaying = false

export const playAudio = (src: string, volume: number = 0.5): Promise<void> => {
  return new Promise((resolve, reject) => {
    try {
      if (audioElement && isPlaying) {
        audioElement.pause()
        audioElement.currentTime = 0
      }

      audioElement = new Audio(src)
      audioElement.volume = volume
      isPlaying = true

      audioElement.onended = () => {
        isPlaying = false
        resolve()
      }

      audioElement.onerror = () => {
        isPlaying = false
        reject(new Error('Failed to play audio'))
      }

      audioElement.play().catch((err) => {
        isPlaying = false
        reject(err)
      })
    } catch (error) {
      isPlaying = false
      reject(error)
    }
  })
}

export const stopAudio = (): void => {
  if (audioElement && isPlaying) {
    audioElement.pause()
    audioElement.currentTime = 0
    isPlaying = false
  }
}

export const getAudioPlayingState = (): boolean => {
  return isPlaying
}

export const showNotification = (
  title: string,
  body: string,
  icon?: string
): void => {
  if (!('Notification' in window)) {
    console.log('This browser does not support desktop notification')
    return
  }

  if (Notification.permission === 'granted') {
    new Notification(title, { body, icon })
  } else if (Notification.permission !== 'denied') {
    Notification.requestPermission().then((permission) => {
      if (permission === 'granted') {
        new Notification(title, { body, icon })
      }
    })
  }
}

export const requestNotificationPermission = (): Promise<NotificationPermission> => {
  if (!('Notification' in window)) {
    return Promise.reject(new Error('Notification not supported'))
  }

  if (Notification.permission === 'granted') {
    return Promise.resolve('granted')
  }

  if (Notification.permission === 'denied') {
    return Promise.resolve('denied')
  }

  return Notification.requestPermission()
}
