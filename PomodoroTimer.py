from typing import List, Optional, Dict
from datetime import datetime, date
from abc import ABC, abstractmethod
from enum import Enum
import time


# ============================================================
# 枚举类：统一管理所有状态常量
# ============================================================
#有没有新增功能根据四象限法则对任务字典列表进行lambda排序，返回的列表前端显示
class TimerMode(Enum):
    """计时模式"""
    POMODORO   = 0   # 番茄钟
    COUNTDOWN  = 1   # 倒计时
    COUNTUP    = 2   # 正计时（正向计时）


class TimerState(Enum):
    """计时器运行状态"""
    IDLE     = "idle"      # 空闲/未开始
    RUNNING  = "running"   # 运行中
    PAUSED   = "paused"    # 已暂停
    FINISHED = "finished"  # 已结束


class PomodoroPhase(Enum):
    """番茄钟阶段"""
    WORK        = "work"         # 工作阶段
    SHORT_BREAK = "short_break"  # 短休息
    LONG_BREAK  = "long_break"   # 长休息


class TaskStatus(Enum):
    """任务状态"""
    PENDING    = "pending"     # 待开始
    ACTIVE     = "active"      # 进行中
    COMPLETED  = "completed"   # 已完成


# ============================================================
# 计时器层：三种计时模式
# ============================================================

class BaseTimer(ABC):
    """
    计时器抽象基类
    职责：维护计时的核心状态（开始/暂停/重置）
    """
    def __init__(self):
        self._start_time:   Optional[float] = None  # 本段计时的起始时间戳
        self._accumulated:  float = 0.0             # 暂停前已累计秒数
        self._pause_start:  Optional[float] = None  # 暂停时刻时间戳
        self.state:         TimerState = TimerState.IDLE

    # ---------- 抽象接口（子类必须实现）----------

    @abstractmethod
    def get_display_time(self) -> float:
        """返回用于界面展示的秒数（倒计时返回剩余，正计时返回已过）"""
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        """判断计时是否自然结束"""
        pass

    @abstractmethod
    def get_mode(self) -> TimerMode:
        """返回计时模式枚举"""
        pass

    # ---------- 通用控制操作 ----------

    def start(self) -> None:
        """开始 或 从暂停恢复"""
        if self.state == TimerState.PAUSED:
            # 恢复：不清空 _accumulated，只重置起始点
            self._start_time = time.time()
            self.state = TimerState.RUNNING
        elif self.state == TimerState.IDLE:
            self._start_time = time.time()
            self._accumulated = 0.0
            self.state = TimerState.RUNNING

    def pause(self) -> None:
        """暂停：将本段已计时秒数合并入 _accumulated"""
        if self.state == TimerState.RUNNING:
            self._accumulated += time.time() - self._start_time
            self._pause_start = time.time()
            self._start_time  = None
            self.state = TimerState.PAUSED

    def stop(self) -> float:
        """
        主动停止，返回本次实际专注秒数
        stop 与 reset 的区别：stop 保留数据供记录，reset 清空一切

        """
        focused = self.elapsed
        self.reset()
        return focused

    def reset(self) -> None:
        """重置到初始空闲状态"""
        self._start_time  = None
        self._accumulated = 0.0
        self._pause_start = None
        self.state = TimerState.IDLE
    def tick(self) -> bool:
        """
        每帧/每秒调用一次，检测是否自然结束
        返回 True 表示刚刚结束（调用方可据此触发下一阶段）
        """
        if self.state == TimerState.RUNNING and self.is_finished():
            self.state = TimerState.FINISHED
            return True
        return False    

    @property
    def elapsed(self) -> float:
        """已累计专注秒数（排除暂停时间）"""
        if self.state == TimerState.RUNNING and self._start_time:
            return self._accumulated + (time.time() - self._start_time)
        return self._accumulated  # PAUSED / IDLE 时直接返回已累计值
    
    
    def format_display(self) -> str:
        """将展示时间格式化为 MM:SS 字符串"""
        total_sec = int(self.get_display_time())
        minutes, seconds = divmod(total_sec, 60)
        return f"{minutes:02d}:{seconds:02d}"

class CountUpTimer(BaseTimer):
    """
    正向计时器
    职责：从 0 向上计时，记录本次专注时长
    这里只要开启正向计时就会判定事件完成，如果需要有目标时间直接使用倒计时即可
    """
    def __init__(self, target_seconds: Optional[float] = None):
        super().__init__()
        

    def get_display_time(self) -> float:
        """返回已经过秒数"""
        return self.elapsed

    def is_finished(self) -> bool:
        if self.target_seconds is None:
            return False
        return self.elapsed >= 0   #判定条件是0
    
    def get_mode(self) -> TimerMode:
        return TimerMode.COUNTUP

class CountDownTimer(BaseTimer):
    """
    倒计时器
    职责：从目标时长向下倒数至 0
    """
    def __init__(self, target_seconds: float):
        super().__init__()
        self.target_seconds: float = target_seconds  # 倒计时目标秒数

    def get_display_time(self) -> float:
        """返回剩余秒数，最小为 0"""
        return max(0.0, self.target_seconds - self.elapsed)

    def is_finished(self) -> bool:
        return self.elapsed >= self.target_seconds
    
    def get_mode(self) -> TimerMode:
        return TimerMode.COUNTDOWN

class PomodoroTimer(BaseTimer):
    """
    番茄钟计时器
    职责：管理工作/短休息/长休息的阶段轮转
    一个完整轮次 = work × 4 + short_break × 3 + long_break × 1
    """
    DEFAULT_WORK:        float = 25 * 60   # 默认工作时长（秒）
    DEFAULT_SHORT_BREAK: float =  5 * 60   # 默认短休息时长
    DEFAULT_LONG_BREAK:  float = 15 * 60   # 默认长休息时长
    POMODOROS_PER_ROUND: int   = 4         # 4个番茄后触发长休息

    def __init__(
        self,
        work_seconds:        float = DEFAULT_WORK,
        short_break_seconds: float = DEFAULT_SHORT_BREAK,
        long_break_seconds:  float = DEFAULT_LONG_BREAK,
    ):
        super().__init__()
        self.work_seconds:        float = work_seconds
        self.short_break_seconds: float = short_break_seconds
        self.long_break_seconds:  float = long_break_seconds

        self.current_phase:      PomodoroPhase = PomodoroPhase.WORK
        self.completed_pomodoros: int = 0   # 本次会话已完成的番茄数
        self.total_pomodoros:     int = 0   # 历史累计番茄数

    @property
    def current_phase_duration(self) -> float:
        """当前阶段的总时长"""
        mapping = {
            PomodoroPhase.WORK:        self.work_seconds,
            PomodoroPhase.SHORT_BREAK: self.short_break_seconds,
            PomodoroPhase.LONG_BREAK:  self.long_break_seconds,
        }
        return mapping[self.current_phase]     #创建了一个mapping的字典

    def get_display_time(self) -> float:
        """返回当前阶段剩余秒数"""
        return max(0.0, self.current_phase_duration - self.elapsed)

    def is_finished(self) -> bool:
        """当前阶段是否结束"""
        return self.elapsed >= self.current_phase_duration

    def next_phase(self) -> PomodoroPhase:
        """
        推进到下一阶段，返回新阶段枚举
        逻辑：work → short/long_break → work → ...
        """
        if self.current_phase == PomodoroPhase.WORK:
            self.completed_pomodoros += 1
            self.total_pomodoros     += 1
            # 每完成 POMODOROS_PER_ROUND 个番茄触发长休息
            if self.completed_pomodoros % self.POMODOROS_PER_ROUND == 0:
                self.current_phase = PomodoroPhase.LONG_BREAK
            else:
                self.current_phase = PomodoroPhase.SHORT_BREAK
        else:
            # 休息结束，回到工作阶段
            self.current_phase = PomodoroPhase.WORK

        self.reset()          # 重置计时，准备下一阶段
        self.start()          # 自动开始下一阶段
        return self.current_phase
    
    def get_mode(self) -> TimerMode:
        return TimerMode.POMODORO

    def get_progress_info(self) -> dict:
        """返回当前番茄进度信息，方便前端展示"""
        return {
            "current_phase":       self.current_phase.value,
            "completed_pomodoros": self.completed_pomodoros,
            "pomodoros_per_round": self.POMODOROS_PER_ROUND,
            "next_is_long_break":  self.completed_pomodoros % self.POMODOROS_PER_ROUND
                                   == self.POMODOROS_PER_ROUND - 1,
            "display_time":        self.format_display(),
            "state":               self.state.value,
        }


# ============================================================
# 记录层：会话记录 + 统计
# ============================================================

class SessionRecord:
    """
    单次专注会话记录
    职责：保存一次计时结束后的结果数据，用于统计分析
    """
    def __init__(
        self,
        record_id:      int,
        task_id:        int,
        user_id:        int,
        mode:           TimerMode,
        started_at:     datetime,
        ended_at:       datetime,
        focused_seconds: float,         # 实际专注秒数（排除暂停）
        is_completed:   bool = True,    # 是否完整完成（未中断）
        note:           Optional[str] = None,
    ):
        self.record_id       = record_id
        self.task_id         = task_id
        self.user_id         = user_id
        self.mode            = mode
        self.started_at      = started_at
        self.ended_at        = ended_at
        self.focused_seconds = focused_seconds
        self.is_completed    = is_completed
        self.note            = note

    @property
    def focused_minutes(self) -> float:
        return round(self.focused_seconds / 60, 2)

    def to_dict(self) -> dict:
        return {
            "record_id":       self.record_id,
            "task_id":         self.task_id,
            "mode":            self.mode.name,
            "started_at":      self.started_at.isoformat(),
            "ended_at":        self.ended_at.isoformat(),
            "focused_minutes": self.focused_minutes,
            "is_completed":    self.is_completed,
        }


class DailyStats:
    """
    单日统计数据
    职责：汇总某一天内所有 SessionRecord 的数据
    """
    def __init__(self, stat_date: date):
        self.stat_date:        date  = stat_date
        self.records:          List[SessionRecord] = []    #SessionRecord类列表

        # 以下字段在 recalculate() 时更新
        self.total_focused_seconds: float = 0.0   # 当日总专注秒数
        self.total_sessions:        int   = 0     # 当日总会话次数
        self.completed_sessions:    int   = 0     # 成功完成次数
        self.pomodoro_count:        int   = 0     # 番茄钟完成个数

    def add_record(self, record: SessionRecord) -> None:
        """添加记录并重新计算统计值"""
        self.records.append(record)
        self._recalculate()

    def _recalculate(self) -> None:
        """遍历所有记录，重新计算聚合数据"""
        self.total_focused_seconds = sum(r.focused_seconds for r in self.records)
        self.total_sessions        = len(self.records)
        self.completed_sessions    = sum(1 for r in self.records if r.is_completed)
        self.pomodoro_count        = sum(
            1 for r in self.records
            if r.mode == TimerMode.POMODORO and r.is_completed
        )



    @property
    def total_focused_minutes(self) -> float:
        return round(self.total_focused_seconds / 60, 2)

    def to_dict(self) -> dict:
        return {
            "date":                  self.stat_date.isoformat(),
            "total_focused_minutes": self.total_focused_minutes,
            "total_sessions":        self.total_sessions,
            "completed_sessions":    self.completed_sessions,
            "pomodoro_count":        self.pomodoro_count,
        }


class Statistics:
    """
    统计中心
    职责：管理所有 DailyStats，提供按日/周/月的历史查询接口
    归属：每个 User 拥有一个 Statistics 实例
    """
    def __init__(self, user_id: int):
        self.user_id:   int = user_id
        # key = date 对象，value = DailyStats
        self._daily_map: Dict[date, DailyStats] = {}   #按日期储存数据
        self._next_record_id: int = 1

    def create_and_save_record(
        self,
        task_id:         int,
        mode:            TimerMode,
        started_at:      datetime,
        ended_at:        datetime,
        focused_seconds: float,
        is_completed:    bool = True,
        note:            Optional[str] = None,
    ) -> SessionRecord:
        """工厂方法：创建 SessionRecord 并自动归档"""
        record = SessionRecord(
            record_id       = self._next_record_id,
            task_id         = task_id,
            user_id         = self.user_id,
            mode            = mode,
            started_at      = started_at,
            ended_at        = ended_at,
            focused_seconds = focused_seconds,
            is_completed    = is_completed,
            note            = note,
        )
        self._next_record_id += 1
        self._archive(record)
        return record
    
    def _archive(self, record: SessionRecord) -> None:
        """将记录归入对应日期的 DailyStats"""
        d = record.started_at.date()
        if d not in self._daily_map:
            self._daily_map[d] = DailyStats(d)
        self._daily_map[d].add_record(record)        
    
    def add_session_record(self, record: SessionRecord) -> None:
        """将会话记录归入对应日期的 DailyStats"""
        record_date = record.started_at.date()
        if record_date not in self._daily_map:
            self._daily_map[record_date] = DailyStats(record_date)    #创建DailyStats类实例
        self._daily_map[record_date].add_record(record)

    def get_daily(self, query_date: date) -> Optional[DailyStats]:
        """查询某一天的统计"""
        return self._daily_map.get(query_date)

    def get_weekly(self, any_day_in_week: date) -> List[DailyStats]:
        """查询某天所在周（周一~周日）的每日统计列表"""
        monday = any_day_in_week - __import__('datetime').timedelta(days=any_day_in_week.weekday())
        return [
            self._daily_map[monday + __import__('datetime').timedelta(days=i)]
            for i in range(7)
            if (monday + __import__('datetime').timedelta(days=i)) in self._daily_map
        ]

    def get_monthly(self, year: int, month: int) -> List[DailyStats]:
        """查询某年某月的每日统计列表"""
        return [
            stats for day, stats in self._daily_map.items()
            if day.year == year and day.month == month
        ]

    def get_total_focused_today(self) -> float:
        """便捷方法：获取今日总专注分钟数"""
        stats = self.get_daily(date.today())
        return stats.total_focused_minutes if stats else 0.0


# ============================================================
# 业务层：Task / Calendar / User
# ============================================================

class Task:
    """
    任务类
    职责：代表用户的一个具体待办事项，持有自己的计时器
    一个 Task 对应一种计时模式，持有对应类型的 Timer 实例
    """
    def __init__(
        self,
        task_id:     int,
        title:       str,
        description: str,
        due_date:    datetime,
        mode:        TimerMode,
        motto:       str = "",
    ):
        self.task_id:     int       = task_id
        self.title:       str       = title
        self.description: str       = description  # 任务描述/留言
        self.motto:       str       = motto        # AI 生成的鼓励话语
        self.due_date:    datetime  = due_date
        self.mode:        TimerMode = mode
        self.status:      TaskStatus = TaskStatus.PENDING
        self.created_at:  datetime  = datetime.now()
        self.completed_at: Optional[datetime] = None

        # 根据模式初始化对应计时器（后续可通过 configure_timer 重新配置）
        self.timer: BaseTimer = self._create_default_timer(mode)

        # 本任务累积的所有会话记录
        self.session_records: List[SessionRecord] = []

    @staticmethod
    def _create_default_timer(mode: TimerMode) -> BaseTimer:
        """工厂方法：按模式创建默认计时器"""
        if mode == TimerMode.POMODORO:
            return PomodoroTimer()
        elif mode == TimerMode.COUNTDOWN:
            return CountDownTimer(target_seconds=25 * 60)      #这里有默认的目标时间
        else:
            return CountUpTimer()

    def configure_timer(self, timer: BaseTimer) -> None:
        """替换为自定义配置的计时器（用于用户修改参数后重新设置）"""
        self.timer = timer

    def complete(self) -> None:
        """标记任务完成"""
        self.status       = TaskStatus.COMPLETED
        self.completed_at = datetime.now()

    def abandon(self) -> None:
        """标记任务放弃"""
        self.status = TaskStatus.ABANDONED

    def update_due_date(self, new_date: datetime) -> None:
        self.due_date = new_date

    def to_dict(self) -> dict:
        return {
            "task_id":               self.task_id,
            "title":                 self.title,
            "description":           self.description,
            "motto":                 self.motto,
            "due_date":              self.due_date.isoformat(),
            "mode":                  self.mode.name,
            "status":                self.status.value,
            "total_focused_minutes": self.total_focused_minutes,
            "timer_state":           self.timer.state.value,
            "display_time":          self.timer.format_display(),
        }


class Calendar:
    """
    日历类
    职责：按日期组织和管理多个 Task，是 User 与 Task 之间的中间层
    """
    def __init__(self, calendar_id: int, name: str):
        self.calendar_id: int        = calendar_id
        self.name:        str        = name
        self.tasks:       List[Task] = []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> bool:
        for task in self.tasks:
            if task.task_id == task_id:
                self.tasks.remove(task)
                return True
        return False

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        return next((t for t in self.tasks if t.task_id == task_id), None)

    def get_pending_tasks(self) -> List[Task]:
        """获取所有未完成任务，按截止时间排序"""
        pending = [t for t in self.tasks if t.status == TaskStatus.PENDING]
        return sorted(pending, key=lambda x: x.due_date)

    def get_tasks_by_date(self, query_date: date) -> List[Task]:
        """获取某一天截止的任务"""
        return [t for t in self.tasks if t.due_date.date() == query_date]

    def get_tasks_by_mode(self, mode: TimerMode) -> List[Task]:
        """按计时模式筛选任务"""
        return [t for t in self.tasks if t.mode == mode]

    def to_dict(self) -> dict:
        return {
            "calendar_id": self.calendar_id,
            "name":        self.name,
            "task_count":  len(self.tasks),
            "tasks":       [t.to_dict() for t in self.tasks],
        }
    

class User:
    """
    用户类（系统顶层实体）
    职责：持有日历、统计中心，提供创建任务等业务入口
    关联：1 User → 1 Calendar → N Tasks
          1 User → 1 Statistics → N DailyStats → N SessionRecords
    """
    _next_task_id: int = 1
    def __init__(self, user_id: int, username: str):
        self.user_id:   int      = user_id
        self.username:  str      = username
        # 核心聚合关系
        self.calendar:   Calendar   = Calendar(calendar_id=user_id, name=f"{username}的日历")
        self.statistics: Statistics = Statistics(user_id=user_id)


    def create_task(
        self,
        title:       str,
        description: str,
        due_date:    datetime,
        mode:        TimerMode = TimerMode.POMODORO,
        motto:       str = "",
        
    ) -> Task:
        """创建任务并自动加入日历"""
        task = Task(
            task_id     = User._next_task_id,
            title       = title,
            description = description,
            due_date    = due_date,
            mode        = mode,
            motto       = motto,
        )
        self.calendar.add_task(task)
        return task

    def save_session(self, record: SessionRecord) -> None:
        """保存一次计时会话，同步写入对应 Task 和统计中心"""
        task = self.calendar.get_task_by_id(record.task_id)
        if task:
            task.session_records.append(record)
        self.statistics.add_session_record(record)


    def get_today_summary(self) -> dict:
        """获取今日专注摘要（供 API 返回前端）"""
        stats = self.statistics.get_daily(date.today())
        return stats.to_dict() if stats else {"message": "今日暂无记录"}
    
class TimerController:
    """
    计时器控制器（核心调度层）
    职责：
        1. 接收用户操作指令（开始/暂停/继续/停止/重置/切换模式）
        2. 驱动 Task.timer 状态机流转
        3. 计时自然结束或主动停止时，自动创建 SessionRecord 并归档至统计中心
        4. 对外统一返回结构化状态字典，供上层（API/前端/快捷键）直接使用
    生命周期：
        一个活跃任务对应一个 TimerController 实例
        任务切换时应销毁旧实例并创建新实例
    状态流转：
        IDLE ──start()──→ RUNNING ──pause()──→ PAUSED
                              ↑                    │
                              └────resume()/start()┘
                              ↓
                           FINISHED ──reset()──→ IDLE
    """
    def __init__(self, user: User, task: Task):
        """
        初始化控制器
        Args:
            user : 当前操作用户（用于归档统计记录）
            task : 被控制的任务（持有计时器实例）
        """
        self.user: User = user
        self.task: Task = task
        # 记录本次会话的开始时刻（用于构造 SessionRecord）
        # 每次 start() 从 IDLE 状态启动时重置
        self._session_start: Optional[datetime] = None
    # =========================================================
    # 只读属性
    # =========================================================
    @property
    def timer(self) -> BaseTimer:
        """当前任务绑定的计时器实例"""
        return self.task.timer
    @property
    def state(self) -> TimerState:
        """计时器当前状态"""
        return self.timer.state
    @property
    def is_pomodoro(self) -> bool:
        """是否为番茄钟模式"""
        return isinstance(self.timer, PomodoroTimer)
    # =========================================================
    # 核心控制操作
    # =========================================================
    def start(self) -> dict:
        """
        开始计时 或 从暂停状态恢复
        规则：
            - IDLE    状态：记录会话开始时刻，启动计时器
            - PAUSED  状态：恢复计时，不重置会话开始时刻
            - RUNNING 状态：已在运行，直接返回当前状态
            - FINISHED状态：提示需要先重置
        Returns:
            状态字典
        """
        current_state = self.timer.state
        if current_state == TimerState.FINISHED:
            return self._build_response(
                message="⚠ 计时已结束，请先调用 reset() 重置后再开始",
                action="blocked",
            )
        if current_state == TimerState.RUNNING:
            return self._build_response(
                message="计时器已在运行中",
                action="none",
            )
        if current_state == TimerState.IDLE:
            # 全新启动：记录会话开始时刻
            self._session_start = datetime.now()
            action_label = "started"
        else:
            # PAUSED → 恢复：保留原 _session_start
            action_label = "resumed"
        self.timer.start()
        return self._build_response(
            message=f"▶ 计时{'开始' if action_label == 'started' else '恢复'}",
            action=action_label,
        )
    def pause(self) -> dict:
        """
        暂停计时
        规则：
            - 仅 RUNNING 状态可暂停
            - 暂停时将本段已计时秒数合并入 _accumulated
        Returns:
            状态字典
        """
        if self.timer.state != TimerState.RUNNING:
            return self._build_response(
                message=f"⚠ 当前状态为 [{self.state.value}]，无法暂停",
                action="blocked",
            )
        self.timer.pause()
        return self._build_response(
            message="⏸ 已暂停",
            action="paused",
        )
    # def resume(self) -> dict:
    #     """
    #     从暂停状态恢复计时
    #     语义上等同于 start()，单独提供此方法使调用方意图更清晰
    #     Returns:
    #         状态字典
    #     """
    #     if self.timer.state != TimerState.PAUSED:
    #         return self._build_response(
    #             message=f"⚠ 当前状态为 [{self.state.value}]，不处于暂停状态，无法恢复",
    #             action="blocked",
    #         )
        return self.start()
    def stop(self, note: Optional[str] = None) -> dict:
        """
        主动停止计时并保存会话记录
        与 reset() 的区别：
            stop()  → 保存已计时数据到统计中心，再重置计时器
            reset() → 静默丢弃数据，直接重置（用于取消/误操作场景）
        Args:
            note : 可选备注，写入 SessionRecord
        Returns:
            包含本次专注时长的状态字典
        """
        if self.timer.state == TimerState.IDLE:
            return self._build_response(
                message="⚠ 计时尚未开始，无记录可保存",
                action="blocked",
            )
        focused_seconds = self.timer.elapsed
        self.timer.stop()   # 内部调用 reset()，状态回到 IDLE
        record = self._save_record(
            focused_seconds=focused_seconds,
            is_completed=False,
            note=note,
        )
        return self._build_response(
            message=f"⏹ 已停止 | 本次专注 {record.focused_minutes:.1f} 分钟",
            action="stopped",
            extra={
                "focused_minutes": record.focused_minutes,
                "record_id":       record.record_id,
            },
        )
    # def reset(self) -> dict:
    #     """
    #     静默重置计时器
    #     不保存任何记录，适用于：
    #         - 用户误触开始后立即取消
    #         - 切换任务前清理状态
    #     Returns:
    #         状态字典
    #     """
    #     self.timer.reset()
    #     self._session_start = None
    #     return self._build_response(
    #         message="🔄 已重置",
    #         action="reset",
    #     )
    # =========================================================
    # 番茄钟专属操作
    # =========================================================
    def next_pomodoro_phase(self) -> dict:
        """
        手动跳转到番茄钟下一阶段
        逻辑：
            1. 保存当前阶段已计时数据（若 elapsed > 0）
            2. 调用 PomodoroTimer.next_phase() 推进阶段
            3. 更新会话开始时刻
        Returns:
            包含新阶段信息的状态字典
        """
        if not self.is_pomodoro:
            return self._build_response(
                message="⚠ 当前不是番茄钟模式，无法切换阶段",
                action="blocked",
            )
        pomodoro_timer: PomodoroTimer = self.timer  # type: ignore
        # 保存本阶段已有的计时数据
        elapsed = pomodoro_timer.elapsed
        if elapsed > 0 and self.timer.state != TimerState.IDLE:
            self._save_record(
                focused_seconds=elapsed,
                is_completed=(self.timer.state == TimerState.FINISHED
                              or pomodoro_timer.is_finished()),
            )
        # 推进阶段（内部自动 reset + start）
        new_phase = pomodoro_timer.next_phase()
        # 新阶段的会话开始时刻
        self._session_start = datetime.now()
        phase_label = {
            PomodoroPhase.WORK:        "🍅 工作",
            PomodoroPhase.SHORT_BREAK: "☕ 短休息",
            PomodoroPhase.LONG_BREAK:  "🛋  长休息",
        }
        return self._build_response(
            message=f"🔄 切换至：{phase_label[new_phase]}",
            action="phase_switched",
            extra={
                "new_phase":           new_phase.value,
                "new_phase_label":     phase_label[new_phase],
                "completed_pomodoros": pomodoro_timer.completed_pomodoros,
                "next_is_long_break":  (
                    pomodoro_timer.completed_pomodoros
                    % pomodoro_timer.POMODOROS_PER_ROUND
                    == pomodoro_timer.POMODOROS_PER_ROUND - 1
                ),
            },
        )
    # =========================================================
    # 切换计时模式
    # =========================================================
    # def switch_mode(
    #     self,
    #     new_mode:       TimerMode,
    #     target_seconds: Optional[float] = None,
    # ) -> dict:
    #     """
    #     切换计时模式并重建计时器
    #     规则：
    #         - 计时进行中（RUNNING）不允许切换，需先 stop() 或 pause()
    #         - 切换后原有计时数据清空（不保存），请在切换前主动 stop()
    #     Args:
    #         new_mode       : 目标计时模式 (TimerMode 枚举)
    #         target_seconds : 倒计时/正计时的目标秒数（可选）
    #                          - COUNTDOWN：不传则默认 25 分钟
    #                          - COUNTUP  ：不传则无上限
    #                          - POMODORO ：忽略此参数
    #     Returns:
    #         状态字典
    #     """
    #     if self.timer.state == TimerState.RUNNING:
    #         return self._build_response(
    #             message="⚠ 计时进行中，请先 pause() 或 stop() 再切换模式",
    #             action="blocked",
    #         )
    #     # 构建对应计时器
    #     new_timer: BaseTimer
    #     if new_mode == TimerMode.POMODORO:
    #         new_timer = PomodoroTimer()
    #     elif new_mode == TimerMode.COUNTDOWN:
    #         secs = target_seconds if target_seconds and target_seconds > 0 else 25 * 60
    #         new_timer = CountDownTimer(target_seconds=secs)
    #     else:  # COUNTUP
    #         new_timer = CountUpTimer(target_seconds=target_seconds)
    #     # 替换任务上的计时器
    #     self.task.configure_timer(new_timer)
    #     self.task.mode  = new_mode
    #     self._session_start = None
    #     return self._build_response(
    #         message=f"✅ 已切换至 [{new_mode.name}] 模式",
    #         action="mode_switched",
    #         extra={"new_mode": new_mode.name},
    #     )
    # =========================================================
    # tick：由外部调度器周期调用（每秒一次）
    # =========================================================
    def tick(self) -> dict:
        """
        驱动计时器前进，检测是否自然结束
        调用方式：
            由外部事件循环 / APScheduler / asyncio 每秒调用一次
            返回的字典可直接推送给前端（WebSocket / SSE）
        Returns:
            状态字典
            若计时自然结束，字典中包含 "event": "finished"
        """
        if self.timer.state != TimerState.RUNNING:
            # 未在运行时直接返回当前快照，不做任何操作
            return self._build_response(
                message="",
                action="idle_tick",
            )
        just_finished = self.timer.tick()  # 检测并标记 FINISHED
        if just_finished:
            focused_seconds = self.timer.elapsed
            record = self._save_record(
                focused_seconds=focused_seconds,
                is_completed=True,
            )
            return self._build_response(
                message=f"✅ 计时结束！本次专注 {record.focused_minutes:.1f} 分钟",
                action="finished",
                extra={
                    "event":           "finished",
                    "focused_minutes": record.focused_minutes,
                    "record_id":       record.record_id,
                },
            )
        # 正常运行中：返回实时快照
        return self._build_response(
            message="",
            action="ticking",
        )

    # =========================================================
    # 内部工具方法
    # =========================================================
    def _save_record(
        self,
        focused_seconds: float,
        is_completed:    bool,
        note:            Optional[str] = None,
    ) -> SessionRecord:
        """
        创建 SessionRecord 并同时归档到：
            1. user.statistics（全局统计中心）
            2. task.session_records（任务级别历史）
        Args:
            focused_seconds : 本次实际专注秒数
            is_completed    : True=自然结束，False=主动中止
            note            : 可选备注
        Returns:
            已保存的 SessionRecord 实例
        """
        started_at = self._session_start or datetime.now()
        ended_at   = datetime.now()
        # 专注时长极短（< 1 秒）时不记录，避免无效数据
        if focused_seconds < 1.0:
            # 返回一个占位记录，不写入统计
            return SessionRecord(
                record_id       = -1,
                task_id         = self.task.task_id,
                user_id         = self.user.user_id,
                mode            = self.task.mode,
                started_at      = started_at,
                ended_at        = ended_at,
                focused_seconds = focused_seconds,
                is_completed    = is_completed,
                note            = note,
            )
        record = self.user.statistics.create_and_save_record(
            task_id         = self.task.task_id,
            mode            = self.task.mode,
            started_at      = started_at,
            ended_at        = ended_at,
            focused_seconds = focused_seconds,
            is_completed    = is_completed,
            note            = note,
        )
        self.task.attach_record(record)
        return record
    def _build_response(
        self,
        message: str,
        action:  str,
        extra:   Optional[dict] = None,
    ) -> dict:
        """
        构造统一的响应字典
        所有公开方法均通过此方法返回，保证结构一致性：
        {
            "action"       : 操作标识
            "message"      : 人类可读描述
            "task_id"      : 任务ID
            "task_title"   : 任务标题
            "mode"         : 计时模式
            "state"        : 计时器状态
            "display_time" : 格式化展示时间 MM:SS
            "elapsed_sec"  : 已计时秒数
            "pomodoro_info": 番茄钟专属进度（仅番茄钟模式附加）
            ...extra        : 调用方附加的额外字段
        }
        Args:
            message : 描述文本
            action  : 操作标识符
            extra   : 额外附加字段（会合并到顶层）
        Returns:
            结构化响应字典
        """
        response = {
            "action":       action,
            "message":      message,
            "task_id":      self.task.task_id,
            "task_title":   self.task.title,
            "mode":         self.task.mode.name,
            "state":        self.timer.state.value,
            "display_time": self.timer.format_display(),
            "elapsed_sec":  round(self.timer.elapsed, 1),
        }
        # 番茄钟模式附加进度信息
        if self.is_pomodoro:
            pomodoro_timer: PomodoroTimer = self.timer  # type: ignore
            response["pomodoro_info"] = pomodoro_timer.get_progress_info()
        # 合并额外字段
        if extra:
            response.update(extra)
        return response
    
# def print_section(title: str) -> None:
#     print(f"\n{'='*50}")
#     print(f"  {title}")
#     print('='*50)
# def demo_pomodoro(user: User) -> None:
#     """演示番茄钟流程"""
#     print_section("番茄钟模式演示")
#     # 1. 创建番茄钟任务（自定义时长：3秒工作 + 2秒休息，方便演示）
#     task = user.create_task(
#         title       = "完成后端架构设计",
#         description = "设计计时器模块和统计模块",
#         due_date    = datetime(2026, 6, 1, 18, 0),
#         mode        = TimerMode.POMODORO,
#         motto       = "专注当下，每一刻都是进步！",
#     )
#     # 自定义番茄钟参数（演示用缩短时间）
#     task.configure_timer(PomodoroTimer(
#         work_seconds        = 3,
#         short_break_seconds = 2,
#         long_break_seconds  = 4,
#     ))
#     ctrl = TimerController(user=user, task=task)
#     shortcuts = ShortcutManager(ctrl)
#     shortcuts.print_bindings()
#     print(f"任务：{task.title}")
#     print(f"激励语：{task.motto}")
#     # 2. 开始计时
#     result = ctrl.start()
#     print(f"\n▶ 开始: {result['message']} | 显示: {result['display_time']}")
#     # 3. 模拟运行 1 秒后暂停
#     time.sleep(1)
#     result = shortcuts.handle("space")   # 空格暂停
#     print(f"⏸ 暂停: {result['message']} | 已计时: {result['elapsed_sec']}s")
#     # 4. 恢复并等待自然结束
#     time.sleep(0.5)
#     result = shortcuts.handle("space")   # 空格恢复
#     print(f"▶ 恢复: {result['message']}")
#     # 5. tick 循环，等待阶段结束
#     print("\n⏳ 等待工作阶段结束...")
#     finished = False
#     for _ in range(10):
#         time.sleep(0.5)
#         result = ctrl.tick()
#         if result.get("event") == "finished":
#             print(f"✅ {result['message']}")
#             finished = True
#             break
#     if finished:
#         # 6. 切换到下一阶段（短休息）
#         result = shortcuts.handle("n")
#         print(f"\n🔄 切换阶段: {result['message']}")
#         print(f"   当前阶段: {result.get('new_phase_name')} | "
#               f"已完成番茄: {result.get('completed_pomodoros')}")
#         # 等待休息结束
#         print("⏳ 等待短休息结束...")
#         for _ in range(8):
#             time.sleep(0.5)
#             result = ctrl.tick()
#             if result.get("event") == "finished":
#                 print(f"✅ {result['message']}")
#                 break
#     print(f"\n📊 任务累计专注: {task.total_focused_minutes:.2f} 分钟")
# def demo_countdown(user: User) -> None:
#     """演示倒计时流程"""
#     print_section("倒计时模式演示")
#     task = user.create_task(
#         title       = "阅读技术文档",
#         description = "阅读 FastAPI 官方文档",
#         due_date    = datetime(2026, 6, 1, 20, 0),
#         mode        = TimerMode.COUNTDOWN,
#     )
#     # 自定义倒计时 4 秒
#     task.configure_timer(CountDownTimer(target_seconds=4))
#     ctrl = TimerController(user=user, task=task)
#     result = ctrl.start()
#     print(f"▶ 倒计时开始 (4秒): {result['display_time']}")
#     # 运行 2 秒后暂停
#     time.sleep(2)
#     result = ctrl.pause()
#     print(f"⏸ 暂停: 剩余 {result['display_time']}")
#     # 恢复
#     time.sleep(0.5)
#     result = ctrl.resume()
#     print(f"▶ 恢复: 剩余 {result['display_time']}")
#     # 等待结束
#     print("⏳ 等待倒计时结束...")
#     for _ in range(8):
#         time.sleep(0.5)
#         result = ctrl.tick()
#         print(f"   剩余: {result['display_time']}", end="\r")
#         if result.get("event") == "finished":
#             print(f"\n✅ {result['message']}")
#             break
#     print(f"📊 任务累计专注: {task.total_focused_minutes:.2f} 分钟")
# def demo_countup(user: User) -> None:
#     """演示正向计时流程"""
#     print_section("正向计时模式演示")
#     task = user.create_task(
#         title       = "自由创作",
#         description = "写周报",
#         due_date    = datetime(2026, 6, 2, 12, 0),
#         mode        = TimerMode.COUNTUP,
#     )
#     # 无目标时长，纯正向计时
#     task.configure_timer(CountUpTimer())
#     ctrl = TimerController(user=user, task=task)
#     result = ctrl.start()
#     print(f"▶ 正向计时开始: {result['display_time']}")
#     time.sleep(3)
#     print(f"   已计时: {ctrl.timer.format_display()}")
#     # 主动停止
#     result = ctrl.stop()
#     print(f"⏹ 停止: {result['message']}")
#     print(f"📊 任务累计专注: {task.total_focused_minutes:.2f} 分钟")
# def demo_switch_mode(user: User) -> None:
#     """演示切换计时模式"""
#     print_section("切换计时模式演示")
#     task = user.create_task(
#         title    = "多模式任务",
#         description = "演示切换",
#         due_date = datetime(2026, 6, 3, 10, 0),
#         mode     = TimerMode.POMODORO,
#     )
#     ctrl = TimerController(user=user, task=task)
#     print(f"初始模式: {task.mode.name}")
#     # 切换到倒计时（5秒）
#     result = ctrl.switch_mode(TimerMode.COUNTDOWN, target_seconds=5)
#     print(f"切换: {result['message']} | 模式: {result['mode']}")
#     ctrl.start()
#     time.sleep(2)
#     # 切换到正向计时（需先停止）
#     ctrl.stop()
#     result = ctrl.switch_mode(TimerMode.COUNTUP)
#     print(f"切换: {result['message']} | 模式: {result['mode']}")
# def demo_statistics(user: User) -> None:
#     """演示统计查询"""
#     print_section("数据统计查询演示")
#     from datetime import date
#     # 今日统计
#     today_summary = user.statistics.get_today_summary()
#     print("📅 今日统计:")
#     for k, v in today_summary.items():
#         print(f"   {k}: {v}")
#     # 所有历史记录
#     all_records = user.statistics.get_all_records()
#     print(f"\n📚 历史会话总数: {len(all_records)} 条")
#     for r in all_records:
#         print(f"   [{r.started_at.strftime('%H:%M:%S')}] "
#               f"任务{r.task_id} | {r.mode.name:10s} | "
#               f"{r.focused_minutes:.2f}min | "
#               f"{'完成✓' if r.is_completed else '中止✗'}")
#     # 本月统计
#     now = date.today()
#     monthly = user.statistics.get_monthly(now.year, now.month)
#     total_min = sum(s.total_focused_minutes for s in monthly)
#     print(f"\n📆 本月累计专注: {total_min:.2f} 分钟")
#     # 用户整体快照
#     print("\n👤 用户完整状态:")
#     user_dict = user.to_dict()
#     print(f"   用户: {user_dict['username']}")
#     print(f"   任务总数: {user_dict['calendar']['task_count']}")
#     print(f"   今日专注: {user_dict['today']['total_focused_minutes']} 分钟")
# if __name__ == "__main__":
#     # 初始化用户
#     print_section("初始化用户")
#     user = User(user_id=1, username="Alex", email="alex@example.com")
#     print(f"✓ 用户 [{user.username}] 注册成功")
#     print(f"✓ 自动创建日历：{user.calendar.name}")
#     # 依次演示各模块
#     demo_pomodoro(user)
#     demo_countdown(user)
#     demo_countup(user)
#     demo_switch_mode(user)
#     demo_statistics(user)
#     print_section("演示完成")




