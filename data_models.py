"""
data_models.py
数据模型定义：Task, PomodoroRecord, User, Calendar, Plan
符合小组数据合同（2026-05-27）
"""

from typing import List, Optional
from datetime import datetime

class Task:
    """任务/事件类"""
    def __init__(
        self,
        id: int,
        title: str,
        description: str = "",
        completed_at: str = "",      # 截止时间 "YYYY-MM-DD HH:MM"
        mode: int = 0,               # 0-番茄钟，1-倒计时
        created_at: str = "",        # 创建时间
        tags: List[str] = None,
        motto: str = ""
    ):
        self.id = id
        self.title = title
        self.description = description
        self.completed_at = completed_at
        self.mode = mode
        self.created_at = created_at if created_at else datetime.now().strftime("%Y-%m-%d %H:%M")
        self.tags = tags if tags is not None else []
        self.motto = motto

    def to_dict(self) -> dict:
        """转换为字典，方便存为JSON"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed_at": self.completed_at,
            "mode": self.mode,
            "created_at": self.created_at,
            "tags": self.tags,
            "motto": self.motto
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """从字典创建Task对象"""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            completed_at=data.get("completed_at", ""),
            mode=data.get("mode", 0),
            created_at=data.get("created_at", ""),
            tags=data.get("tags", []),
            motto=data.get("motto", "")
        )


class PomodoroRecord:
    """番茄钟记录类"""
    def __init__(
        self,
        id: int,
        task_id: Optional[int],
        start_time: str,
        end_time: str,
        type: str,      # "work" 或 "break"
        completed: bool = True
    ):
        self.id = id
        self.task_id = task_id
        self.start_time = start_time
        self.end_time = end_time
        self.type = type
        self.completed = completed

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "type": self.type,
            "completed": self.completed
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PomodoroRecord":
        return cls(
            id=data["id"],
            task_id=data.get("task_id"),
            start_time=data["start_time"],
            end_time=data["end_time"],
            type=data["type"],
            completed=data.get("completed", True)
        )


class Calendar:
    """日历类：按日期组织任务"""
    def __init__(self, calendar_id: int, name: str, tasks: List[Task] = None):
        self.calendar_id = calendar_id
        self.name = name
        self.tasks = tasks if tasks is not None else []

    def to_dict(self) -> dict:
        return {
            "calendar_id": self.calendar_id,
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Calendar":
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return cls(
            calendar_id=data["calendar_id"],
            name=data["name"],
            tasks=tasks
        )


class User:
    """用户类（顶层实体）"""
    def __init__(self, user_id: int, username: str, email: str):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.calendar = None   # 后续关联Calendar对象

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "calendar": self.calendar.to_dict() if self.calendar else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        user = cls(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"]
        )
        if data.get("calendar"):
            user.calendar = Calendar.from_dict(data["calendar"])
        return user


class Plan:
    """计划模板类（日计划/周计划）"""
    def __init__(self, id: int, date: str, type: str, items: List[dict] = None):
        self.id = id
        self.date = date          # 计划日期 "YYYY-MM-DD"
        self.type = type          # "daily" 或 "weekly"
        self.items = items if items is not None else []   # [{"task_id": 1, "order": 1}, ...]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "type": self.type,
            "items": self.items
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        return cls(
            id=data["id"],
            date=data["date"],
            type=data["type"],
            items=data.get("items", [])
        )
