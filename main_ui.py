import customtkinter as ctk
import pygame
from tkinter import messagebox, filedialog
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import calendar
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

# ==========================================
# 后端核心逻辑补全 (将你提供的代码片段完整化)
# ==========================================
class TimerMode(Enum):
    POMODORO = "番茄钟"
    COUNTDOWN = "倒计时"
    STOPWATCH = "正向计时"

@dataclass
class SessionRecord:
    record_id: int
    task_id: int
    user_id: int
    mode: TimerMode
    started_at: datetime
    ended_at: datetime
    focused_seconds: float
    is_completed: bool = True
    note: Optional[str] = None

class DailyStats:
    def __init__(self, d: date):
        self.date = d
        self.records: List[SessionRecord] = []
        self.total_focused_seconds: float = 0.0

    def add_record(self, record: SessionRecord):
        self.records.append(record)
        self.total_focused_seconds += record.focused_seconds

    @property
    def total_focused_minutes(self) -> float:
        return round(self.total_focused_seconds / 60, 2)

class Statistics:
    def __init__(self, user_id: int):
        self.user_id: int = user_id
        self._daily_map: Dict[date, DailyStats] = {}
        self._next_record_id: int = 1
        
        # 启动时注入一些模拟的历史数据，方便演示日历和统计效果
        self._inject_mock_data()

    def create_and_save_record(self, task_id: int, mode: TimerMode, started_at: datetime, 
                               ended_at: datetime, focused_seconds: float, 
                               is_completed: bool = True, note: Optional[str] = None) -> SessionRecord:
        record = SessionRecord(
            record_id=self._next_record_id, task_id=task_id, user_id=self.user_id,
            mode=mode, started_at=started_at, ended_at=ended_at,
            focused_seconds=focused_seconds, is_completed=is_completed, note=note,
        )
        self._next_record_id += 1
        self._archive(record)
        return record
    
    def _archive(self, record: SessionRecord) -> None:
        d = record.started_at.date()
        if d not in self._daily_map:
            self._daily_map[d] = DailyStats(d)
        self._daily_map[d].add_record(record)        

    def get_daily(self, query_date: date) -> Optional[DailyStats]:
        return self._daily_map.get(query_date)

    def get_weekly(self, any_day_in_week: date) -> List[float]:
        """修改版：获取一周七天每天的专注分钟数，方便画图"""
        monday = any_day_in_week - timedelta(days=any_day_in_week.weekday())
        weekly_minutes = []
        for i in range(7):
            current_day = monday + timedelta(days=i)
            stats = self._daily_map.get(current_day)
            weekly_minutes.append(stats.total_focused_minutes if stats else 0.0)
        return weekly_minutes

    def _inject_mock_data(self):
        """注入历史测试数据"""
        today = datetime.now()
        import random
        # 往前推7天，随机生成专注数据
        for i in range(7):
            mock_date = today - timedelta(days=i)
            # 随机专注 30 到 150 分钟
            seconds = random.randint(30, 150) * 60 
            self.create_and_save_record(
                task_id=1, mode=TimerMode.POMODORO,
                started_at=mock_date - timedelta(seconds=seconds),
                ended_at=mock_date, focused_seconds=seconds
            )


# ==========================================
# 前端应用
# ==========================================
pygame.mixer.init()
try:
    SUCCESS_SOUND = pygame.mixer.Sound("ding.mp3") 
except:
    SUCCESS_SOUND = None

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")

class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("时间专注助手 - FocusApp")
        self.geometry("950x650")
        self.minsize(850, 550)
        self.protocol("WM_DELETE_WINDOW", self.on_closing) 

        # ✅ 【前后端联调核心点 1】: 实例化全局后端统计类
        self.stats_manager = Statistics(user_id=1001)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.bg_label = ctk.CTkLabel(self, text="")
        self.bg_label.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")
        self.bg_label.lower() 

        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0, fg_color=("gray90", "gray12"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) 

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Focus App", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_timer = ctk.CTkButton(self.sidebar_frame, text="⏲️ 专注计时", command=lambda: self.select_frame("timer"))
        self.btn_timer.grid(row=1, column=0, padx=20, pady=10)

        self.btn_tasks = ctk.CTkButton(self.sidebar_frame, text="📝 待办事项", command=lambda: self.select_frame("tasks"))
        self.btn_tasks.grid(row=2, column=0, padx=20, pady=10)

        self.btn_calendar = ctk.CTkButton(self.sidebar_frame, text="📅 日历计划", command=lambda: self.select_frame("calendar"))
        self.btn_calendar.grid(row=3, column=0, padx=20, pady=10)

        self.btn_stats = ctk.CTkButton(self.sidebar_frame, text="📊 统计数据", command=lambda: self.select_frame("stats"))
        self.btn_stats.grid(row=4, column=0, padx=20, pady=10)

        self.btn_bg = ctk.CTkButton(self.sidebar_frame, text="🖼️ 更换背景", fg_color="transparent", border_width=1, command=self.change_background)
        self.btn_bg.grid(row=6, column=0, padx=20, pady=20)

        self.timer_frame = TimerFrame(self)
        self.tasks_frame = TasksFrame(self)
        self.calendar_frame = CalendarFrame(self)
        self.stats_frame = StatsFrame(self) 

        self.select_frame("calendar") # 为了测试，默认打开日历页看看效果

    def on_closing(self):
        import matplotlib.pyplot as plt
        plt.close('all')
        self.quit()
        self.destroy()

    def select_frame(self, frame_name):
        self.btn_timer.configure(fg_color=("gray75", "gray25") if frame_name == "timer" else "transparent")
        self.btn_tasks.configure(fg_color=("gray75", "gray25") if frame_name == "tasks" else "transparent")
        self.btn_calendar.configure(fg_color=("gray75", "gray25") if frame_name == "calendar" else "transparent")
        self.btn_stats.configure(fg_color=("gray75", "gray25") if frame_name == "stats" else "transparent")

        self.timer_frame.grid_forget()
        self.tasks_frame.grid_forget()
        self.calendar_frame.grid_forget()
        self.stats_frame.grid_forget()

        if frame_name == "timer":
            self.timer_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        elif frame_name == "tasks":
            self.tasks_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        elif frame_name == "calendar":
            self.calendar_frame.refresh_calendar() # 每次点开刷新日历
            self.calendar_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        elif frame_name == "stats":
            self.stats_frame.refresh_chart()       # 每次点开刷新图表
            self.stats_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def change_background(self):
        file_path = filedialog.askopenfilename(title="选择背景图片", filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            try:
                img = Image.open(file_path)
                bg_image = ctk.CTkImage(light_image=img, dark_image=img, size=(1920, 1080))
                self.bg_label.configure(image=bg_image)
            except Exception as e:
                messagebox.showerror("错误", f"图片加载失败: {e}")

class TimerFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.mode_var = ctk.StringVar(value="番茄钟 (Pomodoro)")
        ctk.CTkOptionMenu(self, values=["番茄钟 (Pomodoro)", "倒计时 (Countdown)", "正向计时 (Stopwatch)"],
                          variable=self.mode_var).grid(row=0, column=0, pady=(0, 10))
        ctk.CTkLabel(self, text='"专注当下，不负韶华"', font=ctk.CTkFont(size=16, slant="italic")).grid(row=2, column=0, pady=(0, 20))
        self.time_display = ctk.CTkLabel(self, text="25:00", font=ctk.CTkFont(family="Helvetica", size=110, weight="bold"))
        self.time_display.grid(row=3, column=0, pady=20)
        
        # 按钮区
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=4, column=0, pady=20)
        self.btn_start = ctk.CTkButton(self.control_frame, text="▶ 模拟完成一次专注", font=("Arial", 18), width=200, height=45, command=self.fake_finish_timer)
        self.btn_start.grid(row=0, column=0, padx=10)

    def fake_finish_timer(self):
        """模拟计时器跑完，向后端写入数据"""
        started = datetime.now() - timedelta(minutes=25)
        # ✅ 【前后端联调核心点 2】: 计时结束调用后端保存方法
        self.master.stats_manager.create_and_save_record(
            task_id=1, mode=TimerMode.POMODORO, started_at=started,
            ended_at=datetime.now(), focused_seconds=25 * 60
        )
        if SUCCESS_SOUND: SUCCESS_SOUND.play()
        messagebox.showinfo("专注完成", "已成功专注 25 分钟，数据已写入日历与统计后台！\n请前往日历或统计页面查看。")


class TasksFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="页面施工中...", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=20)

# ==========================================
# 页面 3：真实的动态日历视图 (已联调后端)
# ==========================================
class CalendarFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=(0, 20))

        self.grid_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray15"))
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        for i in range(7):
            self.grid_frame.grid_columnconfigure(i, weight=1)

    def refresh_calendar(self):
        """根据当前时间和后端数据生成日历"""
        # 清空旧控件
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        today = date.today()
        self.title_label.configure(text=f"{today.year}年 {today.month}月 专注日历")

        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, day_name in enumerate(weekdays):
            ctk.CTkLabel(self.grid_frame, text=day_name, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, pady=10)

        # 获取本月第一天是周几，以及本月有多少天
        first_weekday, num_days = calendar.monthrange(today.year, today.month)
        
        row, col = 1, first_weekday
        for day in range(1, num_days + 1):
            current_date = date(today.year, today.month, day)
            
            # ✅ 【前后端联调核心点 3】: 从后端查询这天是否有记录
            daily_stat = self.master.stats_manager.get_daily(current_date)
            
            # 如果有专注数据，显示绿色高亮；如果没有，显示灰色；如果是今天，稍微区分一下
            if daily_stat and daily_stat.total_focused_minutes > 0:
                btn_color = "#2ECC71"  # 绿色
            elif current_date == today:
                btn_color = "#3498DB"  # 蓝色 (今天)
            else:
                btn_color = ("gray80", "gray30")

            btn = ctk.CTkButton(
                self.grid_frame, text=str(day), fg_color=btn_color,
                corner_radius=4, command=lambda d=current_date, stat=daily_stat: self.show_day_detail(d, stat)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            col += 1
            if col > 6:
                col = 0
                row += 1

    def show_day_detail(self, d: date, stat: DailyStats):
        # ✅ 【前后端联调核心点 4】: 点击日历读取对象属性并展示
        if stat:
            msg = f"日期: {d.strftime('%Y-%m-%d')}\n\n当日总专注时长: {stat.total_focused_minutes} 分钟\n完成专注次数: {len(stat.records)} 次"
        else:
            msg = f"日期: {d.strftime('%Y-%m-%d')}\n\n这天没有专注记录哦，继续加油！"
        messagebox.showinfo("日历详情", msg)

# ==========================================
# 页面 4：真实的统计数据视图 (已联调后端)
# ==========================================
class StatsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="📊 本周个人专注力统计", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(0, 10))

        self.chart_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray15"))
        self.chart_frame.grid(row=1, column=0, sticky="nsew")

    def refresh_chart(self):
        """读取后端数据重新画图"""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        # ✅ 【前后端联调核心点 5】: 读取后端真实的一周数据进行绘图
        today = date.today()
        focus_minutes = self.master.stats_manager.get_weekly(today)

        plt.rcParams['font.sans-serif'] = ['SimHei'] 
        plt.rcParams['axes.unicode_minus'] = False 

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('#2b2b2b') 
        ax.set_facecolor('#2b2b2b')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')

        ax.bar(days, focus_minutes, color="#3498DB", width=0.5)
        ax.set_title('本周每日专注时长 (分钟)', color='white', pad=20)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()