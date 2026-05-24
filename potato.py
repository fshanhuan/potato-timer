from typing import List, Optional
from datetime import datetime
from abc import ABC, abstractmethod
import time

class BaseTimer(ABC):
    """计时器抽象基类"""
#只用于继承
    def __init__(self):
        self._start_time: Optional[float] = None   # 记录开始的时间戳（秒），绝对开始时间
        self._paused: bool = False                 #是否暂停
        self._accumulated: float = 0.0            # 已经过的秒数（用于暂停恢复）
        self._pause_start: Optional[float] = None   #暂停时刻

    @abstractmethod
    def get_remaining(self) -> float:
        """返回剩余秒数，若为0表示计时结束"""
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        """计时是否已结束"""
        pass

    def start(self):
        """开始/继续计时"""
        if self._paused:
            # 从暂停恢复
            self._start_time = time.time()
            self._paused = False
        else:
            self._start_time = time.time()
            self._accumulated = 0.0
            self._paused = False

    def pause(self):
        """暂停计时"""
        if self._start_time is not None and not self._paused:
            self._paused = True
            self._pause_start = time.time()

    def reset(self):
        """重置计时器到初始状态"""
        self._start_time = None
        self._paused = False
        self._accumulated = 0.0
        self._pause_start = None

    @property
    def elapsed(self) -> float:
        """已经过的秒数（不含暂停期间）"""
        if self._paused or self._start_time is None:
            return self._accumulated
        else:
            return self._accumulated + (time.time() - self._start_time)








class Task:
    """任务类：代表具体要做的某件事"""
    def __init__(self, task_id: int, title: str, description: str, due_date: datetime, mode: int , motto: str):
        self.task_id: int = task_id
        self.title: str = title
        self.description: str = description   #用户对本次事件的一个描述，留言等 
        self.motto: str= motto                #生成的一种鼓励话语
        self.due_date: datetime = due_date    #截止时间
        self.mode: int = mode                 #这里可以为task赋予不同的模式，0——番茄钟，1——倒计时，2——正计时
        self.is_completed: bool = False
        self.completed_at: Optional[datetime] = None

    def complete(self) -> None:
        """标记任务完成"""
        self.is_completed = True
        self.completed_at = datetime.now()

    def update_due_date(self, new_date: datetime) -> None:
        """修改截止时间"""
        self.due_date = new_date

    def to_dict(self) -> dict:
        """方便后端转换为 JSON 返回给前端"""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "due_date": self.due_date.isoformat(),
            "mode": self.mode,
            "is_completed": self.is_completed
        }


class Calendar:
    """日历类：作为容器，负责管理和组织多个任务"""
    def __init__(self, calendar_id: int, name: str,date: datetime):
        self.calendar_id: int = calendar_id
        self.name: str = name
        self.tasks: List[Task] = []  # 核心关联：一个日历拥有多个 Task 对象
        self.date: datetime = date   #每天的日期记录任务

    def add_task(self, task: Task) -> None:
        """向日历中添加任务"""
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> bool:
        """根据 ID 移除任务"""
        for task in self.tasks:
            if task.task_id == task_id:
                self.tasks.remove(task)
                return True
        return False

    def get_pending_tasks(self) -> List[Task]:
        """获取所有未完成的任务，按截止日期排序"""
        pending = [t for t in self.tasks if not t.is_completed]
        return sorted(pending, key=lambda x: x.due_date)


class User:
    """用户类：系统的最高层实体，拥有自己的日历"""
    def __init__(self, user_id: int, username: str, email: str):
        self.user_id: int = user_id
        self.username: str = username
        self.email: str = email
        # 核心关联：初始化时，自动为用户绑定一个专属的 Calendar 对象
        self.calendar: Calendar = Calendar(calendar_id=user_id, name=f"{username}的日历")

    def create_new_task(self, task_id: int, title: str, description: str, due_date: datetime, priority: int = 3) -> Task:
        """业务逻辑：用户通过自己的日历创建新任务"""
        new_task = Task(task_id, title, description, due_date, priority)
        self.calendar.add_task(new_task)
        return new_task
    # 1. 注册一个新用户






current_user = User(user_id=101, username="Alex", email="alex@example.com")   #这里是可以自己改变顺序的
print(f"用户 {current_user.username} 注册成功，系统已自动为其创建：{current_user.calendar.name}")

# 2. 用户创建了两个任务 (通过 User 触发，最终存入 Calendar 的列表中)
task_api = current_user.create_new_task(
    task_id=1, 
    title="设计后端数据库模型", 
    description="使用 SQLAlchemy 设计 User 和 Task 表", 
    due_date=datetime(2026, 5, 22, 18, 0),
    priority=5
)

task_gym = current_user.create_new_task(
    task_id=2, 
    title="晚上去健身房", 
    description="有氧运动 40 分钟", 
    due_date=datetime(2026, 5, 21, 20, 0),
    priority=2
)

print(f"\n当前日历中的总任务数: {len(current_user.calendar.tasks)} 个")

# 3. 后端路由调用：获取用户今天待办的事项（按紧急程度/时间排序）
print("\n--- 待办任务清单 (按时间先后排序) ---")
todo_list = current_user.calendar.get_pending_tasks()
for task in todo_list:
    print(f"[{task.due_date.strftime('%m-%d %H:%M')}] 任务: {task.title} (优先级: {task.priority})")

# 4. 用户完成了一个任务
print("\n--- 模拟用户操作 ---")
task_gym.complete() # 标记健身完成

# 5. 再次查看剩余待办
remaining_todo = current_user.calendar.get_pending_tasks()
print(f"完成健身后，剩余待办任务数: {len(remaining_todo)} 个，下一项是: {remaining_todo[0].title}")