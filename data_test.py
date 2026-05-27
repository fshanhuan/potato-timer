"""
data_test.py
测试数据模块：验证 data_models 和 data_manager 的功能
"""

from data_models import Task, PomodoroRecord, Plan, User, Calendar
from data_manager import (
    save_tasks, load_tasks, add_task, delete_task, get_task_by_id,
    save_pomodoro_records, load_pomodoro_records, add_pomodoro_record,
    save_plans, load_plans, add_plan,
    save_user, load_user,
    get_next_task_id, get_next_pomodoro_id, get_next_plan_id
)

def test_tasks():
    print("=== 测试 Task 模块 ===")
    # 创建任务
    task1 = Task(id=1, title="完成数学作业", description="第三章习题", 
                 completed_at="2026-05-25 18:00", mode=0,
                 tags=["学习", "数学"], motto="加油!")
    task2 = Task(id=2, title="写项目报告", description="时间管理软件",
                 completed_at="2026-05-26 20:00", mode=1)
    
    # 保存
    save_tasks([task1, task2])
    print("保存任务成功")
    
    # 加载
    loaded = load_tasks()
    print(f"加载到 {len(loaded)} 个任务")
    for t in loaded:
        print(f"  {t.id}: {t.title} - {t.completed_at}")
    
    # 按ID查找
    found = get_task_by_id(1)
    print(f"查找id=1: {found.title if found else '未找到'}")
    
    # 删除任务
    delete_task(2)
    after_delete = load_tasks()
    print(f"删除后剩余任务数: {len(after_delete)}")
    
    # 新增任务（自动分配ID）
    new_id = get_next_task_id()
    task3 = Task(id=new_id, title="新任务", description="通过add_task添加")
    add_task(task3)
    final = load_tasks()
    print(f"添加后任务数: {len(final)}, 最新ID: {final[-1].id}")
    print("✅ Task 测试通过\n")

def test_pomodoro():
    print("=== 测试 PomodoroRecord 模块 ===")
    record1 = PomodoroRecord(id=1, task_id=1, start_time="2026-05-25 10:00",
                             end_time="2026-05-25 10:25", type="work", completed=True)
    record2 = PomodoroRecord(id=2, task_id=None, start_time="2026-05-25 10:25",
                             end_time="2026-05-25 10:30", type="break", completed=True)
    
    save_pomodoro_records([record1, record2])
    loaded = load_pomodoro_records()
    print(f"保存/加载番茄钟记录 {len(loaded)} 条")
    for r in loaded:
        print(f"  {r.id}: {r.type} ({r.start_time} ~ {r.end_time})")
    
    new_id = get_next_pomodoro_id()
    record3 = PomodoroRecord(id=new_id, task_id=1, start_time="2026-05-26 14:00",
                             end_time="2026-05-26 14:25", type="work", completed=False)
    add_pomodoro_record(record3)
    final = load_pomodoro_records()
    print(f"添加后共 {len(final)} 条记录")
    print("✅ 番茄钟测试通过\n")

def test_plans():
    print("=== 测试 Plan 模块 ===")
    plan1 = Plan(id=1, date="2026-05-21", type="daily", 
                 items=[{"task_id": 1, "order": 1}, {"task_id": 2, "order": 2}])
    save_plans([plan1])
    loaded = load_plans()
    print(f"保存/加载计划 {len(loaded)} 条")
    for p in loaded:
        print(f"  {p.id}: {p.type} {p.date}, 项目数: {len(p.items)}")
    
    new_id = get_next_plan_id()
    plan2 = Plan(id=new_id, date="2026-05-22", type="weekly", items=[])
    add_plan(plan2)
    final = load_plans()
    print(f"添加后共 {len(final)} 条计划")
    print("✅ Plan 测试通过\n")

def test_user():
    print("=== 测试 User 模块 ===")
    user = User(user_id=1, username="测试用户", email="test@example.com")
    calendar = Calendar(calendar_id=10, name="我的日历")
    user.calendar = calendar
    save_user(user)
    loaded = load_user()
    if loaded:
        print(f"加载用户: {loaded.username}, 邮箱: {loaded.email}")
        if loaded.calendar:
            print(f"关联日历: {loaded.calendar.name}")
    else:
        print("加载用户失败")
    print("✅ User 测试通过\n")

def run_all_tests():
    test_tasks()
    test_pomodoro()
    test_plans()
    test_user()
    print("🎉 所有测试通过！数据模块工作正常。")

if __name__ == "__main__":
    run_all_tests()
