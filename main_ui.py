import customtkinter as ctk
import pygame
from tkinter import messagebox, filedialog
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==========================================
# 初始化音频模块
# ==========================================
pygame.mixer.init()
try:
    SUCCESS_SOUND = pygame.mixer.Sound("ding.mp3") 
except:
    SUCCESS_SOUND = None

# ==========================================
# 颜色与主题配置
# ==========================================
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")

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
        self.timer_frame = TimerFrame(self)
        self.tasks_frame = TasksFrame(self)
        self.calendar_frame = CalendarFrame(self)
        self.stats_frame = StatsFrame(self) 

        self.select_frame("timer") # 默认打开计时页

    # ==========================================
    # ✅ 修复：将 on_closing 移到了这里，与 __init__ 平级
    # ==========================================
    def on_closing(self):
        """处理窗口关闭事件，清理 Matplotlib 后台任务防止报错"""
        import matplotlib.pyplot as plt
        plt.close('all')  # 提前强杀所有 Matplotlib 的图表和后台检测任务
        self.quit()       # 停止主循环
        self.destroy()    # 安全销毁窗口

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
                # 👉 【后端联调点】: 保存 file_path 到用户配置
            except Exception as e:
                messagebox.showerror("错误", f"图片加载失败: {e}")


# ==========================================
# 页面 1：计时器视图 (包含自定义时间)
# ==========================================
class TimerFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent") # 透明背景，露出底层壁纸
        self.grid_columnconfigure(0, weight=1)

        self.mode_var = ctk.StringVar(value="番茄钟 (Pomodoro)")
        self.mode_menu = ctk.CTkOptionMenu(
            self, values=["番茄钟 (Pomodoro)", "倒计时 (Countdown)", "正向计时 (Stopwatch)"],
            variable=self.mode_var, command=self.change_mode
        )
        self.mode_menu.grid(row=0, column=0, pady=(0, 10))

        self.btn_custom_time = ctk.CTkButton(self, text="⚙️ 自定义时长", width=100, fg_color="transparent", border_width=1, command=self.set_custom_time)
        self.btn_custom_time.grid(row=1, column=0, pady=(0, 20))

        self.motto_label = ctk.CTkLabel(self, text='"专注当下，不负韶华"', font=ctk.CTkFont(size=16, slant="italic"))
        self.motto_label.grid(row=2, column=0, pady=(0, 20))

        self.time_display = ctk.CTkLabel(self, text="25:00", font=ctk.CTkFont(family="Helvetica", size=110, weight="bold"))
        self.time_display.grid(row=3, column=0, pady=20)

        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=4, column=0, pady=20)

        self.btn_start = ctk.CTkButton(self.control_frame, text="▶ 开始", font=("Arial", 18), width=120, height=45, command=self.start_timer)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_stop = ctk.CTkButton(self.control_frame, text="⏹ 停止", font=("Arial", 18), width=120, height=45, fg_color="#E74C3C", hover_color="#C0392B")
        self.btn_stop.grid(row=0, column=1, padx=10)

    def change_mode(self, choice):
        if "番茄钟" in choice:
            self.time_display.configure(text="25:00")
        elif "倒计时" in choice:
            self.time_display.configure(text="10:00")
        else:
            self.time_display.configure(text="00:00")

    def set_custom_time(self):
        dialog = ctk.CTkInputDialog(text="请输入需要的专注时长 (分钟):", title="自定义时间")
        user_input = dialog.get_input()
        if user_input and user_input.isdigit() and int(user_input) > 0:
            minutes = int(user_input)
            self.time_display.configure(text=f"{minutes:02d}:00")
            self.mode_var.set("倒计时 (Countdown)")
            # 👉 【后端联调点】: 更新后端 task.mode 和目标时间
        elif user_input:
            messagebox.showwarning("无效输入", "请输入大于 0 的纯数字！")

    def start_timer(self):
        self.btn_start.configure(text="⏸ 暂停")
        if SUCCESS_SOUND: SUCCESS_SOUND.play()

# ==========================================
# 页面 2：待办事项视图 
# ==========================================
class TasksFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 顶栏
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.top_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.top_bar, text="今日待办", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(self.top_bar, text="+ 新建任务", width=100).grid(row=0, column=1, sticky="e")

        # 任务列表容器 (可滚动)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=("gray90", "gray15"))
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")

        # 模拟数据
        mock_tasks = [
            {"title": "完成数学作业", "tags": ["学习", "数学"], "desc": "第三章习题", "motto": "拿下这道题，清华等着你"},
            {"title": "英语六级背单词", "tags": ["英语", "倒计时"], "desc": "List 15", "motto": "No pain, no gain"},
        ]

        for i, t in enumerate(mock_tasks):
            self.create_task_card(i, t)

    def create_task_card(self, row_idx, task_data):
        """生成单张任务卡片"""
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

        # 日历网格容器
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
                    has_task = (day_counter in [20, 21, 25]) # 模拟包含任务的日子
                    btn_color = "#3498DB" if has_task else ("gray80", "gray30")
                    
                    btn = ctk.CTkButton(
                        self.grid_frame, text=str(day_counter), fg_color=btn_color,
                        corner_radius=4, command=lambda d=day_counter: self.show_day_detail(d)
                    )
                    btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    day_counter += 1

    def show_day_detail(self, day):
        # 👉 【后端联调点】: 获取并展示当天的真实计划列表
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

        # 承载图表的背景框
        self.chart_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray15"))
        self.chart_frame.grid(row=1, column=0, sticky="nsew")

        # 画图
        self.draw_mock_chart()

    def draw_mock_chart(self):
        """画一个柱状图嵌入界面"""
        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        focus_minutes = [45, 120, 90, 150, 60, 200, 180]

        plt.rcParams['font.sans-serif'] = ['SimHei'] # 防止中文乱码
        plt.rcParams['axes.unicode_minus'] = False 

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        
        # 匹配深色主题
        fig.patch.set_facecolor('#2b2b2b') 
        ax.set_facecolor('#2b2b2b')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')

        ax.bar(days, focus_minutes, color="#3498DB", width=0.5)
        ax.set_title('本周每日专注时长 (分钟)', color='white', pad=20)

        # 嵌入 CustomTkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()