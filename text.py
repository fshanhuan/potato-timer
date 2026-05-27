import tkinter as tk
from PIL import Image, ImageTk
import math

class CatPomodoro:
    def __init__(self, root):
        self.root = root
        self.root.title("猫咪番茄钟")
        self.root.geometry("400x600")
        self.root.configure(bg="white")

        # 计时核心变量
        self.total_seconds = 45 * 60
        self.remaining = self.total_seconds
        self.running = False
        self.is_shaking = False  # 标记是否正在晃动

        # 1. 环形进度条画布
        self.canvas = tk.Canvas(root, width=300, height=300, bg="white", highlightthickness=0)
        self.canvas.place(x=50, y=20)  # 固定画布位置
        self.center_x, self.center_y = 150, 150  # 圆环中心点
        self.radius = 120

        # 底层背景环
        self.canvas.create_oval(
            self.center_x - self.radius, self.center_y - self.radius,
            self.center_x + self.radius, self.center_y + self.radius,
            outline="#FFF5E6", width=15
        )
        # 动态进度环
        self.progress_arc = self.canvas.create_arc(
            self.center_x - self.radius, self.center_y - self.radius,
            self.center_x + self.radius, self.center_y + self.radius,
            start=90, extent=0, outline="#FF7A2F", width=15, style=tk.ARC
        )

        # 2. 加载图片 + 放置在圆环正中心
        self.cat_img = None
        self.cat_label = None
        self.load_center_image()

        # 3. 倒计时文字
        self.time_label = tk.Label(root, text="45:00", font=("Arial", 48, "bold"), bg="white")
        self.time_label.place(x=100, y=330)

        # 4. 提示文案
        self.tip_label = tk.Label(
            root, text="完成专注挑战，即可获得14条小鱼干奖励猫咪哦~",
            font=("Arial", 10), bg="white", fg="#666666"
        )
        self.tip_label.place(x=40, y=390)

        # 5. 控制按钮
        self.start_btn = tk.Button(
            root, text="开始", font=("Arial", 14), bg="black", fg="white",
            width=15, height=2, command=self.toggle_timer
        )
        self.start_btn.place(x=110, y=440)

    def load_center_image(self):
        """加载图片，固定在圆环正中心"""
        img_path = r"D:\数据结构\python\8DE7CDA8AC27266BA2DC396F07D6729E.jpg"
        try:
            # 打开图片并缩放（尺寸根据圆环调整）
            pil_img = Image.open(img_path)
            pil_img = pil_img.resize((100, 100))  # 图片大小，可自行修改
            self.cat_img = ImageTk.PhotoImage(pil_img)

            # 基于圆环中心点，居中放置图片
            img_w, img_h = 100, 100
            x = self.center_x - img_w // 2
            y = self.center_y - img_h // 2
            self.cat_label = tk.Label(self.canvas, image=self.cat_img, bg="white")
            self.cat_label.place(x=x, y=y)

        except Exception as e:
            print("图片加载失败，使用emoji替代：", e)
            # 兜底文字，同样居中
            self.cat_label = tk.Label(
                self.canvas, text="🐱", font=("Arial", 60), bg="white"
            )
            self.cat_label.place(x=self.center_x - 30, y=self.center_y - 30)

    def toggle_timer(self):
        """开始/暂停 计时"""
        if not self.running:
            self.running = True
            self.start_btn.config(text="暂停")
            self.update_timer()
        else:
            self.running = False
            self.start_btn.config(text="继续")

    def update_timer(self):
        """每秒更新时间与环形进度"""
        if self.running and self.remaining > 0:
            self.remaining -= 1
            # 更新倒计时文本
            mins, secs = divmod(self.remaining, 60)
            self.time_label.config(text=f"{mins:02d}:{secs:02d}")
            # 更新环形进度
            progress = (self.total_seconds - self.remaining) / self.total_seconds
            extent = -progress * 360
            self.canvas.itemconfig(self.progress_arc, extent=extent)
            self.root.after(1000, self.update_timer)
        elif self.remaining == 0:
            # 计时结束
            self.running = False
            self.start_btn.config(text="时间到！")
            self.shake_image()  # 启动晃动动画

    def shake_image(self, count=0):
        """图片左右晃动动画（圆环中心位置晃动）"""
        max_shake = 12  # 晃动次数
        offset = 8      # 晃动偏移像素，越大晃得越厉害

        if count >= max_shake:
            # 晃动结束，回归正中心
            img_w, img_h = 100, 100
            x = self.center_x - img_w // 2
            y = self.center_y - img_h // 2
            self.cat_label.place(x=x, y=y)
            return

        # 左右交替偏移
        if count % 2 == 0:
            new_x = self.center_x - 50 + offset
        else:
            new_x = self.center_x - 50 - offset
        self.cat_label.place(x=new_x, y=self.center_y - 50)

        # 递归执行动画
        self.root.after(80, self.shake_image, count + 1)

if __name__ == "__main__":
    root = tk.Tk()
    app = CatPomodoro(root)
    root.mainloop()