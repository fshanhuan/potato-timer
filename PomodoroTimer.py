from typing import List, Optional, Dict
from datetime import datetime, date
from abc import ABC, abstractmethod
from enum import Enum
import time


# ============================================================
# 枚举类：统一管理所有状态常量
# ============================================================

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

    @property
    def elapsed(self) -> float:
        """已累计专注秒数（排除暂停时间）"""
        if self.state == TimerState.RUNNING and self._start_time:
            return self._accumulated + (time.time() - self._start_time)
        return self._accumulated  # PAUSED / IDLE 时直接返回已累计值


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
        self._daily_map: Dict[date, DailyStats] = {}

    def add_session_record(self, record: SessionRecord) -> None:
        """将会话记录归入对应日期的 DailyStats"""
        record_date = record.started_at.date()
        if record_date not in self._daily_map:
            self._daily_map[record_date] = DailyStats(record_date)
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
            return CountDownTimer(target_seconds=25 * 60)
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
            "task_id":    self.task_id,
            "title":      self.title,
            "due_date":   self.due_date.isoformat(),
            "mode":       self.mode.name,
            "status":     self.status.value,
            "motto":      self.motto,
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


class User:
    """
    用户类（系统顶层实体）
    职责：持有日历、统计中心，提供创建任务等业务入口
    关联：1 User → 1 Calendar → N Tasks
          1 User → 1 Statistics → N DailyStats → N SessionRecords
    """
    def __init__(self, user_id: int, username: str, email: str):
        self.user_id:   int      = user_id
        self.username:  str      = username
        self.email:     str      = email

        # 核心聚合关系
        self.calendar:   Calendar   = Calendar(calendar_id=user_id, name=f"{username}的日历")
        self.statistics: Statistics = Statistics(user_id=user_id)

        # 快捷键绑定表（key=快捷键字符串, value=操作名称）
        self.shortcuts: Dict[str, str] = {
            "space": "start_pause",   # 空格：开始/暂停
            "s":     "stop",
            "r":     "reset",
            "n":     "next_phase",    # 番茄钟：切换下一阶段
        }

    def create_task(
        self,
        task_id:     int,
        title:       str,
        description: str,
        due_date:    datetime,
        mode:        TimerMode = TimerMode.POMODORO,
        motto:       str = "",
    ) -> Task:
        """创建任务并自动加入日历"""
        task = Task(task_id, title, description, due_date, mode, motto)
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