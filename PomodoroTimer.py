from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from abc import ABC, abstractmethod
from enum import Enum
import time
import json
import random
import re
import shutil
from pathlib import Path


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
    ABANDONED  = "abandoned"   # 已放弃


class ImportanceLevel(Enum):
    """事件重要性等级"""
    LOW      = 1   # 普通
    MEDIUM   = 2   # 重要
    HIGH     = 3   # 很重要
    CRITICAL = 4   # 紧急且重要


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
        self.target_seconds: Optional[float] = target_seconds
        

    def get_display_time(self) -> float:
        """返回已经过秒数"""
        return self.elapsed

    def is_finished(self) -> bool:
        if self.target_seconds is None:
            return False
        return self.elapsed >= self.target_seconds   #判定条件是目标秒数
    
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
            "user_id":         self.user_id,
            "mode":            self.mode.name,
            "started_at":      self.started_at.isoformat(),
            "ended_at":        self.ended_at.isoformat(),
            "focused_seconds": self.focused_seconds,
            "focused_minutes": self.focused_minutes,
            "is_completed":    self.is_completed,
            "note":            self.note,
        }

    @staticmethod
    def from_dict(data: dict) -> "SessionRecord":
        """从本地持久化数据恢复会话记录"""
        return SessionRecord(
            record_id       = int(data["record_id"]),
            task_id         = int(data.get("task_id", -1)),
            user_id         = int(data.get("user_id", 0)),
            mode            = TimerMode[data["mode"]],
            started_at      = datetime.fromisoformat(data["started_at"]),
            ended_at        = datetime.fromisoformat(data["ended_at"]),
            focused_seconds = float(data.get("focused_seconds", data.get("focused_minutes", 0) * 60)),
            is_completed    = bool(data.get("is_completed", True)),
            note            = data.get("note"),
        )


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
    def __init__(self, user_id: int, storage_path: Optional[Path] = None, autosave: bool = True):
        self.user_id:   int = user_id
        # key = date 对象，value = DailyStats
        self._daily_map: Dict[date, DailyStats] = {}   #按日期储存数据
        self._next_record_id: int = 1
        self.storage_path: Optional[Path] = storage_path
        self.autosave: bool = autosave

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
        self.save_to_file()
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
        self._next_record_id = max(self._next_record_id, record.record_id + 1)
        self.save_to_file()

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

    def get_records_between(self, start_date: date, end_date: date) -> List[SessionRecord]:
        """查询日期范围内的所有会话记录（包含开始和结束日期）"""
        records: List[SessionRecord] = []
        for day, stats in self._daily_map.items():
            if start_date <= day <= end_date:
                records.extend(stats.records)
        return records

    def get_time_usage_report(
        self,
        tasks: List["Task"],
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        统计时间使用情况，给出实际用时与计划差异，以及可能浪费的时间报告
        Args:
            tasks      : 需要纳入统计的任务列表
            start_date : 统计开始日期
            end_date   : 统计结束日期
        Returns:
            结构化报告字典，可直接给前端展示
        """
        records = self.get_records_between(start_date, end_date)
        task_map = {task.task_id: task for task in tasks}
        focused_by_task: Dict[int, float] = {}
        interrupted_seconds = 0.0
        for record in records:
            focused_by_task[record.task_id] = focused_by_task.get(record.task_id, 0.0) + record.focused_seconds
            if not record.is_completed:
                interrupted_seconds += record.focused_seconds

        task_reports = []
        total_planned_seconds = 0.0
        total_actual_seconds = 0.0
        overdue_unfinished = 0
        for task in tasks:
            actual_seconds = focused_by_task.get(task.task_id, 0.0)
            due_in_range = task.due_date is not None and start_date <= task.due_date.date() <= end_date
            if not due_in_range and actual_seconds <= 0:
                continue
            planned_seconds = task.planned_minutes * 60
            diff_seconds = actual_seconds - planned_seconds
            total_planned_seconds += planned_seconds
            total_actual_seconds += actual_seconds
            is_overdue = (
                task.due_date is not None
                and task.status != TaskStatus.COMPLETED
                and task.due_date < datetime.now()
            )
            if is_overdue:
                overdue_unfinished += 1
            task_reports.append({
                "task_id": task.task_id,
                "title": task.title,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "planned_minutes": round(planned_seconds / 60, 2),
                "actual_minutes": round(actual_seconds / 60, 2),
                "difference_minutes": round(diff_seconds / 60, 2),
                "status": task.status.value,
                "is_overdue": is_overdue,
            })
        for task_id, actual_seconds in focused_by_task.items():
            if task_id in task_map:
                continue
            total_actual_seconds += actual_seconds
            task_reports.append({
                "task_id": task_id,
                "title": "历史任务",
                "due_date": None,
                "planned_minutes": 0.0,
                "actual_minutes": round(actual_seconds / 60, 2),
                "difference_minutes": round(actual_seconds / 60, 2),
                "status": "archived",
                "is_overdue": False,
            })

        idle_or_unfinished_seconds = max(0.0, total_planned_seconds - total_actual_seconds)
        suggestions = []
        if idle_or_unfinished_seconds > 0:
            suggestions.append("实际专注少于计划，建议缩小单个任务粒度或提前安排开始时间")
        if interrupted_seconds > 0:
            suggestions.append("存在中断会话，建议把易被打断的任务安排在低干扰时段")
        if overdue_unfinished > 0:
            suggestions.append("存在逾期未完成任务，建议优先处理高重要性和临近截止任务")

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "planned_minutes": round(total_planned_seconds / 60, 2),
            "actual_minutes": round(total_actual_seconds / 60, 2),
            "difference_minutes": round((total_actual_seconds - total_planned_seconds) / 60, 2),
            "time_waste_minutes": round((idle_or_unfinished_seconds + interrupted_seconds) / 60, 2),
            "interrupted_minutes": round(interrupted_seconds / 60, 2),
            "overdue_unfinished": overdue_unfinished,
            "tasks": task_reports,
            "suggestions": suggestions,
        }

    def get_total_focused_today(self) -> float:
        """便捷方法：获取今日总专注分钟数"""
        stats = self.get_daily(date.today())
        return stats.total_focused_minutes if stats else 0.0

    def to_dict(self) -> dict:
        """将统计中心序列化为可写入本地文件的字典"""
        records = []
        for stats in self._daily_map.values():
            records.extend(record.to_dict() for record in stats.records)
        return {
            "user_id": self.user_id,
            "next_record_id": self._next_record_id,
            "records": records,
        }

    def load_from_dict(self, data: dict) -> None:
        """从字典恢复统计数据"""
        self._daily_map = {}
        self._next_record_id = int(data.get("next_record_id", 1))
        old_autosave = self.autosave
        self.autosave = False
        for item in data.get("records", []):
            record = SessionRecord.from_dict(item)
            self._archive(record)
            self._next_record_id = max(self._next_record_id, record.record_id + 1)
        self.autosave = old_autosave

    def load_from_file(self) -> None:
        """从本地文件加载统计数据；文件不存在时保持空统计"""
        if not self.storage_path or not self.storage_path.exists():
            return
        with self.storage_path.open("r", encoding="utf-8") as file:
            self.load_from_dict(json.load(file))

    def save_to_file(self) -> None:
        """将统计数据保存到本地文件"""
        if not self.autosave or not self.storage_path:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.storage_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=2)
        tmp_path.replace(self.storage_path)


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
        due_date:    Optional[datetime],
        mode:        TimerMode,
        motto:       str = "",
        importance:  ImportanceLevel = ImportanceLevel.MEDIUM,
        planned_minutes: float = 25.0,
        reminder_at: Optional[datetime] = None,
    ):
        self.task_id:     int       = task_id
        self.title:       str       = title
        self.description: str       = description  # 任务描述/留言
        self.motto:       str       = motto        # AI 生成的鼓励话语
        self.due_date:    Optional[datetime] = due_date
        self.mode:        TimerMode = mode
        self.importance:   ImportanceLevel = importance
        self.planned_minutes: float = max(0.0, planned_minutes)
        self.reminder_at: Optional[datetime] = reminder_at
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

    def update_due_date(self, new_date: Optional[datetime]) -> None:
        self.due_date = new_date

    def attach_record(self, record: SessionRecord) -> None:
        """关联一次计时记录到当前任务"""
        self.session_records.append(record)

    @property
    def total_focused_seconds(self) -> float:
        """当前任务累计专注秒数"""
        return sum(record.focused_seconds for record in self.session_records)

    @property
    def total_focused_minutes(self) -> float:
        """当前任务累计专注分钟数"""
        return round(self.total_focused_seconds / 60, 2)

    def build_reminder(self, now: Optional[datetime] = None) -> dict:
        """
        根据事件重要性和目标到期时间生成提醒程度值
        未设置截止日期的任务不需要提醒，只返回 0；具体提示方式由前端决定
        """
        now = now or datetime.now()
        if self.status in (TaskStatus.COMPLETED, TaskStatus.ABANDONED) or self.due_date is None:
            minutes_left = None
            reminder_degree = 0
            level = "none"
        else:
            minutes_left = (self.due_date - now).total_seconds() / 60
            if minutes_left <= 0:
                reminder_degree = 4
                level = "expired"
            elif self.importance == ImportanceLevel.CRITICAL or minutes_left <= 15:
                reminder_degree = 3
                level = "high"
            elif self.importance == ImportanceLevel.HIGH or minutes_left <= 60:
                reminder_degree = 2
                level = "medium"
            else:
                reminder_degree = 1
                level = "low"
        return {
            "task_id": self.task_id,
            "title": self.title,
            "importance": self.importance.name,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "minutes_left": round(minutes_left, 1) if minutes_left is not None else None,
            "reminder_degree": reminder_degree,
            "level": level,
        }

    def to_dict(self) -> dict:
        return {
            "task_id":               self.task_id,
            "title":                 self.title,
            "description":           self.description,
            "motto":                 self.motto,
            "due_date":              self.due_date.isoformat() if self.due_date else None,
            "importance":            self.importance.name,
            "planned_minutes":        self.planned_minutes,
            "reminder_at":            self.reminder_at.isoformat() if self.reminder_at else None,
            "mode":                  self.mode.name,
            "status":                self.status.value,
            "created_at":            self.created_at.isoformat(),
            "completed_at":          self.completed_at.isoformat() if self.completed_at else None,
            "total_focused_minutes": self.total_focused_minutes,
        }

    @staticmethod
    def from_dict(data: dict) -> "Task":
        """从持久化数据恢复任务"""
        mode = TimerMode[data["mode"]]
        due_date = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
        reminder_at = datetime.fromisoformat(data["reminder_at"]) if data.get("reminder_at") else None
        task = Task(
            task_id         = int(data["task_id"]),
            title           = data["title"],
            description     = data.get("description", ""),
            due_date        = due_date,
            mode            = mode,
            motto           = data.get("motto", ""),
            importance      = ImportanceLevel[data["importance"]],
            planned_minutes = float(data.get("planned_minutes", 25.0)),
            reminder_at     = reminder_at,
        )
        task.status = TaskStatus(data.get("status", "pending"))
        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])
        return task


class Calendar:
    """
    日历类
    职责：按日期组织和管理多个 Task，是 User 与 Task 之间的中间层
    """
    def __init__(self, calendar_id: int, name: str, storage_path: Optional[Path] = None):
        self.calendar_id: int        = calendar_id
        self.name:        str        = name
        self.tasks:       List[Task] = []
        self.storage_path: Optional[Path] = storage_path

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
        return self.sort_tasks_by_time(pending)

    def get_tasks_by_date(self, query_date: date) -> List[Task]:
        """获取某一天截止的任务"""
        return [t for t in self.tasks if t.due_date and t.due_date.date() == query_date]

    def get_tasks_by_mode(self, mode: TimerMode) -> List[Task]:
        """按计时模式筛选任务"""
        return [t for t in self.tasks if t.mode == mode]

    def sort_tasks_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """按截止时间排序；未设置截止日期的任务排在最后"""
        source = self.tasks if tasks is None else tasks
        return sorted(
            source,
            key=lambda task: (
                task.due_date is None,
                task.due_date or datetime.max,
            ),
        )

    def sort_tasks_by_priority(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """按优先级排序；优先级越高越靠前，同优先级再按截止时间排序"""
        source = self.tasks if tasks is None else tasks
        return sorted(
            source,
            key=lambda task: (
                -task.importance.value,
                task.due_date is None,
                task.due_date or datetime.max,
            ),
        )

    def get_reminders(self, now: Optional[datetime] = None) -> List[dict]:
        """生成所有未完成任务的提醒信息"""
        now = now or datetime.now()
        reminders = [
            task.build_reminder(now)
            for task in self.tasks
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.ABANDONED)
            and task.due_date is not None
        ]
        return sorted(
            reminders,
            key=lambda item: (
                -item["reminder_degree"],
                item["minutes_left"],
            ),
        )

    def generate_day_plan(self, query_date: date) -> dict:
        """根据当天任务生成日计划"""
        day_tasks = sorted(
            self.get_tasks_by_date(query_date),
            key=lambda task: (-task.importance.value, task.due_date or datetime.max),
        )
        plan_items = []
        cursor = datetime.combine(query_date, datetime.min.time()).replace(hour=9)
        for task in day_tasks:
            start_time = max(cursor, task.created_at if task.created_at.date() == query_date else cursor)
            end_time = start_time + timedelta(minutes=task.planned_minutes)
            plan_items.append({
                "task_id": task.task_id,
                "title": task.title,
                "importance": task.importance.name,
                "planned_minutes": task.planned_minutes,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "status": task.status.value,
            })
            cursor = end_time
        return {
            "date": query_date.isoformat(),
            "total_planned_minutes": round(sum(task.planned_minutes for task in day_tasks), 2),
            "items": plan_items,
        }

    def generate_week_plan(self, any_day_in_week: date) -> dict:
        """根据某天所在周生成周计划（周一到周日）"""
        monday = any_day_in_week - timedelta(days=any_day_in_week.weekday())
        days = [self.generate_day_plan(monday + timedelta(days=i)) for i in range(7)]
        return {
            "week_start": monday.isoformat(),
            "week_end": (monday + timedelta(days=6)).isoformat(),
            "total_planned_minutes": round(sum(day["total_planned_minutes"] for day in days), 2),
            "days": days,
        }

    def to_dict(self) -> dict:
        return {
            "calendar_id": self.calendar_id,
            "name":        self.name,
            "task_count":  len(self.tasks),
            "tasks":       [t.to_dict() for t in self.tasks],
        }

    @staticmethod
    def from_dict(data: dict) -> "Calendar":
        """从持久化数据恢复日历及所有任务"""
        calendar = Calendar(
            calendar_id=int(data["calendar_id"]),
            name=data["name"],
        )
        for task_data in data.get("tasks", []):
            calendar.add_task(Task.from_dict(task_data))
        return calendar

    def save_to_file(self) -> None:
        """将日历（含所有任务）保存到本地文件"""
        if not self.storage_path:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "calendar_id": self.calendar_id,
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks],
        }
        tmp_path = self.storage_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        tmp_path.replace(self.storage_path)

    def load_from_file(self) -> None:
        """从本地文件加载日历及所有任务；文件不存在时保持空日历"""
        if not self.storage_path or not self.storage_path.exists():
            return
        with self.storage_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self.calendar_id = int(data.get("calendar_id", self.calendar_id))
        self.name = data.get("name", self.name)
        self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
    

class MottoProvider:
    """
    本地 motto 读取器
    支持两种文件格式：
        1. 普通行：专注当下，每一分钟都算数
        2. 分阶段行：work|开始深度工作；short_break|起身喝水；long_break|好好休息
    """
    DEFAULT_MOTTOS = [
        "专注当下，每一分钟都算数",
        "先完成最小的一步，再完成下一步",
        "保持节奏，比一次冲刺更重要",
    ]

    def __init__(self, motto_path: Optional[Path] = None):
        self.motto_path: Optional[Path] = motto_path

    def get_random_motto(self, phase: Optional[Any] = None) -> str:
        """从本地文件随机读取一句 motto；文件不存在时使用默认内容"""
        if isinstance(phase, PomodoroPhase):
            phase = phase.value
        mottos = self._load_mottos(phase)
        return random.choice(mottos)

    def _load_mottos(self, phase: Optional[str]) -> List[str]:
        if not self.motto_path or not self.motto_path.exists():
            return self.DEFAULT_MOTTOS
        plain_mottos: List[str] = []
        phase_mottos: List[str] = []
        with self.motto_path.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "|" in line:
                    line_phase, text = line.split("|", 1)
                    if phase and line_phase.strip().lower() == phase.lower():
                        phase_mottos.append(text.strip())
                else:
                    plain_mottos.append(line)
        return phase_mottos or plain_mottos or self.DEFAULT_MOTTOS


class UserManager:
    """
    用户管理器
    以昵称作为本地统计数据的身份标准：昵称相同则加载同一份统计，昵称不同则互不影响
    """
    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        motto_path: Optional[Path] = None,
    ):
        base_dir = Path(__file__).resolve().parent
        self.storage_dir: Path = storage_dir or (Path.cwd() / "local_user_data")
        self.motto_provider = MottoProvider(motto_path or (base_dir / "mottos.txt"))

    def create_user(self, nickname: str) -> "User":
        """创建或加载用户；昵称相同会自动加载历史统计数据、计划和任务"""
        clean_name = nickname.strip()
        if not clean_name:
            raise ValueError("用户昵称不能为空")
        user_id = self._build_user_id(clean_name)
        safe_name = self._safe_filename(clean_name)
        stats_path = self.storage_dir / f"{safe_name}_stats.json"
        plans_path = self.storage_dir / f"{safe_name}_plans.json"
        tasks_path = self.storage_dir / f"{safe_name}_tasks.json"
        return User(
            user_id=user_id,
            username=clean_name,
            statistics_path=stats_path,
            plans_path=plans_path,
            tasks_path=tasks_path,
            motto_provider=self.motto_provider,
            load_statistics=True,
            load_plans=True,
            load_tasks=True,
        )

    @staticmethod
    def _safe_filename(nickname: str) -> str:
        safe = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", nickname.strip())
        return safe or "user"

    @staticmethod
    def _build_user_id(nickname: str) -> int:
        return sum((index + 1) * ord(char) for index, char in enumerate(nickname))


class FocusPlan:
    """
    计划表
    职责：根据起止日期、选中日期和目标专注时长生成计划，并结合统计数据检查进度
    """
    def __init__(
        self,
        plan_id: int,
        title: str,
        start_date: date,
        end_date: date,
        daily_focus_minutes: Optional[float] = None,
        total_focus_minutes: Optional[float] = None,
        selected_dates: Optional[List[date]] = None,
    ):
        if end_date < start_date:
            raise ValueError("截止日期不能早于开始日期")
        has_daily = daily_focus_minutes is not None and daily_focus_minutes > 0
        has_total = total_focus_minutes is not None and total_focus_minutes > 0
        if has_daily == has_total:
            raise ValueError("每天专注时长和总专注时长必须二选一填写")

        self.plan_id: int = plan_id
        self.title: str = title
        self.start_date: date = start_date
        self.end_date: date = end_date
        self.selected_dates: List[date] = self._normalize_selected_dates(
            start_date=start_date,
            end_date=end_date,
            selected_dates=selected_dates,
        )
        if not self.selected_dates:
            raise ValueError("计划至少需要选择一天")

        self.total_days: int = len(self.selected_dates)
        if has_daily:
            self.daily_focus_minutes: float = float(daily_focus_minutes)
            self.total_focus_minutes: float = round(self.daily_focus_minutes * self.total_days, 2)
        else:
            self.total_focus_minutes = float(total_focus_minutes)
            self.daily_focus_minutes = round(self.total_focus_minutes / self.total_days, 2)
        self.created_at: datetime = datetime.now()

    @staticmethod
    def _normalize_selected_dates(
        start_date: date,
        end_date: date,
        selected_dates: Optional[List[date]],
    ) -> List[date]:
        """整理用户选择的日期；未选择时默认包含起止日期内的每一天"""
        if selected_dates is None:
            total_days = (end_date - start_date).days + 1
            return [start_date + timedelta(days=i) for i in range(total_days)]
        normalized = sorted(set(selected_dates))
        for selected in normalized:
            if selected < start_date or selected > end_date:
                raise ValueError("选择的日期必须位于开始日期和截止日期之间")
        return normalized

    def get_day_plan(self, query_date: date) -> dict:
        """查看计划范围内任意一天的计划安排"""
        is_selected = query_date in self.selected_dates
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "date": query_date.isoformat(),
            "in_range": self.start_date <= query_date <= self.end_date,
            "is_selected": is_selected,
            "planned_minutes": self.daily_focus_minutes if is_selected else 0.0,
        }

    def get_schedule(self) -> List[dict]:
        """生成整个计划表"""
        return [self.get_day_plan(day) for day in self.selected_dates]

    def get_progress_report(
        self,
        statistics: Statistics,
        query_date: Optional[date] = None,
    ) -> dict:
        """
        结合历史统计检查计划进度
        query_date 表示统计到哪一天；不传时默认今天
        """
        query_date = query_date or date.today()
        actual_by_date = self._actual_minutes_by_date(statistics)
        total_actual_minutes = round(sum(actual_by_date.values()), 2)
        elapsed_selected_dates = [
            day for day in self.selected_dates
            if day <= min(query_date, self.end_date)
        ]
        expected_minutes = round(len(elapsed_selected_dates) * self.daily_focus_minutes, 2)
        remaining_minutes = max(0.0, round(self.total_focus_minutes - total_actual_minutes, 2))
        future_selected_dates = [
            day for day in self.selected_dates
            if day >= query_date and day <= self.end_date
        ]
        required_daily_minutes = (
            round(remaining_minutes / len(future_selected_dates), 2)
            if future_selected_dates else 0.0
        )
        progress_percent = (
            round(total_actual_minutes / self.total_focus_minutes * 100, 2)
            if self.total_focus_minutes > 0 else 0.0
        )
        expected_progress_percent = (
            round(expected_minutes / self.total_focus_minutes * 100, 2)
            if self.total_focus_minutes > 0 else 0.0
        )
        gap_minutes = round(total_actual_minutes - expected_minutes, 2)
        if total_actual_minutes >= self.total_focus_minutes:
            status = "completed"
            status_message = "计划已完成"
        elif gap_minutes >= 0:
            status = "on_track"
            status_message = "进度正常或领先"
        else:
            status = "behind"
            status_message = "进度落后，需要补足专注时间"

        daily_reports = []
        for day in self.selected_dates:
            planned = self.daily_focus_minutes
            actual = actual_by_date.get(day, 0.0)
            daily_reports.append({
                "date": day.isoformat(),
                "planned_minutes": planned,
                "actual_minutes": round(actual, 2),
                "difference_minutes": round(actual - planned, 2),
                "is_completed": actual >= planned,
            })

        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "selected_dates": [day.isoformat() for day in self.selected_dates],
            "daily_focus_minutes": self.daily_focus_minutes,
            "total_focus_minutes": self.total_focus_minutes,
            "actual_minutes": total_actual_minutes,
            "expected_minutes_by_query_date": expected_minutes,
            "gap_minutes": gap_minutes,
            "remaining_minutes": remaining_minutes,
            "required_daily_minutes": required_daily_minutes,
            "progress_percent": progress_percent,
            "expected_progress_percent": expected_progress_percent,
            "status": status,
            "status_message": status_message,
            "daily_reports": daily_reports,
        }

    def _actual_minutes_by_date(self, statistics: Statistics) -> Dict[date, float]:
        records = statistics.get_records_between(self.start_date, self.end_date)
        selected_set = set(self.selected_dates)
        actual_by_date: Dict[date, float] = {day: 0.0 for day in self.selected_dates}
        for record in records:
            record_date = record.started_at.date()
            if record_date in selected_set:
                actual_by_date[record_date] += record.focused_minutes
        return actual_by_date

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "selected_dates": [day.isoformat() for day in self.selected_dates],
            "daily_focus_minutes": self.daily_focus_minutes,
            "total_focus_minutes": self.total_focus_minutes,
            "created_at": self.created_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "FocusPlan":
        """从本地持久化数据恢复计划表"""
        plan = FocusPlan(
            plan_id=int(data["plan_id"]),
            title=data["title"],
            start_date=datetime.fromisoformat(data["start_date"]).date(),
            end_date=datetime.fromisoformat(data["end_date"]).date(),
            daily_focus_minutes=float(data["daily_focus_minutes"]),
            selected_dates=[
                datetime.fromisoformat(day).date()
                for day in data.get("selected_dates", [])
            ],
        )
        plan.total_focus_minutes = float(data.get("total_focus_minutes", plan.total_focus_minutes))
        if data.get("created_at"):
            plan.created_at = datetime.fromisoformat(data["created_at"])
        return plan


class User:
    """
    用户类（系统顶层实体）
    职责：持有日历、统计中心，提供创建任务等业务入口
    关联：1 User → 1 Calendar → N Tasks
          1 User → 1 Statistics → N DailyStats → N SessionRecords
    """
    _SUPPORTED_AVATAR_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

    def __init__(
        self,
        user_id: int,
        username: str,
        statistics_path: Optional[Path] = None,
        plans_path: Optional[Path] = None,
        tasks_path: Optional[Path] = None,
        avatar_path: Optional[Path] = None,
        motto_provider: Optional[MottoProvider] = None,
        load_statistics: bool = False,
        load_plans: bool = False,
        load_tasks: bool = False,
    ):
        self.user_id:   int      = user_id
        self.username:  str      = username
        self.statistics_path: Optional[Path] = statistics_path
        self.plans_path: Optional[Path] = plans_path
        self.tasks_path: Optional[Path] = tasks_path
        self.avatar_path: Optional[Path] = avatar_path
        self.motto_provider: MottoProvider = motto_provider or MottoProvider()
        self._next_task_id: int = 1
        self._next_plan_id: int = 1
        # 核心聚合关系
        self.calendar:   Calendar   = Calendar(
            calendar_id=user_id, name=f"{username}的日历", storage_path=tasks_path,
        )
        self.statistics: Statistics = Statistics(user_id=user_id, storage_path=statistics_path)
        self.focus_plans: List[FocusPlan] = []
        if load_statistics:
            self.statistics.load_from_file()
        if load_plans:
            self.load_focus_plans()
        if load_tasks:
            self.load_tasks()


    def create_task(
        self,
        title:       str,
        description: str,
        due_date:    Optional[datetime] = None,
        mode:        TimerMode = TimerMode.POMODORO,
        motto:       str = "",
        importance:  ImportanceLevel = ImportanceLevel.MEDIUM,
        planned_minutes: float = 25.0,
        reminder_at: Optional[datetime] = None,
        
    ) -> Task:
        """创建任务并自动加入日历"""
        if not motto:
            motto = self.get_random_motto(PomodoroPhase.WORK)
        task = Task(
            task_id     = self._next_task_id,
            title       = title,
            description = description,
            due_date    = due_date,
            mode        = mode,
            motto       = motto,
            importance  = importance,
            planned_minutes = planned_minutes,
            reminder_at = reminder_at,
        )
        self._next_task_id += 1
        self.calendar.add_task(task)
        self.save_tasks()
        return task

    def create_tasks_from_arrangements(self, arrangements: List[Dict[str, Any]]) -> List[Task]:
        """
        输入安排列表，批量创建任务
        arrangement 支持字段：title、description、due_date、mode、motto、importance、planned_minutes、reminder_at
        """
        created_tasks: List[Task] = []
        for item in arrangements:
            due_date = item.get("due_date")
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date)
            reminder_at = item.get("reminder_at")
            if isinstance(reminder_at, str):
                reminder_at = datetime.fromisoformat(reminder_at)
            mode = item.get("mode", TimerMode.POMODORO)
            if isinstance(mode, str):
                mode = TimerMode[mode.upper()]
            importance = item.get("importance", ImportanceLevel.MEDIUM)
            if isinstance(importance, str):
                importance = ImportanceLevel[importance.upper()]
            elif isinstance(importance, int):
                importance = ImportanceLevel(importance)
            created_tasks.append(self.create_task(
                title=item.get("title", "未命名任务"),
                description=item.get("description", ""),
                due_date=due_date,
                mode=mode,
                motto=item.get("motto", ""),
                importance=importance,
                planned_minutes=float(item.get("planned_minutes", 25.0)),
                reminder_at=reminder_at,
            ))
        return created_tasks

    def generate_day_plan(self, query_date: date) -> dict:
        """生成日计划"""
        return self.calendar.generate_day_plan(query_date)

    def generate_week_plan(self, any_day_in_week: date) -> dict:
        """生成周计划"""
        return self.calendar.generate_week_plan(any_day_in_week)

    def get_reminders(self, now: Optional[datetime] = None) -> List[dict]:
        """获取重要事件提醒"""
        return self.calendar.get_reminders(now)

    def sort_tasks_by_time(self) -> List[Task]:
        """按截止时间排序当前用户的全部任务"""
        return self.calendar.sort_tasks_by_time()

    def sort_tasks_by_priority(self) -> List[Task]:
        """按优先级排序当前用户的全部任务"""
        return self.calendar.sort_tasks_by_priority()

    def get_time_usage_report(self, start_date: date, end_date: date) -> dict:
        """统计时间使用情况，并与计划进行对比"""
        return self.statistics.get_time_usage_report(self.calendar.tasks, start_date, end_date)

    def create_focus_plan(
        self,
        title: str,
        start_date: Any,
        end_date: Any,
        daily_focus_minutes: Optional[float] = None,
        total_focus_minutes: Optional[float] = None,
        selected_dates: Optional[List[Any]] = None,
    ) -> FocusPlan:
        """创建计划表，支持每天专注时长或总专注时长二选一"""
        parsed_start = self._parse_date(start_date)
        parsed_end = self._parse_date(end_date)
        parsed_selected_dates = (
            [self._parse_date(day) for day in selected_dates]
            if selected_dates is not None else None
        )
        plan = FocusPlan(
            plan_id=self._next_plan_id,
            title=title,
            start_date=parsed_start,
            end_date=parsed_end,
            daily_focus_minutes=daily_focus_minutes,
            total_focus_minutes=total_focus_minutes,
            selected_dates=parsed_selected_dates,
        )
        self._next_plan_id += 1
        self.focus_plans.append(plan)
        self.save_focus_plans()
        return plan

    def get_focus_plan(self, plan_id: int) -> Optional[FocusPlan]:
        """根据计划 ID 查询计划表"""
        return next((plan for plan in self.focus_plans if plan.plan_id == plan_id), None)

    def get_focus_plan_day(self, plan_id: int, query_date: Any) -> dict:
        """查看某个计划中任意一天的计划安排"""
        plan = self.get_focus_plan(plan_id)
        if not plan:
            return {"message": "计划不存在"}
        return plan.get_day_plan(self._parse_date(query_date))

    def get_focus_plan_progress(self, plan_id: int, query_date: Optional[Any] = None) -> dict:
        """对比计划进度，检查当前完成情况"""
        plan = self.get_focus_plan(plan_id)
        if not plan:
            return {"message": "计划不存在"}
        parsed_query_date = self._parse_date(query_date) if query_date is not None else None
        return plan.get_progress_report(self.statistics, parsed_query_date)

    def get_random_motto(self, phase: Optional[Any] = None) -> str:
        """从本地 motto 文件随机读取一句话，可按阶段筛选"""
        return self.motto_provider.get_random_motto(phase)

    def save_statistics(self) -> None:
        """手动保存当前用户统计数据到本地"""
        self.statistics.save_to_file()

    def save_tasks(self) -> None:
        """将任务列表保存到本地文件"""
        if not self.tasks_path:
            return
        self.tasks_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "user_id": self.user_id,
            "username": self.username,
            "avatar_path": str(self.avatar_path) if self.avatar_path else None,
            "next_task_id": self._next_task_id,
            "calendar": self.calendar.to_dict(),
        }
        tmp_path = self.tasks_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        tmp_path.replace(self.tasks_path)

    def load_tasks(self) -> None:
        """从本地文件加载任务列表；文件不存在时保持空日历"""
        if not self.tasks_path or not self.tasks_path.exists():
            return
        with self.tasks_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self._next_task_id = int(data.get("next_task_id", 1))
        raw_avatar = data.get("avatar_path")
        self.avatar_path = Path(raw_avatar) if raw_avatar else None
        if "calendar" in data:
            self.calendar = Calendar.from_dict(data["calendar"])
            self.calendar.storage_path = self.tasks_path

    def load_focus_plans(self) -> None:
        """从本地文件加载计划表；文件不存在时保持空计划"""
        if not self.plans_path or not self.plans_path.exists():
            return
        with self.plans_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self.focus_plans = [
            FocusPlan.from_dict(item)
            for item in data.get("focus_plans", [])
        ]
        self._next_plan_id = max(
            [plan.plan_id for plan in self.focus_plans],
            default=0,
        ) + 1

    def save_focus_plans(self) -> None:
        """将计划表保存到本地文件"""
        if not self.plans_path:
            return
        self.plans_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "user_id": self.user_id,
            "username": self.username,
            "next_plan_id": self._next_plan_id,
            "focus_plans": [plan.to_dict() for plan in self.focus_plans],
        }
        tmp_path = self.plans_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        tmp_path.replace(self.plans_path)

    @staticmethod
    def _parse_date(value: Any) -> date:
        """解析 date / datetime / ISO 字符串为 date"""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value).date()
        raise ValueError("日期必须是 date、datetime 或 ISO 格式字符串")

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

    # ---------- 头像管理 ----------

    def set_avatar(self, source_path: Any) -> Path:
        """
        设置用户头像：将本地图片复制到用户数据目录
        Args:
            source_path: 本地图片文件路径（str 或 Path）
        Returns:
            新头像文件的 Path
        Raises:
            ValueError: 文件不存在、不是图片、或文件过大
        """
        source = Path(source_path)
        if not source.is_file():
            raise ValueError(f"头像源文件不存在: {source}")
        ext = source.suffix.lower()
        if ext not in self._SUPPORTED_AVATAR_EXTS:
            raise ValueError(f"不支持的图片格式 {ext}，支持: {', '.join(sorted(self._SUPPORTED_AVATAR_EXTS))}")
        max_size = 5 * 1024 * 1024
        if source.stat().st_size > max_size:
            raise ValueError(f"头像文件不能超过 5MB")
        avatar_dir = self._avatar_dir()
        avatar_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", self.username.strip()) or "user"
        dest = avatar_dir / f"{safe_name}_avatar{ext}"
        # 删除旧头像（可能扩展名不同）
        self._clean_old_avatars(avatar_dir, safe_name, keep_ext=ext)
        shutil.copy2(source, dest)
        self.avatar_path = dest
        self.save_tasks()
        return dest

    def remove_avatar(self) -> None:
        """删除用户头像"""
        if self.avatar_path and self.avatar_path.is_file():
            self.avatar_path.unlink()
        self.avatar_path = None
        self.save_tasks()

    def get_avatar_path(self) -> Optional[Path]:
        """返回当前有效头像路径，文件不存在时返回 None"""
        if self.avatar_path and self.avatar_path.is_file():
            return self.avatar_path
        return None

    def _avatar_dir(self) -> Path:
        """头像存储目录"""
        if self.tasks_path:
            return self.tasks_path.parent / "avatars"
        return Path("local_user_data") / "avatars"

    @staticmethod
    def _clean_old_avatars(avatar_dir: Path, safe_name: str, keep_ext: str) -> None:
        """删除同一用户的老头像文件（扩展名可能不同）"""
        for ext in User._SUPPORTED_AVATAR_EXTS:
            if ext == keep_ext:
                continue
            old = avatar_dir / f"{safe_name}_avatar{ext}"
            if old.is_file():
                old.unlink()

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "avatar_path": str(self.avatar_path) if self.avatar_path else None,
            "statistics_path": str(self.statistics_path) if self.statistics_path else None,
            "plans_path": str(self.plans_path) if self.plans_path else None,
            "calendar": self.calendar.to_dict(),
            "focus_plans": [plan.to_dict() for plan in self.focus_plans],
            "today": self.get_today_summary(),
        }
    
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
    



def demo_task_reminder_plan_statistics() -> None:
    """主函数测试：用户创建、本地统计加载、motto、排序、计划和统计"""
    manager = UserManager()
    user = manager.create_user("测试用户")
    other_user = manager.create_user("另一个用户")
    now = datetime.now()
    print("=== 用户创建与本地统计加载 ===")
    print(user.to_dict()["username"], user.statistics_path)
    print("同昵称会加载同一份统计；昵称改变后使用另一份统计：", other_user.statistics_path)
    print("work motto:", user.get_random_motto(PomodoroPhase.WORK))
    print("short_break motto:", user.get_random_motto(PomodoroPhase.SHORT_BREAK))
    print("long_break motto:", user.get_random_motto(PomodoroPhase.LONG_BREAK))

    user.create_tasks_from_arrangements([
        {
            "title": "完成课程作业",
            "description": "有截止日期，高优先级，需要参与提醒和计划",
            "due_date": (now + timedelta(minutes=30)).isoformat(),
            "importance": "high",
            "planned_minutes": 60,
        },
        {
            "title": "整理阅读笔记",
            "description": "无截止日期，只统计时间数据，不生成提醒",
            "importance": "medium",
            "planned_minutes": 30,
        },
        {
            "title": "提交项目报告",
            "description": "紧急任务，提醒程度应该更高",
            "due_date": (now + timedelta(minutes=10)).isoformat(),
            "importance": "critical",
            "planned_minutes": 90,
        },
    ])

    print("=== 按时间排序 ===")
    for task in user.sort_tasks_by_time():
        print(task.task_id, task.title, task.due_date, task.importance.name)

    print("\n=== 按优先级排序 ===")
    for task in user.sort_tasks_by_priority():
        print(task.task_id, task.title, task.importance.name, task.due_date)

    print("\n=== 提醒程度（无截止日期任务不会出现）===")
    for reminder in user.get_reminders(now):
        print(reminder)

    print("\n=== 今日计划 ===")
    print(user.generate_day_plan(now.date()))

    no_due_task = user.calendar.get_task_by_id(2)
    if no_due_task:
        controller = TimerController(user=user, task=no_due_task)
        controller.start()
        time.sleep(1.1)
        controller.stop(note="测试无截止日期任务统计")

    print("\n=== 时间使用报告 ===")
    print(user.get_time_usage_report(now.date(), now.date()))

    print("\n=== 计划表：每天专注时长 ===")
    daily_plan = user.create_focus_plan(
        title="期末复习计划",
        start_date=now.date(),
        end_date=now.date() + timedelta(days=6),
        daily_focus_minutes=60,
        selected_dates=[
            now.date(),
            now.date() + timedelta(days=2),
            now.date() + timedelta(days=4),
        ],
    )
    print(daily_plan.to_dict())
    print("查看任意一天:", user.get_focus_plan_day(daily_plan.plan_id, now.date() + timedelta(days=2)))
    print("进度报告:", user.get_focus_plan_progress(daily_plan.plan_id, now.date()))

    print("\n=== 计划表：总专注时长 ===")
    total_plan = user.create_focus_plan(
        title="项目冲刺计划",
        start_date=now.date(),
        end_date=now.date() + timedelta(days=3),
        total_focus_minutes=240,
    )
    print(total_plan.to_dict())
    print("进度报告:", user.get_focus_plan_progress(total_plan.plan_id, now.date()))


if __name__ == "__main__":
    demo_task_reminder_plan_statistics()




