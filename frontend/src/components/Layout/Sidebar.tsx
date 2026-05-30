import React from 'react'
import { Menu } from 'antd'
import {
  CheckSquareOutlined,
  UserOutlined,
  RobotOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useAppStore } from '@/store'
import { THEME_COLORS } from '@/config/theme'
import './Sidebar.css'

interface SidebarProps {
  className?: string
}

export const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const { currentPage, setCurrentPage, theme } = useAppStore()
  const themeConfig = THEME_COLORS[theme]

  const menuItems = [
    {
      key: 'tasks',
      icon: <CheckSquareOutlined />,
      label: '待办事项',
    },
    {
      key: 'settings',
      icon: <UserOutlined />,
      label: '用户设置',
    },
    {
      key: 'ai',
      icon: <RobotOutlined />,
      label: 'AI 计划',
    },
    {
      key: 'stats',
      icon: <BarChartOutlined />,
      label: '数据统计',
    },
  ]

  return (
    <div
      className={`sidebar ${className || ''}`}
      style={
        {
          '--primary-color': themeConfig.primary,
          '--secondary-color': themeConfig.secondary,
        } as React.CSSProperties
      }
    >
      <div className="sidebar-logo">
        <h2>专注计时器</h2>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[currentPage]}
        items={menuItems}
        onClick={({ key }) => setCurrentPage(key as 'tasks' | 'settings' | 'ai' | 'stats')}
        className="sidebar-menu"
      />
    </div>
  )
}
