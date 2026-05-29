- 后端对接说明（2026-05-29 更新）

  后端文件：

  - `PomodoroTimer.py` — 核心业务层
  - `ai_assistant.py` — AI 自然语言解析模块（新增）

  主要模块：

  - 用户管理：`UserManager`
  - 用户对象：`User`
  - 任务对象：`Task`
  - 计时控制：`TimerController`
  - 统计中心：`Statistics`
  - 计划表：`FocusPlan`
  - 本地激励语：`MottoProvider`
  - AI 助手：`AIAssistant`（新增）

  ---

  **一、用户系统**

  前端应先通过昵称创建或加载用户。

  ```python
  manager = UserManager()
  user = manager.create_user("小明")
  ```

  规则：

  - 用户身份以 `nickname` 为准。
  - 昵称相同：加载同一个用户的历史任务、统计和计划表。
  - 昵称不同：不会读取其他用户的数据。
  - 昵称不能为空。
  - 后端会自动在本地创建用户文件，重启后自动恢复所有数据。

  本地文件：

  ```text
  local_user_data/小明_stats.json   ← 专注记录
  local_user_data/小明_plans.json   ← 计划表
  local_user_data/小明_tasks.json   ← 任务列表（2026-05-29 新增）
  ```

  所有文件写入均采用原子写入（先写临时文件再替换），防止中途崩溃导致文件损坏。

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

  任务字段（`task.to_dict()` 返回）：

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
    "created_at": "2026-05-29T10:00:00",
    "completed_at": null,
    "total_focused_minutes": 0
  }
  ```

  注意：

  - `due_date` 可以为 `null`。`due_date = null` 时，不生成提醒。
  - 无截止日期任务仍然参与计时和统计。
  - `planned_minutes` 单位是分钟。
  - 未传 `motto` 时，后端会随机读取本地 motto。
  - **任务自动保存**：`create_task()` 和 `create_tasks_from_arrangements()` 调用后自动写入本地文件，重启后自动恢复。

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

  1. `CRITICAL` → `HIGH` → `MEDIUM` → `LOW`
  2. 同优先级再按截止时间排序。
  3. 无截止日期排后。

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

  开始 / 暂停 / 停止：

  ```python
  controller.start()              # 开始计时
  controller.pause()              # 暂停
  controller.stop(note="备注")    # 停止并保存记录
  controller.tick()               # 每秒调用一次，检测自然结束
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

  番茄钟额外字段（`is_pomodoro=True` 时）：

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
  - 番茄钟自然结束时，`tick()` 会保存 `is_completed=True`。

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

  - 日/周计划基于任务截止日期生成。
  - 无截止日期任务不会进入计划。
  - 默认从当天 9:00 开始排。

  ---

  **八、计划表 FocusPlan**

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
  - `selected_dates` 可选，不传则默认覆盖起止之间所有天。
  - 计划创建后自动保存，重启后自动加载。

  计划对象：

  ```json
  {
    "plan_id": 1,
    "title": "期末复习计划",
    "start_date": "2026-05-29",
    "end_date": "2026-06-04",
    "selected_dates": ["2026-05-29", "2026-05-31", "2026-06-02"],
    "daily_focus_minutes": 60,
    "total_focus_minutes": 180,
    "created_at": "2026-05-29T10:00:00"
  }
  ```

  查询某天 / 查询进度：

  ```python
  user.get_focus_plan_day(plan_id=1, query_date="2026-05-31")
  user.get_focus_plan_progress(plan_id=1, query_date="2026-05-29")
  ```

  进度状态 `status`：

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

  - `difference_minutes = actual_minutes - planned_minutes`。
  - 重启后，同昵称用户会自动加载历史统计数据。

  ---

  **十、本地 Motto 文件**

  默认读取 `mottos.txt`。

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

  规则：文件不存在时使用内置默认 motto，空行和 `#` 开头的行忽略。

  ---

  **十一、AI 智能解析（新增）**

  文件：`ai_assistant.py`

  AI 可将自然语言自动解析为任务或计划表。模型固定为 `deepseek-v4flash`，API Key 从 `~/.deepseek_key` 文件读取。

  **初始化：**

  ```python
  from ai_assistant import AIAssistant
  
  # api_key 自动从 ~/.deepseek_key 读取；也可显式传入
  assistant = AIAssistant(user=user)
  # 或: assistant = AIAssistant(user=user, api_key="sk-xxxxx")
  ```

  **对话框模式（推荐，一条语句完成对话+创建）：**

  ```python
  result = assistant.chat("明天下午3点前完成实验报告，很重要，90分钟")
  ```

  返回：

  ```json
  {
    "reply": "好的！已为你创建任务「实验报告」，截止时间是明天（2026-05-30）下午3点，重要程度为高，预计90分钟。加油！",
    "type": "tasks",
    "summary": "创建任务：明天下午3点前完成实验报告",
    "data": {
      "tasks": [
        {
          "title": "实验报告",
          "description": "",
          "due_date": "2026-05-30T15:00:00",
          "importance": "HIGH",
          "planned_minutes": 90,
          "mode": "POMODORO"
        }
      ]
    },
    "created": [
      {
        "task_id": 1,
        "title": "实验报告",
        "status": "pending",
        ...
      }
    ]
  }
  ```

  **预览模式（先展示再确认）：**

  ```python
  preview = assistant.preview("下周一三五每天复习2小时")
  # 前端展示 preview["reply"] 和 preview["data"]
  # 用户点击确认后：
  result = assistant.confirm(preview)
  ```

  **支持的输入类型：**

  | 类型         | 示例输入                       | 行为                       |
  | ------------ | ------------------------------ | -------------------------- |
  | `tasks`      | "明天下午完成作业，很重要"     | 创建任务，返回对话确认     |
  | `focus_plan` | "下周一三五每天复习2小时"      | 创建计划表，返回对话确认   |
  | `chat`       | "你好" / "你能做什么" / "谢谢" | 纯聊天回复，不创建任何对象 |
  | `error`      | "学习"（太模糊）               | 友好提示用户补充信息       |

  **前端集成对话框示例：**

  ```python
  # 每条用户消息直接调用 chat()
  for user_message in dialog_messages:
      result = assistant.chat(user_message)
      # 展示 AI 回复
      display_bubble(result["reply"])
      # 如果创建了内容，更新侧边栏
      if result.get("created"):
          refresh_task_list()
          refresh_plan_list()
  ```

  **注意：**

  - `chat()` 在解析成功时**自动创建**任务/计划，`preview()` 只解析不创建。
  - AI 回复已包含 emoji 和友好语气，可直接展示在对话框 UI 中。
  - 模型锁定为 `deepseek-v4flash`，不可切换。
  - API Key 文件位置：`~/.deepseek_key`（纯文本，只写 key 本身），换设备只需复制该文件。

  ---

  **十二、建议 API 设计**

  ```text
  POST /users
  GET  /users/{nickname}
  
  GET  /tasks                        ← 获取已持久化的任务列表
  POST /tasks
  POST /tasks/batch
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
  
  POST /ai/chat                      ← 对话框模式（新增）
  POST /ai/preview                   ← 预览模式（新增）
  POST /ai/confirm                   ← 确认创建（新增）
  ```

  ---

  **十三、前端特别注意**

  - 日期建议统一传 ISO 格式（`2026-05-29`、`2026-05-29T18:00:00`），不要传 `2026/05/29`。
  - `due_date` 必须允许为 `null`。无截止日期任务不展示提醒。
  - 提醒 UI 由前端根据 `reminder_degree` 自行决定（颜色、图标、红点等）。
  - **任务日/周计划** 和 **FocusPlan** 是两个不同的概念：
    - 任务日/周计划：基于任务截止日期自动生成。
    - FocusPlan：用户自定义一段时间内的专注目标。
  - **所有用户数据均已持久化**（2026-05-29 更新）：
    - 任务列表 → `{昵称}_tasks.json`，每次创建任务自动保存。
    - 专注记录 → `{昵称}_stats.json`，每次计时结束自动保存。
    - 计划表 → `{昵称}_plans.json`，每次创建计划自动保存。
    - 所有文件原子写入（`.tmp` + `rename`），防崩溃损坏。
  - 同一昵称重启后自动恢复全部数据（任务 + 统计 + 计划）。
  - AI 对话框功能需在 `~/.deepseek_key` 中配置 API Key。
  - 测试/demo 中运行主函数会写入本地文件，正式集成时建议不要自动运行 demo。