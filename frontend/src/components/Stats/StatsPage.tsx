import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  DatePicker,
  Select,
  Statistic,
  Table,
  Tag,
  Alert,
  Progress,
  Empty,
  Spin,
  Radio,
  Space,
} from 'antd'
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  FireOutlined,
  ExclamationCircleOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { TimeUsageReport, DailyStats, TaskReport } from '@/types'
import { formatDate } from '@/utils/timeFormat'
import { THEME_COLORS } from '@/config/theme'
import { useAppStore } from '@/store'
import './StatsPage.css'

const { RangePicker } = DatePicker
const { Column } = Table

type TimeRange = 'today' | 'week' | 'month' | 'custom'
type ChartType = 'bar' | 'line'

const generateMockDailyStats = (): DailyStats[] => {
  const stats: DailyStats[] = []
  const today = new Date()

  for (let i = 6; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)

    const focusedMinutes = Math.floor(Math.random() * 120) + 20
    const sessions = Math.floor(focusedMinutes / 25) + (Math.random() > 0.5 ? 1 : 0)
    const completedSessions = Math.floor(sessions * (0.6 + Math.random() * 0.4))
    const pomodoroCount = Math.floor(focusedMinutes / 25)

    stats.push({
      date: formatDate(date),
      total_focused_minutes: focusedMinutes,
      total_sessions: sessions,
      completed_sessions: completedSessions,
      pomodoro_count: pomodoroCount,
    })
  }

  return stats
}

const mockTaskReports: TaskReport[] = [
  {
    task_id: 1,
    title: '学习 Python 后端开发',
    due_date: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
    planned_minutes: 60,
    actual_minutes: 45,
    difference_minutes: -15,
    status: 'pending',
    is_overdue: false,
  },
  {
    task_id: 2,
    title: '编写前端组件',
    due_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    planned_minutes: 45,
    actual_minutes: 45,
    difference_minutes: 0,
    status: 'completed',
    is_overdue: false,
  },
  {
    task_id: 3,
    title: '代码审查与优化',
    due_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    planned_minutes: 30,
    actual_minutes: 35,
    difference_minutes: 5,
    status: 'completed',
    is_overdue: false,
  },
  {
    task_id: 4,
    title: '编写测试用例',
    due_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    planned_minutes: 40,
    actual_minutes: 30,
    difference_minutes: -10,
    status: 'completed',
    is_overdue: false,
  },
  {
    task_id: 5,
    title: 'API 接口对接',
    due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    planned_minutes: 90,
    actual_minutes: 60,
    difference_minutes: -30,
    status: 'active',
    is_overdue: false,
  },
]

const generateMockTimeUsageReport = (stats: DailyStats[]): TimeUsageReport => {
  const actualMinutes = stats.reduce((sum, s) => sum + s.total_focused_minutes, 0)
  const plannedMinutes = actualMinutes + Math.floor(Math.random() * 60) - 30
  const completedSessions = stats.reduce((sum, s) => sum + s.completed_sessions, 0)
  const totalSessions = stats.reduce((sum, s) => sum + s.total_sessions, 0)

  return {
    start_date: stats[0]?.date || formatDate(new Date()),
    end_date: stats[stats.length - 1]?.date || formatDate(new Date()),
    planned_minutes: Math.max(0, plannedMinutes),
    actual_minutes: actualMinutes,
    difference_minutes: actualMinutes - plannedMinutes,
    time_waste_minutes:
      Math.max(0, plannedMinutes - actualMinutes) + Math.floor(Math.random() * 20),
    interrupted_minutes: totalSessions - completedSessions,
    overdue_unfinished: 0,
    tasks: mockTaskReports,
    suggestions: [
      '实际专注少于计划，建议缩小单个任务粒度或提前安排开始时间',
      '存在中断会话，建议把易被打断的任务安排在低干扰时段',
    ],
  }
}

export const StatsPage: React.FC = () => {
  const { theme } = useAppStore()
  const themeConfig = THEME_COLORS[theme]

  const [timeRange, setTimeRange] = useState<TimeRange>('week')
  const [chartType, setChartType] = useState<ChartType>('bar')
  const [customRange, setCustomRange] = useState<[Dayjs, Dayjs] | null>(null)
  const [loading, setLoading] = useState(false)
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([])
  const [report, setReport] = useState<TimeUsageReport | null>(null)

  useEffect(() => {
    loadData()
  }, [timeRange, customRange])

  const loadData = async () => {
    setLoading(true)

    setTimeout(() => {
      let stats: DailyStats[] = []

      switch (timeRange) {
        case 'today':
          stats = [generateMockDailyStats()[6]]
          break
        case 'week':
          stats = generateMockDailyStats()
          break
        case 'month':
          stats = generateMockDailyStats().concat(
            Array.from({ length: 23 }, (_, i) => {
              const date = new Date(Date.now() - (i + 7) * 24 * 60 * 60 * 1000)
              return {
                date: formatDate(date),
                total_focused_minutes: Math.floor(Math.random() * 120) + 20,
                total_sessions: 3,
                completed_sessions: 2,
                pomodoro_count: 2,
              }
            })
          )
          break
        case 'custom':
          if (customRange) {
            const days = customRange[1].diff(customRange[0], 'day') + 1
            stats = Array.from({ length: days }, (_, i) => {
              const date = new Date(customRange[0].add(i, 'day').valueOf())
              return {
                date: formatDate(date),
                total_focused_minutes: Math.floor(Math.random() * 120) + 20,
                total_sessions: 3,
                completed_sessions: 2,
                pomodoro_count: 2,
              }
            })
          } else {
            stats = generateMockDailyStats()
          }
          break
      }

      setDailyStats(stats)
      setReport(generateMockTimeUsageReport(stats))
      setLoading(false)
    }, 600)
  }

  const handleRangeChange = (value: TimeRange) => {
    setTimeRange(value)
    if (value !== 'custom') {
      setCustomRange(null)
    }
  }

  const handleCustomRangeChange = (dates: [Dayjs | null, Dayjs | null] | null) => {
    if (dates && dates[0] && dates[1]) {
      setCustomRange([dates[0], dates[1]])
      setTimeRange('custom')
    }
  }

  const calculateTotalStats = () => {
    return {
      totalFocused: dailyStats.reduce((sum, s) => sum + s.total_focused_minutes, 0),
      totalSessions: dailyStats.reduce((sum, s) => sum + s.total_sessions, 0),
      completedSessions: dailyStats.reduce(
        (sum, s) => sum + s.completed_sessions,
        0
      ),
      pomodoroCount: dailyStats.reduce((sum, s) => sum + s.pomodoro_count, 0),
    }
  }

  const totalStats = calculateTotalStats()

  const chartData = dailyStats.map((stat) => ({
    date: stat.date.slice(5),
    minutes: stat.total_focused_minutes,
    sessions: stat.total_sessions,
    pomodoros: stat.pomodoro_count,
  }))

  const pieData = [
    {
      name: '已完成',
      value: mockTaskReports.filter((t) => t.status === 'completed').length,
      color: '#52c41a',
    },
    {
      name: '进行中',
      value: mockTaskReports.filter((t) => t.status === 'active').length,
      color: '#1890ff',
    },
    {
      name: '待开始',
      value: mockTaskReports.filter((t) => t.status === 'pending').length,
      color: '#faad14',
    },
  ]

  const renderTimeUsageReport = (report: TimeUsageReport) => {
    const progressPercent =
      report.planned_minutes > 0
        ? Math.min(100, (report.actual_minutes / report.planned_minutes) * 100)
        : 0

    return (
      <div className="time-usage-report">
        <h3>时间使用报告</h3>

        <Row gutter={[16, 16]} className="report-stats">
          <Col xs={12} sm={6}>
            <Statistic
              title="计划时长"
              value={report.planned_minutes}
              suffix="分钟"
              valueStyle={{ color: '#1890ff', fontSize: '18px' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="实际专注"
              value={report.actual_minutes}
              suffix="分钟"
              valueStyle={{
                color: progressPercent >= 90 ? '#52c41a' : '#faad14',
                fontSize: '18px',
              }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="时间差"
              value={report.difference_minutes}
              suffix="分钟"
              valueStyle={{
                color: report.difference_minutes >= 0 ? '#52c41a' : '#ff4d4f',
                fontSize: '18px',
              }}
              formatter={(value) =>
                typeof value === 'number' && value >= 0 ? `+${value}` : `${value}`
              }
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="浪费时间"
              value={report.time_waste_minutes}
              suffix="分钟"
              valueStyle={{ color: '#ff4d4f', fontSize: '18px' }}
            />
          </Col>
        </Row>

        <div className="progress-section">
          <div className="progress-label">完成进度</div>
          <Progress
            percent={Math.round(progressPercent)}
            status={
              progressPercent >= 90
                ? 'success'
                : progressPercent >= 70
                  ? 'normal'
                  : 'exception'
            }
            strokeColor={themeConfig.primary}
            strokeWidth={10}
          />
        </div>

        {report.suggestions.length > 0 && (
          <div className="suggestions">
            <h4>
              <ExclamationCircleOutlined /> 建议
            </h4>
            {report.suggestions.map((suggestion, index) => (
              <Alert
                key={index}
                message={suggestion}
                type="info"
                showIcon
                style={{ marginBottom: 8 }}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  const renderTaskCompletion = (tasks: TaskReport[]) => {
    const columns = [
      {
        title: '任务',
        dataIndex: 'title',
        key: 'title',
        width: 200,
        ellipsis: true,
      },
      {
        title: '计划',
        dataIndex: 'planned_minutes',
        key: 'planned_minutes',
        align: 'right' as const,
        width: 80,
        render: (value: number) => `${value}分钟`,
      },
      {
        title: '实际',
        dataIndex: 'actual_minutes',
        key: 'actual_minutes',
        align: 'right' as const,
        width: 80,
        render: (value: number) => `${value}分钟`,
      },
      {
        title: '差异',
        dataIndex: 'difference_minutes',
        key: 'difference_minutes',
        align: 'right' as const,
        width: 80,
        render: (value: number) => (
          <span style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
            {value >= 0 ? `+${value}` : value}
          </span>
        ),
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        render: (status: string) => {
          const colorMap: Record<string, string> = {
            pending: 'default',
            active: 'processing',
            completed: 'success',
            abandoned: 'error',
          }
          const textMap: Record<string, string> = {
            pending: '待开始',
            active: '进行中',
            completed: '已完成',
            abandoned: '已放弃',
          }
          return <Tag color={colorMap[status]}>{textMap[status]}</Tag>
        },
      },
    ]

    return (
      <div className="task-completion">
        <h3>任务完成情况</h3>
        <Table
          dataSource={tasks}
          columns={columns}
          pagination={false}
          rowKey="task_id"
          size="middle"
        />
      </div>
    )
  }

  if (loading) {
    return (
      <div className="stats-page-loading">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="stats-page">
      <div className="stats-header">
        <h1>数据统计</h1>
        <Space wrap>
          <Select
            value={timeRange}
            onChange={handleRangeChange}
            style={{ width: 100 }}
          >
            <Select.Option value="today">今天</Select.Option>
            <Select.Option value="week">本周</Select.Option>
            <Select.Option value="month">本月</Select.Option>
            <Select.Option value="custom">自定义</Select.Option>
          </Select>
          {timeRange === 'custom' && (
            <RangePicker
              value={customRange}
              onChange={handleCustomRangeChange}
            />
          )}
          <Radio.Group
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
            size="small"
          >
            <Radio.Button value="bar">柱状图</Radio.Button>
            <Radio.Button value="line">折线图</Radio.Button>
          </Radio.Group>
        </Space>
      </div>

      <div className="stats-content">
        {/* 统计概览卡片 */}
        <Row gutter={[16, 16]} className="stats-overview">
          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card stat-card-primary">
              <div className="stat-icon">
                <ClockCircleOutlined />
              </div>
              <div className="stat-content">
                <div className="stat-value">{totalStats.totalFocused}</div>
                <div className="stat-label">专注时长(分钟)</div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card stat-card-orange">
              <div className="stat-icon">
                <FireOutlined />
              </div>
              <div className="stat-content">
                <div className="stat-value">{totalStats.pomodoroCount}</div>
                <div className="stat-label">完成番茄(个)</div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card stat-card-blue">
              <div className="stat-icon">
                <ThunderboltOutlined />
              </div>
              <div className="stat-content">
                <div className="stat-value">{totalStats.totalSessions}</div>
                <div className="stat-label">总会话(次)</div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card className="stat-card stat-card-green">
              <div className="stat-icon">
                <CheckCircleOutlined />
              </div>
              <div className="stat-content">
                <div className="stat-value">{totalStats.completedSessions}</div>
                <div className="stat-label">完成会话(次)</div>
              </div>
            </Card>
          </Col>
        </Row>

        {/* 图表区域 */}
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={16}>
            <Card className="chart-card" title="专注趋势">
              {dailyStats.length === 0 ? (
                <Empty description="暂无数据" />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  {chartType === 'bar' ? (
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        stroke="#666"
                      />
                      <YAxis
                        tick={{ fontSize: 12 }}
                        stroke="#666"
                        label={{
                          value: '分钟',
                          angle: -90,
                          position: 'insideLeft',
                        }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'white',
                          borderRadius: 8,
                          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                        }}
                      />
                      <Legend />
                      <Bar
                        dataKey="minutes"
                        name="专注时长"
                        fill={themeConfig.primary}
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  ) : (
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        stroke="#666"
                      />
                      <YAxis
                        tick={{ fontSize: 12 }}
                        stroke="#666"
                        label={{
                          value: '分钟',
                          angle: -90,
                          position: 'insideLeft',
                        }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'white',
                          borderRadius: 8,
                          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                        }}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="minutes"
                        name="专注时长"
                        stroke={themeConfig.primary}
                        strokeWidth={2}
                        dot={{ fill: themeConfig.primary, r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  )}
                </ResponsiveContainer>
              )}
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card className="chart-card" title="任务状态分布">
              {pieData.filter((d) => d.value > 0).length === 0 ? (
                <Empty description="暂无数据" />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(0)}%`
                      }
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Card>
          </Col>
        </Row>

        {/* 时间使用报告 */}
        <Row gutter={[16, 16]}>
          <Col xs={24}>
            <Card className="report-card" title={<TrophyOutlined />}>
              {report && renderTimeUsageReport(report)}
            </Card>
          </Col>
        </Row>

        {/* 任务完成情况 */}
        <Row gutter={[16, 16]}>
          <Col xs={24}>
            <Card className="tasks-card" title="任务完成情况">
              {report &&
                report.tasks.length > 0 &&
                renderTaskCompletion(report.tasks)}
            </Card>
          </Col>
        </Row>

        {/* 日数据明细 */}
        <Row gutter={[16, 16]}>
          <Col xs={24}>
            <Card className="detail-card" title="日数据明细">
              {dailyStats.length === 0 ? (
                <Empty description="暂无数据" />
              ) : (
                <Table
                  dataSource={dailyStats}
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `共 ${total} 条记录`,
                  }}
                  size="middle"
                  rowKey="date"
                >
                  <Column title="日期" dataIndex="date" key="date" width={120} />
                  <Column
                    title="专注时长"
                    dataIndex="total_focused_minutes"
                    key="total_focused_minutes"
                    align="right"
                    width={100}
                    render={(value: number) => (
                      <span
                        style={{
                          color: themeConfig.primary,
                          fontWeight: 500,
                        }}
                      >
                        {value}分钟
                      </span>
                    )}
                  />
                  <Column
                    title="会话次数"
                    dataIndex="total_sessions"
                    key="total_sessions"
                    align="right"
                    width={80}
                  />
                  <Column
                    title="完成次数"
                    dataIndex="completed_sessions"
                    key="completed_sessions"
                    align="right"
                    width={80}
                    render={(value: number, record: DailyStats) => (
                      <span
                        style={{
                          color:
                            value === record.total_sessions
                              ? '#52c41a'
                              : undefined,
                        }}
                      >
                        {value}
                      </span>
                    )}
                  />
                  <Column
                    title="番茄数"
                    dataIndex="pomodoro_count"
                    key="pomodoro_count"
                    align="right"
                    width={80}
                    render={(value: number) => (
                      <span style={{ color: '#fa541c', fontWeight: 500 }}>
                        {value}
                      </span>
                    )}
                  />
                  <Column
                    title="完成率"
                    key="completion_rate"
                    align="right"
                    width={80}
                    render={(_: unknown, record: DailyStats) => {
                      const rate =
                        record.total_sessions > 0
                          ? Math.round(
                              (record.completed_sessions /
                                record.total_sessions) *
                                100
                            )
                          : 0
                      return (
                        <Progress
                          percent={rate}
                          size="small"
                          status={
                            rate >= 80
                              ? 'success'
                              : rate >= 50
                                ? 'normal'
                                : 'exception'
                          }
                        />
                      )
                    }}
                  />
                </Table>
              )}
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  )
}
