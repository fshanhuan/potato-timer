import React, { useState, useRef, useEffect } from 'react'
import {
  Card,
  Input,
  Button,
  List,
  Space,
  Tag,
  Empty,
  Spin,
  message,
} from 'antd'
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { AIMessage, FocusPlan } from '@/types'
import { formatDate, formatDateTime } from '@/utils/timeFormat'
import { useAppStore } from '@/store'
import './AIPage.css'

const { TextArea } = Input

const mockPlans: FocusPlan[] = [
  {
    plan_id: 1,
    title: '本周学习计划',
    start_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    end_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    selected_dates: [
      formatDate(new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)),
      formatDate(new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)),
      formatDate(new Date(Date.now() - 1 * 24 * 60 * 60 * 1000)),
      formatDate(new Date()),
      formatDate(new Date(Date.now() + 1 * 24 * 60 * 60 * 1000)),
      formatDate(new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)),
      formatDate(new Date(Date.now() + 3 * 24 * 60 * 60 * 1000)),
    ],
    daily_focus_minutes: 60,
    total_focus_minutes: 420,
    created_at: new Date().toISOString(),
  },
]

export const AIPage: React.FC = () => {
  const { theme } = useAppStore()

  const [messages, setMessages] = useState<AIMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        '你好！我是你的AI助手。请告诉我你的目标或需要完成的事情，我会为你生成合理的计划表。',
      timestamp: new Date().toISOString(),
    },
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [plans, setPlans] = useState<FocusPlan[]>(mockPlans)
  const [selectedPlan, setSelectedPlan] = useState<FocusPlan | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!inputValue.trim()) return

    const userMessage: AIMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    setTimeout(() => {
      const aiResponse: AIMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateAIResponse(inputValue),
        timestamp: new Date().toISOString(),
        plan: shouldGeneratePlan(inputValue)
          ? generateMockPlan(inputValue)
          : undefined,
      }

      setMessages((prev) => [...prev, aiResponse])
      setLoading(false)

      if (aiResponse.plan) {
        message.success('已为您生成计划表，可在左侧查看')
        setPlans((prev) => [...prev, aiResponse.plan!])
        setSelectedPlan(aiResponse.plan!)
      }
    }, 1500)
  }

  const generateAIResponse = (input: string): string => {
    if (input.length < 10) {
      return '请提供更详细的描述，包括具体的事件内容和时间安排，这样我可以为你生成更精准的计划表。'
    }

    if (!hasTimeInfo(input)) {
      return '我注意到你的描述中缺少具体的时间安排。请告诉我：\n• 任务的截止日期是什么时候？\n• 你计划每天投入多少时间？\n• 有哪些重要的里程碑？'
    }

    return `好的，根据你的描述"${input.substring(0, 30)}..."，我已为你生成了一个初步的计划表。你可以查看左侧的计划列表，手动调整各项内容。如有需要修改的地方，可以继续与我对话。`
  }

  const shouldGeneratePlan = (input: string): boolean => {
    return input.length >= 10 && hasTimeInfo(input)
  }

  const hasTimeInfo = (input: string): boolean => {
    const timeKeywords = ['天', '周', '月', '日', '日期', '截止', '完成', '时间']
    return timeKeywords.some((keyword) => input.includes(keyword))
  }

  const generateMockPlan = (input: string): FocusPlan => {
    const startDate = new Date()
    const endDate = new Date(startDate.getTime() + 6 * 24 * 60 * 60 * 1000)

    return {
      plan_id: Date.now(),
      title: `${input.substring(0, 15)}...计划`,
      start_date: startDate.toISOString(),
      end_date: endDate.toISOString(),
      selected_dates: Array.from({ length: 7 }, (_, i) =>
        formatDate(new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000))
      ),
      daily_focus_minutes: 45,
      total_focus_minutes: 315,
      created_at: new Date().toISOString(),
    }
  }

  const handleDeletePlan = (planId: number) => {
    setPlans((prev) => prev.filter((p) => p.plan_id !== planId))
    if (selectedPlan?.plan_id === planId) {
      setSelectedPlan(null)
    }
    message.success('计划已删除')
  }

  const handleEditPlan = (plan: FocusPlan) => {
    message.info('编辑功能开发中')
  }

  const renderPlanDetail = (plan: FocusPlan) => {
    return (
      <div className="plan-detail">
        <div className="plan-header">
          <h3>{plan.title}</h3>
          <Space>
            <Button
              icon={<EditOutlined />}
              size="small"
              onClick={() => handleEditPlan(plan)}
            >
              编辑
            </Button>
            <Button
              icon={<DeleteOutlined />}
              size="small"
              danger
              onClick={() => handleDeletePlan(plan.plan_id)}
            >
              删除
            </Button>
          </Space>
        </div>

        <div className="plan-info">
          <p>
            <strong>时间范围：</strong>
            {formatDate(plan.start_date)} ~ {formatDate(plan.end_date)}
          </p>
          <p>
            <strong>每日专注：</strong> {plan.daily_focus_minutes} 分钟
          </p>
          <p>
            <strong>总计划时长：</strong> {plan.total_focus_minutes} 分钟
          </p>
          <p>
            <strong>选中日期：</strong> {plan.selected_dates.length} 天
          </p>
        </div>

        <div className="plan-dates">
          <h4>选中日期</h4>
          <div className="date-tags">
            {plan.selected_dates.slice(0, 7).map((date) => (
              <Tag key={date}>{date}</Tag>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="ai-page">
      <div className="ai-page-left">
        <Card
          title={
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span>已有计划表</span>
              <Button icon={<PlusOutlined />} size="small" type="primary">
                新建
              </Button>
            </div>
          }
          className="plans-card"
        >
          {plans.length === 0 ? (
            <Empty
              description="暂无计划表"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <List
              dataSource={plans}
              renderItem={(plan) => (
                <List.Item
                  className={`plan-item ${selectedPlan?.plan_id === plan.plan_id ? 'selected' : ''}`}
                  onClick={() => setSelectedPlan(plan)}
                  actions={[
                    <Button
                      key="edit"
                      icon={<EditOutlined />}
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleEditPlan(plan)
                      }}
                    />,
                    <Button
                      key="delete"
                      icon={<DeleteOutlined />}
                      size="small"
                      danger
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeletePlan(plan.plan_id)
                      }}
                    />,
                  ]}
                >
                  <List.Item.Meta
                    title={plan.title}
                    description={
                      <span>
                        {formatDate(plan.start_date)} ~{' '}
                        {formatDate(plan.end_date)} · {plan.daily_focus_minutes}
                        分钟/天
                      </span>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Card>

        {selectedPlan && (
          <Card title="计划详情" className="plan-detail-card">
            {renderPlanDetail(selectedPlan)}
          </Card>
        )}
      </div>

      <div className="ai-page-right">
        <Card className="chat-card">
          <div className="chat-header">
            <RobotOutlined />
            <span>AI 助手</span>
            <Tag color="blue">在线</Tag>
          </div>

          <div className="chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                </div>
                <div className="message-content">
                  <div className="message-text">{msg.content}</div>
                  {msg.plan && (
                    <Card size="small" className="message-plan">
                      <p>
                        <strong>已生成计划：</strong>
                        {msg.plan.title}
                      </p>
                      <p>
                        时间范围：{formatDate(msg.plan.start_date)} ~{' '}
                        {formatDate(msg.plan.end_date)}
                      </p>
                      <Button
                        type="primary"
                        size="small"
                        style={{ marginTop: 8 }}
                      >
                        导入计划
                      </Button>
                    </Card>
                  )}
                  <div className="message-time">
                    {formatDateTime(msg.timestamp)}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-avatar">
                  <RobotOutlined />
                </div>
                <div className="message-content">
                  <Spin size="small" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input">
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="请描述您的目标或需要完成的事情..."
              autoSize={{ minRows: 2, maxRows: 4 }}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={loading}
              style={{ marginTop: 12 }}
              block
            >
              发送
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}
