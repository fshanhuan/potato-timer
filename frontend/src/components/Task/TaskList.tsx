import React, { useEffect } from 'react'
import { Input, Select, Button, Space, Empty, Spin } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { TaskCreateModal } from './TaskCreateModal'
import { TaskCard } from './TaskCard'
import { SortType, Task } from '@/types'
import { useAppStore } from '@/store'
import './TaskList.css'

export const TaskList: React.FC = () => {
  const {
    filteredTasks,
    searchKeyword,
    sortType,
    setSearchKeyword,
    setSortType,
    refreshTasks,
    startTimer,
    setCurrentTask,
  } = useAppStore()

  const [createModalVisible, setCreateModalVisible] = React.useState(false)
  const [loading, setLoading] = React.useState(false)

  useEffect(() => {
    const loadTasks = async () => {
      setLoading(true)
      await refreshTasks()
      setLoading(false)
    }
    loadTasks()
  }, [])

  const handleSortChange = (value: SortType) => {
    setSortType(value)
  }

  const handleStartTask = (task: Task) => {
    setCurrentTask(task)
    startTimer(task.task_id, task.mode)
  }

  return (
    <div className="task-list">
      <div className="task-list-header">
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
          size="large"
        >
          新建待办事项
        </Button>

        <Space size="middle">
          <Input
            placeholder="搜索事件..."
            prefix={<SearchOutlined />}
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />

          <Select
            value={sortType}
            onChange={handleSortChange}
            style={{ width: 150 }}
          >
            <Select.Option value="due_date">按截止时间</Select.Option>
            <Select.Option value="priority">按优先级</Select.Option>
          </Select>
        </Space>
      </div>

      <div className="task-list-content">
        {loading ? (
          <div className="loading-container">
            <Spin size="large" />
          </div>
        ) : filteredTasks.length === 0 ? (
          <Empty
            description={searchKeyword ? '没有找到匹配的任务' : '暂无待办事项'}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <div className="task-cards">
            {filteredTasks.map((task) => (
              <TaskCard
                key={task.task_id}
                task={task}
                onStart={() => handleStartTask(task)}
              />
            ))}
          </div>
        )}
      </div>

      <TaskCreateModal
        visible={createModalVisible}
        onClose={() => setCreateModalVisible(false)}
        onCreated={refreshTasks}
      />
    </div>
  )
}
