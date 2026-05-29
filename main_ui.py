import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PomodoroTimer import (
    UserManager, User, TimerController, TimerMode, TimerState, PomodoroPhase
)

# ==========================================
# 初始化音频模块（pygame 可选）
# ==========================================
try:
    import pygame
    pygame.mixer.init()
    SUCCESS_SOUND = pygame.mixer.Sound("ding.mp3")
except Exception:
    SUCCESS_SOUND = None

# ==========================================
# 颜色与主题配置
# ==========================================
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

PHASE_LABELS = {
    "work":        "🍅 工作中",
    "short_break": "☕ 短休息",
    "long_break":  "🛋️ 长休息",
}


class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("时间专注助手 - FocusApp")
        self.geometry("950x650")
        self.minsize(850, 550)

        # 绑定关闭窗口事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ----------------------------------------
        # 初始化后端用户
        # ----------------------------------------
        self.user_manager = UserManager()
        self.user = self.user_manager.create_user("默认用户")

        # ==========================================
        # 全局底层背景图载体 (放在最底层)
        # ==========================================
        self.bg_label = ctk.CTkLabel(self, text="")
        self.bg_label.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")
        self.bg_label.lower()

        # ----------------------------------------
        # 1. 侧边栏 (Sidebar) 导航区
        # ----------------------------------------
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

        # ----------------------------------------
        # 2. 主内容区 (Main Frame)
        # ----------------------------------------
        self.timer_frame = TimerFrame(self, user=self.user)
        self.tasks_frame = TasksFrame(self)
        self.calendar_frame = CalendarFrame(self)
        self.stats_frame = StatsFrame(self)

        self.select_frame("timer")  # 默认打开计时页

    def on_closing(self):
        """处理窗口关闭事件"""
        self.timer_frame.on_destroy()
        plt.close('all')
        self.quit()
        self.destroy()

    def select_frame(self, frame_name):
        """控制页面切换"""
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
            self.calendar_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        elif frame_name == "stats":
            self.stats_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def change_background(self):
        """自定义背景图逻辑"""
        file_path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            try:
                img = Image.open(file_path)
                bg_image = ctk.CTkImage(light_image=img, dark_image=img, size=(1920, 1080))
                self.bg_label.configure(image=bg_image)
            except Exception as e:
                messagebox.showerror("错误", f"图片加载失败: {e}")


# ==========================================
# 页面 1：计时器视图 (已对接后端)
# ==========================================
class TimerFrame(ctk.CTkFrame):
    def __init__(self, master, user=None):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        self.user = user
        self.controller: TimerController | None = None
        self.task = None
        self._tick_after_id = None
        self._custom_minutes = 25

        # 初始化后端控制器
        if self.user:
            self._init_backend()

        # ---- UI 组件 ----
        self.mode_var = ctk.StringVar(value="番茄钟 (Pomodoro)")
        self.mode_menu = ctk.CTkOptionMenu(
            self, values=["番茄钟 (Pomodoro)", "倒计时 (Countdown)", "正向计时 (Stopwatch)"],
            variable=self.mode_var, command=self.change_mode
        )
        self.mode_menu.grid(row=0, column=0, pady=(0, 10))

        self.btn_custom_time = ctk.CTkButton(
            self, text="⚙️ 自定义时长", width=100, fg_color="transparent",
            border_width=1, command=self.set_custom_time
        )
        self.btn_custom_time.grid(row=1, column=0, pady=(0, 10))

        # 阶段指示标签（仅番茄钟模式显示）
        self.phase_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3498DB"
        )
        self.phase_label.grid(row=2, column=0, pady=(0, 5))

        self.motto_label = ctk.CTkLabel(
            self, text='"专注当下，不负韶华"', font=ctk.CTkFont(size=16, slant="italic")
        )
        self.motto_label.grid(row=3, column=0, pady=(0, 20))

        self.time_display = ctk.CTkLabel(
            self, text="25:00", font=ctk.CTkFont(family="Helvetica", size=110, weight="bold")
        )
        self.time_display.grid(row=4, column=0, pady=20)

        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=5, column=0, pady=10)

        self.btn_start = ctk.CTkButton(
            self.control_frame, text="▶ 开始", font=("Arial", 18),
            width=120, height=45, command=self.start_timer
        )
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_stop = ctk.CTkButton(
            self.control_frame, text="⏹ 停止", font=("Arial", 18),
            width=120, height=45, fg_color="#E74C3C", hover_color="#C0392B",
            command=self.stop_timer
        )
        self.btn_stop.grid(row=0, column=1, padx=10)

        # 下一阶段按钮（仅番茄钟模式显示）
        self.btn_next_phase = ctk.CTkButton(
            self.control_frame, text="⏭ 下一阶段", font=("Arial", 14),
            width=120, height=45, fg_color="#2ECC71", hover_color="#27AE60",
            command=self.next_phase
        )
        self.btn_next_phase.grid(row=0, column=2, padx=10)

        self._update_phase_ui()

    # =========================================================
    # 后端初始化
    # =========================================================
    def _init_backend(self):
        """创建默认任务与计时器控制器"""
        self.task = self.user.create_task(
            title="快速专注",
            description="",
            mode=TimerMode.POMODORO,
            planned_minutes=float(self._custom_minutes),
        )
        self.controller = TimerController(user=self.user, task=self.task)
        self._update_from_controller()

    def _recreate_controller(self, mode: TimerMode):
        """切换模式时重建 task 和 controller"""
        self._stop_tick()
        self.task = self.user.create_task(
            title="快速专注",
            description="",
            mode=mode,
            planned_minutes=float(self._custom_minutes),
        )
        self.controller = TimerController(user=self.user, task=self.task)
        self._update_from_controller()

    # =========================================================
    # UI 更新
    # =========================================================
    def _update_from_controller(self, result: dict | None = None):
        """从控制器当前状态刷新所有 UI"""
        if not self.controller:
            return
        if result is None:
            result = self.controller._build_response("", "idle")

        # 时间
        self.time_display.configure(text=result.get("display_time", "25:00"))

        # 阶段 + motto
        pomo = result.get("pomodoro_info")
        if pomo:
            phase = pomo["current_phase"]
            self.phase_label.configure(text=PHASE_LABELS.get(phase, phase))
            self.btn_next_phase.grid()
        else:
            self.phase_label.configure(text="")
            self.btn_next_phase.grid_remove()

        motto = result.get("current_motto", "")
        if motto:
            self.motto_label.configure(text=f'"{motto}"')

        # 按钮状态
        state = result.get("state", "idle")
        if state == "running":
            self.btn_start.configure(text="⏸ 暂停")
        elif state == "paused":
            self.btn_start.configure(text="▶ 继续")
        else:
            self.btn_start.configure(text="▶ 开始")

    def _update_phase_ui(self):
        """根据当前模式显示/隐藏阶段相关组件"""
        mode_text = self.mode_var.get()
        if "番茄钟" in mode_text:
            self.btn_next_phase.grid()
        else:
            self.btn_next_phase.grid_remove()
            self.phase_label.configure(text="")

    # =========================================================
    # 计时器生命周期
    # =========================================================
    def start_timer(self):
        if not self.controller:
            return
        state = self.controller.state

        if state == TimerState.RUNNING:
            result = self.controller.pause()
            self._stop_tick()
        elif state == TimerState.PAUSED:
            result = self.controller.start()
            self._start_tick()
        elif state == TimerState.FINISHED:
            # 番茄钟：提示用户点击"下一阶段"
            result = self.controller._build_response(
                "⏰ 当前阶段已结束，请点击下一阶段", "blocked"
            )
        else:
            result = self.controller.start()
            if result.get("action") not in ("blocked", "none"):
                self._start_tick()

        self._update_from_controller(result)
        if SUCCESS_SOUND:
            SUCCESS_SOUND.play()

    def stop_timer(self):
        if not self.controller:
            return
        self._stop_tick()
        result = self.controller.stop()
        self._update_from_controller(result)

    def next_phase(self):
        """手动推进到番茄钟下一阶段"""
        if not self.controller or not self.controller.is_pomodoro:
            return
        self._stop_tick()
        result = self.controller.next_pomodoro_phase()
        self._update_from_controller(result)
        # 自动开始新阶段
        self._start_tick()

    # =========================================================
    # 每秒 tick 循环
    # =========================================================
    def _start_tick(self):
        self._stop_tick()
        self._schedule_tick()

    def _stop_tick(self):
        if self._tick_after_id is not None:
            try:
                self.after_cancel(self._tick_after_id)
            except Exception:
                pass
            self._tick_after_id = None

    def _schedule_tick(self):
        self._tick_after_id = self.after(1000, self._tick)

    def _tick(self):
        if not self.controller:
            return
        result = self.controller.tick()
        self._update_from_controller(result)

        if result.get("action") == "finished":
            # 番茄钟自然结束，提示下一阶段
            self._update_phase_ui()
            return

        if self.controller.state == TimerState.RUNNING:
            self._schedule_tick()

    # =========================================================
    # 模式 / 自定义时长
    # =========================================================
    def change_mode(self, choice):
        self._stop_tick()
        if "番茄钟" in choice:
            self.time_display.configure(text="25:00")
            self._custom_minutes = 25
            if self.user:
                self._recreate_controller(TimerMode.POMODORO)
        elif "倒计时" in choice:
            self.time_display.configure(text="10:00")
            self._custom_minutes = 10
            if self.user:
                self._recreate_controller(TimerMode.COUNTDOWN)
        else:
            self.time_display.configure(text="00:00")
            self._custom_minutes = 0
            if self.user:
                self._recreate_controller(TimerMode.COUNTUP)
        self._update_phase_ui()

    def set_custom_time(self):
        dialog = ctk.CTkInputDialog(text="请输入需要的专注时长 (分钟):", title="自定义时间")
        user_input = dialog.get_input()
        if user_input and user_input.isdigit() and int(user_input) > 0:
            minutes = int(user_input)
            self._custom_minutes = minutes
            self.time_display.configure(text=f"{minutes:02d}:00")
            self.mode_var.set("倒计时 (Countdown)")
            if self.user:
                self._recreate_controller(TimerMode.COUNTDOWN)
            self._update_phase_ui()
        elif user_input:
            messagebox.showwarning("无效输入", "请输入大于 0 的纯数字！")

    def on_destroy(self):
        """窗口关闭前清理 tick 定时器"""
        self._stop_tick()


# ==========================================
# 页面 2：待办事项视图
# ==========================================
class TasksFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.top_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.top_bar, text="今日待办", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(self.top_bar, text="+ 新建任务", width=100).grid(row=0, column=1, sticky="e")

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=("gray90", "gray15"))
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")

        mock_tasks = [
            {"title": "完成数学作业", "tags": ["学习", "数学"], "desc": "第三章习题", "motto": "拿下这道题，清华等着你"},
            {"title": "英语六级背单词", "tags": ["英语", "倒计时"], "desc": "List 15", "motto": "No pain, no gain"},
        ]

        for i, t in enumerate(mock_tasks):
            self.create_task_card(i, t)

    def create_task_card(self, row_idx, task_data):
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=8, fg_color=("white", "gray20"))
        card.grid(row=row_idx, column=0, sticky="ew", pady=5, padx=5)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkCheckBox(card, text="", width=20).grid(row=0, column=0, padx=10, pady=10, rowspan=2)

        title_box = ctk.CTkFrame(card, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w", pady=(10, 0))
        ctk.CTkLabel(title_box, text=task_data["title"], font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=(0, 10))
        for tag in task_data["tags"]:
            ctk.CTkLabel(title_box, text=f" #{tag} ", fg_color="#3498DB", text_color="white", corner_radius=4).pack(side="left", padx=2)

        ctk.CTkLabel(card, text=f"{task_data['desc']} | 🌟 {task_data['motto']}", text_color="gray").grid(row=1, column=1, sticky="w", pady=(0, 10))
        ctk.CTkButton(card, text="去专注", width=60, fg_color="#2ECC71", hover_color="#27AE60").grid(row=0, column=2, rowspan=2, padx=15)


# ==========================================
# 页面 3：日历视图
# ==========================================
class CalendarFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="2026年 5月 计划表", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(0, 20))

        self.grid_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray15"))
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        for i in range(7):
            self.grid_frame.grid_columnconfigure(i, weight=1)

        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, day in enumerate(weekdays):
            ctk.CTkLabel(self.grid_frame, text=day, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, pady=10)

        day_counter = 1
        for row in range(1, 6):
            for col in range(7):
                if day_counter <= 31:
                    has_task = (day_counter in [20, 21, 25])
                    btn_color = "#3498DB" if has_task else ("gray80", "gray30")

                    btn = ctk.CTkButton(
                        self.grid_frame, text=str(day_counter), fg_color=btn_color,
                        corner_radius=4, command=lambda d=day_counter: self.show_day_detail(d)
                    )
                    btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    day_counter += 1

    def show_day_detail(self, day):
        messagebox.showinfo("日期详情", f"您点击了 2026年5月{day}日\n此处将展示后端的 Plan 列表。")


# ==========================================
# 页面 4：统计数据视图
# ==========================================
class StatsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="📊 个人专注力统计分析", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(0, 10))

        self.chart_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray15"))
        self.chart_frame.grid(row=1, column=0, sticky="nsew")

        self.draw_mock_chart()

    def draw_mock_chart(self):
        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        focus_minutes = [45, 120, 90, 150, 60, 200, 180]

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
