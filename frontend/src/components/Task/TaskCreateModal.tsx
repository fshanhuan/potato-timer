import React from 'react'
import { Modal, Form, Input, DatePicker, Select, InputNumber, Button } from 'antd'
import { TimerMode, ImportanceLevel } from '@/types'
import { mockAPI } from '@/api'

interface TaskCreateModalProps {
  visible: boolean
  onClose: () => void
  onCreated: () => void
}

export const TaskCreateModal: React.FC<TaskCreateModalProps> = ({
  visible,
  onClose,
  onCreated,
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = React.useState(false)

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      await mockAPI.createTask({
        title: values.title,
        description: values.description || '',
        due_date: values.due_date ? values.due_date.toISOString() : null,
        mode: values.mode || TimerMode.POMODORO,
        importance: values.importance || ImportanceLevel.MEDIUM,
        planned_minutes: values.planned_minutes || 25,
        reminder_at: null,
      })

      form.resetFields()
      onClose()
      onCreated()
    } catch (error) {
      console.error('Failed to create task:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title="新建待办事项"
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          创建
        </Button>,
      ]}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          mode: TimerMode.POMODORO,
          importance: ImportanceLevel.MEDIUM,
          planned_minutes: 25,
        }}
      >
        <Form.Item
          label="标题"
          name="title"
          rules={[{ required: true, message: '请输入任务标题' }]}
        >
          <Input placeholder="请输入任务标题" />
        </Form.Item>

        <Form.Item label="内容描述" name="description">
          <Input.TextArea rows={3} placeholder="请输入任务详细描述（可选）" />
        </Form.Item>

        <Form.Item label="截止日期" name="due_date">
          <DatePicker
            showTime
            placeholder="选择截止日期和时间（可选）"
            style={{ width: '100%' }}
            format="YYYY-MM-DD HH:mm"
          />
        </Form.Item>

        <Form.Item label="重要程度" name="importance">
          <Select placeholder="选择重要程度">
            <Select.Option value={ImportanceLevel.LOW}>普通</Select.Option>
            <Select.Option value={ImportanceLevel.MEDIUM}>重要</Select.Option>
            <Select.Option value={ImportanceLevel.HIGH}>很重要</Select.Option>
            <Select.Option value={ImportanceLevel.CRITICAL}>
              紧急且重要
            </Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="计划完成时长（分钟）" name="planned_minutes">
          <InputNumber min={1} max={480} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item label="计时器模式" name="mode">
          <Select placeholder="选择计时器模式">
            <Select.Option value={TimerMode.POMODORO}>番茄钟</Select.Option>
            <Select.Option value={TimerMode.COUNTDOWN}>倒计时</Select.Option>
            <Select.Option value={TimerMode.COUNTUP}>正计时</Select.Option>
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  )
}
