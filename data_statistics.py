"""
data_statistics.py
统计时间使用情况：任务完成率、番茄钟效率、计划对比、生成饼图和报告
"""

import matplotlib.pyplot as plt
from datetime import datetime
from typing import List, Dict, Tuple
from data_models import Task, PomodoroRecord, Plan
from data_manager import load_tasks, load_pomodoro_records, load_plans

class TimeStatistics:
    """时间统计与分析类"""
    
    def __init__(self):
        self.tasks: List[Task] = load_tasks()
        self.records: List[PomodoroRecord] = load_pomodoro_records()
        self.plans: List[Plan] = load_plans()
    
    # ---------- 1. 任务统计 ----------
    def task_completion_rate(self) -> Dict:
        """统计任务完成情况"""
        total = len(self.tasks)
        if total == 0:
            return {"total": 0, "completed": 0, "completion_rate": 0}
        
        # 判断任务是否完成：有 completed_at 截止时间且已过？简化：按任务属性，这里假设任务只要有 completed_at 且不为空就算完成
        # 更合理：增加一个 completed 字段，但数据合同没有。这里简单演示：检查 completed_at 是否为空字符串
        completed = sum(1 for t in self.tasks if t.completed_at and t.completed_at.strip())
        rate = (completed / total) * 100
        return {"total": total, "completed": completed, "completion_rate": rate}
    
    # ---------- 2. 番茄钟统计 ----------
    def pomodoro_summary(self) -> Dict:
        """统计番茄钟总时长和工作/休息次数"""
        work_sessions = [r for r in self.records if r.type == "work" and r.completed]
        break_sessions = [r for r in self.records if r.type == "break" and r.completed]
        
        # 计算总工作时间（分钟）
        def minutes_between(start: str, end: str) -> float:
            fmt = "%Y-%m-%d %H:%M"
            start_dt = datetime.strptime(start, fmt)
            end_dt = datetime.strptime(end, fmt)
            return (end_dt - start_dt).total_seconds() / 60.0
        
        work_minutes = sum(minutes_between(r.start_time, r.end_time) for r in work_sessions)
        break_minutes = sum(minutes_between(r.start_time, r.end_time) for r in break_sessions)
        
        return {
            "work_sessions": len(work_sessions),
            "break_sessions": len(break_sessions),
            "work_minutes": round(work_minutes, 1),
            "break_minutes": round(break_minutes, 1),
            "total_minutes": round(work_minutes + break_minutes, 1)
        }
    
    # ---------- 3. 计划对比 ----------
    def compare_with_plans(self) -> List[str]:
        """比较计划与实际任务执行的差异，生成文字差异报告"""
        report = []
        if not self.plans:
            report.append("暂无计划数据，无法对比。")
            return report
        
        # 获取所有任务标题
        task_titles = {t.id: t.title for t in self.tasks}
        
        for plan in self.plans:
            planned_ids = [item["task_id"] for item in plan.items]
            planned_titles = [task_titles.get(pid, f"未命名任务{pid}") for pid in planned_ids]
            # 实际任务（所有任务）
            actual_titles = [t.title for t in self.tasks]
            
            # 找出计划中未完成的任务（简化：计划中的任务如果没有出现在实际任务列表中，视为未完成）
            missing = [title for title in planned_titles if title not in actual_titles]
            extra = [title for title in actual_titles if title not in planned_titles]
            
            report.append(f"\n【{plan.type}计划】日期: {plan.date}")
            if missing:
                report.append(f"  未按计划完成的任务: {', '.join(missing)}")
            else:
                report.append("  计划任务全部完成！")
            if extra:
                report.append(f"  额外完成的任务: {', '.join(extra)}")
        return report
    
    # ---------- 4. 生成文本报告 ----------
    def generate_text_report(self) -> str:
        """生成完整的时间使用分析报告（文本）"""
        completion = self.task_completion_rate()
        pomo = self.pomodoro_summary()
        plan_diff = self.compare_with_plans()
        
        report_lines = [
            "=" * 50,
            "           时间使用分析报告",
            "=" * 50,
            f"\n📌 任务统计:",
            f"  总任务数: {completion['total']}",
            f"  已完成: {completion['completed']}",
            f"  完成率: {completion['completion_rate']:.1f}%",
            f"\n🍅 番茄钟统计:",
            f"  工作番茄钟: {pomo['work_sessions']} 次",
            f"  休息时段: {pomo['break_sessions']} 次",
            f"  总工作时长: {pomo['work_minutes']} 分钟 ({pomo['work_minutes']/60:.1f} 小时)",
            f"  总休息时长: {pomo['break_minutes']} 分钟",
            f"\n📅 计划对比:",
        ]
        if plan_diff:
            report_lines.extend(plan_diff)
        else:
            report_lines.append("  无计划数据")
        
        # 估算浪费时间（简单：未完成任务的数量 x 预估25分钟）
        wasted_tasks = completion['total'] - completion['completed']
        wasted_time = wasted_tasks * 25  # 假设每个未完成任务至少浪费25分钟
        report_lines.extend([
            f"\n⏰ 时间浪费评估:",
            f"  未完成任务数: {wasted_tasks}",
            f"  估算浪费时间: {wasted_time} 分钟 ({wasted_time/60:.1f} 小时)",
            f"  建议: {'设置更合理的截止时间' if wasted_tasks > 0 else '继续保持！'}"
        ])
        report_lines.append("\n" + "=" * 50)
        return "\n".join(report_lines)
    
    # ---------- 5. 饼图可视化 ----------
    def plot_time_distribution(self):
        """绘制时间分配饼图（工作/休息/浪费）"""
        pomo = self.pomodoro_summary()
        completion = self.task_completion_rate()
        wasted_tasks = completion['total'] - completion['completed']
        # 假设每个未完成任务代表浪费25分钟
        wasted_minutes = wasted_tasks * 25
        work_minutes = pomo['work_minutes']
        break_minutes = pomo['break_minutes']
        
        labels = []
        sizes = []
        if work_minutes > 0:
            labels.append("工作时间")
            sizes.append(work_minutes)
        if break_minutes > 0:
            labels.append("休息时间")
            sizes.append(break_minutes)
        if wasted_minutes > 0:
            labels.append("浪费时间")
            sizes.append(wasted_minutes)
        
        if not sizes:
            print("没有足够的数据绘制饼图。")
            return
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#66b3ff', '#99ff99', '#ff9999'])
        plt.title("时间分配饼图")
        plt.axis('equal')
        plt.show()

def main():
    """运行统计并输出报告、显示饼图"""
    stats = TimeStatistics()
    # 输出文本报告
    print(stats.generate_text_report())
    # 绘制饼图
    stats.plot_time_distribution()

if __name__ == "__main__":
    main()
