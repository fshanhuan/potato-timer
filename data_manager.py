"""
data_manager.py
数据管理模块：提供 JSON 文件的读写、任务/记录的增删改查
符合小组数据合同（2026-05-27）
"""

import json
import os
from typing import List, Optional
from datetime import datetime
from data_models import Task, PomodoroRecord, User, Calendar, Plan

# ---------- 文件路径配置 ----------
DATA_DIR = "data"  # 数据文件夹
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
POMODORO_FILE = os.path.join(DATA_DIR, "pomodoro.json")
PLANS_FILE = os.path.join(DATA_DIR, "plans.json")
USER_FILE = os.path.join(DATA_DIR, "user.json")

# ---------- 辅助函数：确保文件夹存在 ----------
def ensure_data_dir():
    """确保 data 文件夹存在，如果不存在则创建"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

# ---------- 任务（Task）相关 ----------
def save_tasks(tasks: List[Task]):
    """保存任务列表到 tasks.json"""
    ensure_data_dir()
    data = [task.to_dict() for task in tasks]
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_tasks() -> List[Task]:
    """从 tasks.json 加载任务列表"""
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Task.from_dict(item) for item in data]

def add_task(task: Task):
    """添加单个任务（自动保存）"""
    tasks = load_tasks()
    # 简单去重：如果 id 已存在，则覆盖
    tasks = [t for t in tasks if t.id != task.id]
    tasks.append(task)
    save_tasks(tasks)

def delete_task(task_id: int):
    """删除指定 id 的任务"""
    tasks = load_tasks()
    tasks = [t for t in tasks if t.id != task_id]
    save_tasks(tasks)

def get_task_by_id(task_id: int) -> Optional[Task]:
    """根据 id 查找任务"""
    tasks = load_tasks()
    for t in tasks:
        if t.id == task_id:
            return t
    return None

# ---------- 番茄钟记录（PomodoroRecord）相关 ----------
def save_pomodoro_records(records: List[PomodoroRecord]):
    """保存番茄钟记录"""
    ensure_data_dir()
    data = [r.to_dict() for r in records]
    with open(POMODORO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_pomodoro_records() -> List[PomodoroRecord]:
    """加载番茄钟记录"""
    if not os.path.exists(POMODORO_FILE):
        return []
    with open(POMODORO_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PomodoroRecord.from_dict(item) for item in data]

def add_pomodoro_record(record: PomodoroRecord):
    """添加一条番茄钟记录"""
    records = load_pomodoro_records()
    records = [r for r in records if r.id != record.id]
    records.append(record)
    save_pomodoro_records(records)

# ---------- 计划（Plan）相关 ----------
def save_plans(plans: List[Plan]):
    """保存计划列表"""
    ensure_data_dir()
    data = [p.to_dict() for p in plans]
    with open(PLANS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_plans() -> List[Plan]:
    """加载计划列表"""
    if not os.path.exists(PLANS_FILE):
        return []
    with open(PLANS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Plan.from_dict(item) for item in data]

def add_plan(plan: Plan):
    """添加计划"""
    plans = load_plans()
    plans = [p for p in plans if p.id != plan.id]
    plans.append(plan)
    save_plans(plans)

# ---------- 用户数据 ----------
def save_user(user: User):
    """保存用户信息"""
    ensure_data_dir()
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(user.to_dict(), f, ensure_ascii=False, indent=2)

def load_user() -> Optional[User]:
    """加载用户信息"""
    if not os.path.exists(USER_FILE):
        return None
    with open(USER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return User.from_dict(data)

# ---------- 便捷函数：获取下一个可用 ID ----------
def get_next_task_id() -> int:
    """返回下一个可用的任务ID（现有最大id+1，如果没有任务则返回1）"""
    tasks = load_tasks()
    if not tasks:
        return 1
    return max(t.id for t in tasks) + 1

def get_next_pomodoro_id() -> int:
    """返回下一个可用的番茄钟记录ID"""
    records = load_pomodoro_records()
    if not records:
        return 1
    return max(r.id for r in records) + 1

def get_next_plan_id() -> int:
    """返回下一个可用的计划ID"""
    plans = load_plans()
    if not plans:
        return 1
    return max(p.id for p in plans) + 1
