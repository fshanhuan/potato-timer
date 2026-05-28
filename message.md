# 这里可以用来记录一些东西
# 也可以写在代码注释里面

下面这份可以直接发给前端，作为正式对接说明。

**后端对接说明**

后端文件：`PomodoroTimer.py`

主要模块：

- 用户管理：`UserManager`
- 用户对象：`User`
- 任务对象：`Task`
- 计时控制：`TimerController`
- 统计中心：`Statistics`
- 计划表：`FocusPlan`
- 本地激励语：`MottoProvider`

---

**一、用户系统**

前端应先通过昵称创建或加载用户。

```python
manager = UserManager()
user = manager.create_user("小明")
```

规则：

- 用户身份以 `nickname` 为准。
- 昵称相同：加载同一个用户的历史统计和计划表。
- 昵称不同：不会读取其他用户的数据。
- 昵称不能为空。
- 后端会自动在本地创建用户文件。

本地文件：

```text
local_user_data/小明_stats.json
local_user_data/小明_plans.json
```

---

**二、任务创建**

创建单个任务：

```python
task = user.create_task(
    title="完成课程作业",
    description="写完实验报告",
    due_date=datetime(2026, 5, 29, 18, 0),
    mode=TimerMode.POMODORO,
    importance=ImportanceLevel.HIGH,
    planned_minutes=60
)
```

批量创建：

```python
user.create_tasks_from_arrangements([
    {
        "title": "提交项目报告",
        "description": "最终版报告",
        "due_date": "2026-05-29T18:00:00",
        "importance": "CRITICAL",
        "planned_minutes": 90,
        "mode": "POMODORO"
    },
    {
        "title": "自由阅读",
        "description": "无截止日期任务",
        "due_date": None,
        "importance": "MEDIUM",
        "planned_minutes": 30,
        "mode": "COUNTUP"
    }
])
```

任务字段：

```json
{
  "task_id": 1,
  "title": "完成课程作业",
  "description": "写完实验报告",
  "motto": "专注当下，每一分钟都算数",
  "due_date": "2026-05-29T18:00:00",
  "importance": "HIGH",
  "planned_minutes": 60,
  "reminder_at": null,
  "mode": "POMODORO",
  "status": "pending",
  "total_focused_minutes": 0,
  "timer_state": "idle",
  "display_time": "25:00"
}
```

注意：

- `due_date` 可以为 `null`。
- `due_date = null` 时，不生成提醒。
- 无截止日期任务仍然参与计时和统计。
- `planned_minutes` 单位是分钟。
- 未传 `motto` 时，后端会随机读取本地 motto。

---

**三、枚举值**

计时模式 `mode`：

```text
POMODORO
COUNTDOWN
COUNTUP
```

任务优先级 `importance`：

```text
LOW
MEDIUM
HIGH
CRITICAL
```

任务状态 `status`：

```text
pending
active
completed
abandoned
```

计时器状态 `timer_state/state`：

```text
idle
running
paused
finished
```

番茄钟阶段 `current_phase`：

```text
work
short_break
long_break
```

---

**四、任务排序**

按截止时间排序：

```python
user.sort_tasks_by_time()
```

规则：

1. 有截止日期的任务在前。
2. 截止时间越早越靠前。
3. 无截止日期任务排最后。

按优先级排序：

```python
user.sort_tasks_by_priority()
```

规则：

1. `CRITICAL`
2. `HIGH`
3. `MEDIUM`
4. `LOW`
5. 同优先级再按截止时间排序。
6. 无截止日期排后。

前端展示时建议调用：

```python
[task.to_dict() for task in user.sort_tasks_by_time()]
[task.to_dict() for task in user.sort_tasks_by_priority()]
```

---

**五、提醒程度**

调用：

```python
user.get_reminders(now)
```

返回示例：

```json
[
  {
    "task_id": 3,
    "title": "提交项目报告",
    "importance": "CRITICAL",
    "due_date": "2026-05-29T18:00:00",
    "minutes_left": 10.0,
    "reminder_degree": 3,
    "level": "high"
  }
]
```

提醒规则：

| 条件                         | reminder_degree | level     |
| ---------------------------- | --------------: | --------- |
| 无截止日期 / 已完成 / 已放弃 |               0 | `none`    |
| 已过截止时间                 |               4 | `expired` |
| `CRITICAL` 或 15 分钟内到期  |               3 | `high`    |
| `HIGH` 或 60 分钟内到期      |               2 | `medium`  |
| 其他有截止日期任务           |               1 | `low`     |

注意：

- 无截止日期任务不会出现在提醒列表中。
- 前端只根据 `reminder_degree` 或 `level` 决定 UI 表现。
- 后端不负责弹窗、声音、红点、颜色等具体提示方式。

---

**六、计时控制**

创建控制器：

```python
controller = TimerController(user=user, task=task)
```

开始：

```python
controller.start()
```

暂停：

```python
controller.pause()
```

停止并保存记录：

```python
controller.stop(note="用户备注")
```

定时刷新：

```python
controller.tick()
```

建议前端每秒调用一次 `tick()`，或者由后端定时器主动推送。

统一返回结构：

```json
{
  "action": "started",
  "message": "▶ 计时开始",
  "task_id": 1,
  "task_title": "完成课程作业",
  "mode": "POMODORO",
  "state": "running",
  "display_time": "25:00",
  "elapsed_sec": 0
}
```

番茄钟额外字段：

```json
{
  "pomodoro_info": {
    "current_phase": "work",
    "completed_pomodoros": 0,
    "pomodoros_per_round": 4,
    "next_is_long_break": false,
    "display_time": "25:00",
    "state": "running"
  }
}
```

计时结束返回：

```json
{
  "action": "finished",
  "event": "finished",
  "focused_minutes": 25,
  "record_id": 1
}
```

注意：

- `stop()` 会保存本次记录。
- 小于 1 秒的计时不会写入统计。
- 当前 `stop()` 默认为主动中止，`is_completed=False`。
- 番茄钟自然结束时，`tick()` 会保存 `is_completed=True`。
- 如果前端需要“完成任务并停止”，建议后续扩展一个专用接口。

---

**七、日计划和周计划**

日计划：

```python
user.generate_day_plan(date(2026, 5, 29))
```

返回：

```json
{
  "date": "2026-05-29",
  "total_planned_minutes": 150,
  "items": [
    {
      "task_id": 1,
      "title": "完成课程作业",
      "importance": "HIGH",
      "planned_minutes": 60,
      "start_time": "2026-05-29T09:00:00",
      "end_time": "2026-05-29T10:00:00",
      "due_date": "2026-05-29T18:00:00",
      "status": "pending"
    }
  ]
}
```

周计划：

```python
user.generate_week_plan(date(2026, 5, 29))
```

返回：

```json
{
  "week_start": "2026-05-25",
  "week_end": "2026-05-31",
  "total_planned_minutes": 300,
  "days": []
}
```

注意：

- 这里的日计划/周计划基于任务截止日期生成。
- 无截止日期任务不会进入日/周计划。
- 默认从当天 9:00 开始排。

---

**八、计划表 FocusPlan**

计划表用于用户自定义一段时间内的专注目标。

创建方式一：每天固定专注时长

```python
plan = user.create_focus_plan(
    title="期末复习计划",
    start_date="2026-05-29",
    end_date="2026-06-04",
    daily_focus_minutes=60,
    selected_dates=["2026-05-29", "2026-05-31", "2026-06-02"]
)
```

创建方式二：输入总专注时长

```python
plan = user.create_focus_plan(
    title="项目冲刺计划",
    start_date="2026-05-29",
    end_date="2026-06-01",
    total_focus_minutes=240
)
```

规则：

- `daily_focus_minutes` 和 `total_focus_minutes` 必须二选一。
- 不能同时传，也不能都不传。
- `selected_dates` 可选。
- 如果不传 `selected_dates`，默认选择开始日期到截止日期之间的所有天。
- `selected_dates` 必须在 `start_date` 和 `end_date` 范围内。
- 计划创建后会自动保存到本地。
- 同昵称用户重启后会自动加载历史计划。

计划对象：

```json
{
  "plan_id": 1,
  "title": "期末复习计划",
  "start_date": "2026-05-29",
  "end_date": "2026-06-04",
  "selected_dates": [
    "2026-05-29",
    "2026-05-31",
    "2026-06-02"
  ],
  "daily_focus_minutes": 60,
  "total_focus_minutes": 180,
  "created_at": "2026-05-29T10:00:00"
}
```

查询某一天：

```python
user.get_focus_plan_day(plan_id=1, query_date="2026-05-31")
```

返回：

```json
{
  "plan_id": 1,
  "title": "期末复习计划",
  "date": "2026-05-31",
  "in_range": true,
  "is_selected": true,
  "planned_minutes": 60
}
```

查询进度：

```python
user.get_focus_plan_progress(plan_id=1, query_date="2026-05-29")
```

返回：

```json
{
  "plan_id": 1,
  "title": "期末复习计划",
  "start_date": "2026-05-29",
  "end_date": "2026-06-04",
  "selected_dates": ["2026-05-29", "2026-05-31"],
  "daily_focus_minutes": 60,
  "total_focus_minutes": 120,
  "actual_minutes": 30,
  "expected_minutes_by_query_date": 60,
  "gap_minutes": -30,
  "remaining_minutes": 90,
  "required_daily_minutes": 45,
  "progress_percent": 25,
  "expected_progress_percent": 50,
  "status": "behind",
  "status_message": "进度落后，需要补足专注时间",
  "daily_reports": [
    {
      "date": "2026-05-29",
      "planned_minutes": 60,
      "actual_minutes": 30,
      "difference_minutes": -30,
      "is_completed": false
    }
  ]
}
```

计划状态 `status`：

```text
completed  # 已完成
on_track   # 正常或领先
behind     # 落后
```

---

**九、统计报告**

调用：

```python
user.get_time_usage_report(start_date, end_date)
```

返回：

```json
{
  "start_date": "2026-05-29",
  "end_date": "2026-05-29",
  "planned_minutes": 120,
  "actual_minutes": 80,
  "difference_minutes": -40,
  "time_waste_minutes": 45,
  "interrupted_minutes": 5,
  "overdue_unfinished": 1,
  "tasks": [],
  "suggestions": []
}
```

注意：

- 有截止日期且在统计范围内的任务会进入报告。
- 无截止日期任务如果有实际计时记录，也会进入报告。
- `difference_minutes = actual_minutes - planned_minutes`。
- 重启后，同昵称用户会加载历史统计数据并参与报告。

---

**十、本地 Motto 文件**

默认读取：

```text
mottos.txt
```

支持普通格式：

```text
专注当下，每一分钟都算数
先完成最小的一步，再完成下一步
```

支持分阶段格式：

```text
work|开始深度工作
short_break|起身喝水
long_break|好好休息
```

规则：

- 文件不存在时使用默认内置 motto。
- 空行忽略。
- `#` 开头视为注释。
- 阶段名支持：`work`、`short_break`、`long_break`。

---

**十一、建议 API 设计**

```text
POST /users
GET  /users/{nickname}

POST /tasks
POST /tasks/batch
GET  /tasks
GET  /tasks/sorted/time
GET  /tasks/sorted/priority
GET  /reminders

POST /timer/{task_id}/start
POST /timer/{task_id}/pause
POST /timer/{task_id}/stop
GET  /timer/{task_id}/tick

GET  /plans/day?date=2026-05-29
GET  /plans/week?date=2026-05-29

POST /focus-plans
GET  /focus-plans
GET  /focus-plans/{plan_id}/day?date=2026-05-31
GET  /focus-plans/{plan_id}/progress?date=2026-05-31

GET  /statistics/report?start_date=2026-05-29&end_date=2026-06-04
```

---

**十二、前端特别注意**

- 日期建议统一传 ISO 格式：
  - `2026-05-29`
  - `2026-05-29T18:00:00`
- 不要传 `2026/05/29`。
- `due_date` 必须允许为 `null`。
- 无截止日期任务不展示提醒。
- 提醒 UI 由前端根据 `reminder_degree` 自行决定。
- 任务计划和 `FocusPlan` 是两个概念：
  - 任务日/周计划：基于任务截止日期。
  - `FocusPlan`：用户自定义一段时间内的专注目标。
- 计划表已持久化，但任务列表本身目前没有持久化。
- 统计数据和计划表按昵称隔离。
- 测试/demo 中运行主函数会写入本地统计和计划文件，正式集成时建议不要自动运行 demo。