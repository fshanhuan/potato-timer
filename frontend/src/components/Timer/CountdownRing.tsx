import React from 'react'
import { THEME_COLORS, getStateColor, TimerState } from '@/config/theme'
import './CountdownRing.css'

interface CountdownRingProps {
  remaining: number
  total: number
  theme: 'BLUE' | 'PURPLE' | 'GREEN' | 'ORANGE'
  phase: 'work' | 'short_break' | 'long_break' | 'idle' | 'paused'
  paused?: boolean
}

export const CountdownRing: React.FC<CountdownRingProps> = ({
  remaining,
  total,
  theme,
  phase,
  paused = false,
}) => {
  const themeConfig = THEME_COLORS[theme]
  const progress = total > 0 ? (total - remaining) / total : 0
  const circumference = 2 * Math.PI * 120
  const offset = circumference * (1 - progress)

  const getColor = (): string => {
    if (paused) return themeConfig.paused
    return getStateColor(phase as TimerState, theme)
  }

  const color = getColor()

  return (
    <div className="countdown-ring">
      <svg width="280" height="280" viewBox="0 0 280 280">
        <circle
          cx="140"
          cy="140"
          r="120"
          fill="none"
          stroke="#f0f0f0"
          strokeWidth="8"
          strokeLinecap="round"
        />
        <circle
          cx="140"
          cy="140"
          r="120"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 140 140)"
          className="progress-circle"
          style={{
            transition: 'stroke-dashoffset 1s linear, stroke 0.3s ease',
          }}
        />
      </svg>
    </div>
  )
}
