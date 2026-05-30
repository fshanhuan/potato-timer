import tkinter as tk
from tkinter import ttk
from data_manager import load_tasks, load_pomodoro_records
from data_statistics import TimeStatistics

class StatsWindow:
    def __init__(self, root):
        self.win = tk.Toplevel(root)
        self.win.title("统计数据")
        self.win.geometry("600x500")

        # 创建统计对象
        self.stats = TimeStatistics()

        # 获取数据
        self.completion = self.stats.task_completion_rate()
        self.pomo = self.stats.pomodoro_summary()

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        # 任务统计
        frame1 = ttk.LabelFrame(self.win, text="任务统计", padding=10)
        frame1.pack(fill="x", padx=10, pady=5)
        ttk.Label(frame1, text=f"总任务数: {self.completion['total']}").pack(anchor="w")
        ttk.Label(frame1, text=f"已完成: {self.completion['completed']}").pack(anchor="w")
        ttk.Label(frame1, text=f"完成率: {self.completion['completion_rate']:.1f}%").pack(anchor="w")

        # 专注统计
        frame2 = ttk.LabelFrame(self.win, text="专注统计", padding=10)
        frame2.pack(fill="x", padx=10, pady=5)
        ttk.Label(frame2, text=f"工作番茄钟: {self.pomo['work_sessions']} 次").pack(anchor="w")
        ttk.Label(frame2, text=f"总专注时长: {self.pomo['work_minutes']} 分钟").pack(anchor="w")
        ttk.Label(frame2, text=f"总休息时长: {self.pomo['break_minutes']} 分钟").pack(anchor="w")

        # 饼图按钮
        ttk.Button(self.win, text="查看时间分配饼图", command=self.show_pie).pack(pady=10)

        # 关闭按钮
        ttk.Button(self.win, text="关闭", command=self.win.destroy).pack(pady=5)

    def show_pie(self):
        self.stats.plot_time_distribution()

def show_stats_window(parent_root=None):
    """供外部调用的入口，parent_root 是主窗口的根"""
    if parent_root is None:
        # 测试时自己创建根窗口
        root = tk.Tk()
        root.withdraw()
        StatsWindow(root)
        root.mainloop()
    else:
        StatsWindow(parent_root)

if __name__ == "__main__":
    # 单独测试
    show_stats_window()