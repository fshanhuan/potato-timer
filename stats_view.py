import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from data_manager import load_tasks, load_pomodoro_records
from data_statistics import TimeStatistics

class StatsWindow:
    def __init__(self, root):
        self.win = tk.Toplevel(root)
        self.win.title("统计数据")
        self.win.geometry("650x600")

        self.stats = TimeStatistics()
        self.completion = self.stats.task_completion_rate()
        self.pomo = self.stats.pomodoro_summary()

        self.create_widgets()
        self.draw_pie_chart()   # 直接显示饼图

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

        # 饼图容器
        self.pie_frame = ttk.LabelFrame(self.win, text="时间分配饼图", padding=10)
        self.pie_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 关闭按钮
        ttk.Button(self.win, text="关闭", command=self.win.destroy).pack(pady=10)

    def draw_pie_chart(self):
        """直接在 tkinter 窗口中绘制饼图"""
        work_min = self.pomo['work_minutes']
        break_min = self.pomo['break_minutes']
        completion = self.completion['completion_rate']
        wasted_min = (100 - completion) / 100 * (work_min + break_min) if (work_min + break_min) > 0 else 0

        labels = []
        sizes = []
        if work_min > 0:
            labels.append("工作时间")
            sizes.append(work_min)
        if break_min > 0:
            labels.append("休息时间")
            sizes.append(break_min)
        if wasted_min > 0:
            labels.append("浪费时间")
            sizes.append(wasted_min)

        if not sizes:
            label = ttk.Label(self.pie_frame, text="暂无数据，请先添加任务和番茄钟记录")
            label.pack()
            return

        fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
               colors=['#66b3ff', '#99ff99', '#ff9999'])
        ax.set_title("时间分配")

        canvas = FigureCanvasTkAgg(fig, master=self.pie_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def show_stats_window(parent_root=None):
    if parent_root is None:
        root = tk.Tk()
        root.withdraw()
        StatsWindow(root)
        root.mainloop()
    else:
        StatsWindow(parent_root)

if __name__ == "__main__":
    show_stats_window()
