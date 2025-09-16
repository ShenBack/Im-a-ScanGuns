import tkinter as tk
from tkinter import ttk
import keyboard
import time
import threading
import json
import os

class KeyboardSimulatorApp:
    def __init__(self, root):
        # 设置中文字体支持
        self.font_config = ('Microsoft YaHei UI', 9)

        self.root = root
        self.root.title("我是扫码枪")
        self.root.geometry("420x150")  # 更紧凑的窗口尺寸

        # 设置窗口置顶
        self.root.attributes('-topmost', True)

        # 设置窗口样式 - Notion风格
        self.root.configure(bg='#ffffff')  # 白色背景
        self.root.resizable(False, False)  # 禁止调整窗口大小

        # 创建自定义ttk样式，实现Notion风格
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 使用现代风格

        # 配置Notion风格的颜色和字体
        self.configure_notion_style()

        # 设置变量
        self.with_enter = tk.BooleanVar(value=True)  # 默认勾选以回车键结束
        self.window_alpha = tk.IntVar(value=100)  # 窗口透明度 0-100
        self.history = []  # 用于存储历史记录的列表，保持插入顺序
        self.history_visible = False  # 历史记录区域的显示状态
        self.max_history_items = 50  # 最大历史记录条数
        # 将历史记录保存在系统临时目录，避免在exe目录生成多余文件
        # import tempfile
        # import os
        # self.history_file = os.path.join(tempfile.gettempdir(), 'keyboard_history.json')
        self.history_file = 'keyboard_history.json'  # 历史记录保存文件
        self.settings_file = 'keyboard_settings.json'  # 设置保存文件

        # 输入间隔时间（毫秒）
        self.typing_delay = tk.IntVar(value=20)  # 默认20ms

        # 加载历史记录和设置
        self.load_history()
        self.load_settings()
        # 应用透明度
        try:
            alpha = max(10, min(100, int(self.window_alpha.get()))) / 100.0
            self.root.attributes('-alpha', alpha)
        except Exception:
            pass

        # 创建菜单栏
        self.create_menu()

        # 创建主框架 - 使用自定义圆角框架
        self.main_frame = self.create_rounded_frame(root, padding=8, bg_color='#ffffff')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 创建说明标签
        self.label = ttk.Label(self.main_frame, text="请输入想要模拟的文本:", style='Notion.TLabel')
        self.label.pack(anchor='w', pady=(0, 4))

        # 创建输入框和状态文本组合容器
        input_container = ttk.Frame(self.main_frame, style='Notion.TFrame')
        input_container.pack(fill=tk.X, pady=(0, 4))

        # 创建文本输入框 - Notion风格（圆角、柔和边框）
        self.text_input = ttk.Entry(input_container, width=40, style='Notion.TEntry')
        self.text_input.pack(fill=tk.X, pady=(0, 1))
        self.text_input.focus()

        # 创建状态标签 - 放置在输入框同一容器内
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_label = ttk.Label(input_container, textvariable=self.status_var, style='Notion.Status.TLabel')
        self.status_label.pack(anchor='w')

        # 创建按钮框架
        self.button_frame = ttk.Frame(self.main_frame, style='Notion.TFrame')
        self.button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # 创建开始按钮 - Notion风格
        self.start_button = ttk.Button(self.button_frame, text="开始", command=self.start_simulation, style='Notion.Primary.TButton')
        self.start_button.pack(side=tk.RIGHT, padx=(0, 2))

        # 创建历史记录按钮 - Notion风格
        self.history_button = ttk.Button(self.button_frame, text="显示历史", command=self.toggle_history, style='Notion.TButton')
        self.history_button.pack(side=tk.LEFT, padx=(0, 2))

        # 创建清空按钮 - Notion风格
        self.clear_button = ttk.Button(self.button_frame, text="清空", command=self.clear_input, style='Notion.TButton')
        self.clear_button.pack(side=tk.RIGHT, padx=(0, 2))

        # 创建历史记录区域框架
        self.history_frame = ttk.Frame(self.root, style='Notion.TFrame')
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.history_frame.pack_forget()  # 初始隐藏历史记录区域

        # 绑定Enter键触发开始模拟
        self.root.bind('<Return>', lambda event: self.start_simulation())

    def configure_notion_style(self):
        """配置Notion风格的UI样式"""
        # 主色调设置 - Notion风格的中性色调
        bg_color = '#ffffff'       # 白色背景
        text_color = '#37352f'     # 深灰色文字
        light_text_color = '#6b7280' # 浅灰色文字
        border_color = '#e5e7eb'   # 边框颜色
        hover_color = '#f7f7f7'    # 悬停颜色
        active_color = '#f0f0f0'   # 激活颜色

        # 配置框架样式
        self.style.configure('Notion.TFrame', background=bg_color)

        # 配置标签样式
        self.style.configure('Notion.TLabel',
                            font=self.font_config,
                            foreground=text_color,
                            background=bg_color)

        # 配置状态标签样式
        self.style.configure('Notion.Status.TLabel',
                            font=self.font_config,
                            foreground=light_text_color,
                            background=bg_color)

        # 配置输入框样式 - 圆角效果通过borderwidth和relief实现
        self.style.configure('Notion.TEntry',
                            font=self.font_config,
                            padding=6,  # 更紧凑的内边距
                            fieldbackground=bg_color,
                            foreground=text_color,
                            bordercolor=border_color,
                            lightcolor=border_color,
                            darkcolor=border_color)
        self.style.map('Notion.TEntry',
                      bordercolor=[('focus', '#2563eb')],  # 聚焦时边框颜色变化
                      lightcolor=[('focus', '#2563eb')],
                      darkcolor=[('focus', '#2563eb')])

        # 配置按钮样式 - Notion风格的圆角按钮（基础）
        self.style.configure('Notion.TButton',
                            font=self.font_config,
                            padding=5,  # 更紧凑的内边距
                            background=hover_color,
                            foreground=text_color,
                            bordercolor=border_color,
                            relief=tk.FLAT)
        self.style.map('Notion.TButton',
                      background=[('active', active_color), ('hover', hover_color)],
                      relief=[('pressed', tk.SUNKEN), ('!pressed', tk.FLAT)])

        # 主按钮（开始）- 蓝色
        primary_bg = '#2563eb'
        primary_bg_hover = '#1d4ed8'
        self.style.configure('Notion.Primary.TButton',
                             font=self.font_config,
                             padding=5,
                             background=primary_bg,
                             foreground='#ffffff',
                             bordercolor=primary_bg,
                             relief=tk.FLAT)
        self.style.map('Notion.Primary.TButton',
                       background=[('active', primary_bg_hover), ('hover', primary_bg_hover)],
                       relief=[('pressed', tk.SUNKEN), ('!pressed', tk.FLAT)])

        # 配置复选框样式 - Notion风格
        self.style.configure('Notion.TCheckbutton',
                            font=self.font_config,
                            foreground=text_color,
                            background=bg_color)
        self.style.map('Notion.TCheckbutton',
                      background=[('active', active_color)])

    def create_rounded_frame(self, parent, padding=10, bg_color='#ffffff'):
        """创建圆角框架（模拟实现）"""
        # 创建一个普通框架
        frame = ttk.Frame(parent, style='Notion.TFrame', padding=padding)

        # 为了更好的圆角效果，我们可以在需要时使用Canvas来实现
        # 但由于ttk的限制，这里主要通过样式配置来模拟圆角效果

        return frame

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)

        # 创建设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="设置", command=self.open_settings)

        # 添加到菜单栏
        menubar.add_cascade(label="选项", menu=settings_menu)

        # 设置菜单栏
        self.root.config(menu=menubar)

    def toggle_history(self):
        """切换历史记录区域的显示/隐藏"""
        if self.history_visible:
            self.hide_history()
        else:
            self.show_history()

    def show_history(self):
        """在主界面下方显示历史记录"""
        # 显示历史记录区域
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.history_visible = True
        self.history_button.config(text="隐藏历史")

        # 更新窗口高度以适应历史记录显示
        self.root.geometry("420x260")

        # 刷新历史记录显示内容
        self.refresh_history_display()

    def refresh_history_display(self):
        """刷新历史记录显示内容"""
        # 清空历史记录区域
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        # 创建滚动区域
        canvas = tk.Canvas(self.history_frame, highlightthickness=0, bg='#ffffff')
        scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas, style='Notion.TFrame')

        # 配置滚动
        content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 布局滚动区域
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 设置Canvas可以响应鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # 确保在窗口大小变化时正确更新滚动区域
        self.history_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # 显示历史记录
        if not self.history:
            empty_label = ttk.Label(content_frame, text="暂无历史记录", style='Notion.Status.TLabel')
            empty_label.pack(pady=12)
        else:
            # 显示所有历史记录，让用户可以通过滚动查看全部
            display_history = self.history

            # 创建3列的网格布局来显示小卡片
            for i, text in enumerate(display_history):
                # 计算行列位置
                row = i // 3
                col = i % 3

                # 创建小卡片框架
                card_frame = ttk.Frame(content_frame, style='Notion.TFrame', padding=4)
                card_frame.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

                # 设置固定大小，增加宽度以容纳更长的文本
                card_frame.configure(width=110, height=64)

                # 添加阴影和圆角效果
                card_frame.config(relief="solid", borderwidth=1)

                # 文本标签（小卡片样式）
                # 截取部分文本显示在卡片上
                display_text = text[:20] + '...' if len(text) > 20 else text
                text_label = ttk.Label(card_frame, text=display_text, style='Notion.TLabel', wraplength=100, justify="left")
                text_label.pack(fill=tk.BOTH, expand=True, pady=4)

                # 为卡片添加点击事件，点击后复制内容
                def copy_on_click(event, text_to_copy=text):
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text_to_copy)
                    self.root.update()  # 保持剪贴板内容

                    # 显示复制成功提示（完整显示内容）
                    self.status_var.set(f"已复制: {text_to_copy}")
                    self.root.after(2000, lambda: self.status_var.set("就绪"))

                card_frame.bind("<Button-1>", copy_on_click)
                text_label.bind("<Button-1>", copy_on_click)

                # 设置鼠标悬停效果（使用ttk样式来改变背景颜色为绿色，不改变边框）
                # 创建悬停样式（如果不存在）
                if not hasattr(self, 'hover_style_created'):
                    self.hover_style_created = True
                    # 设置框架悬停样式
                    self.style.configure('Hover.TFrame', background='#d4edda')
                    # 设置标签悬停样式
                    self.style.configure('Hover.TLabel', background='#d4edda')

                # 保存原始样式

                # 为卡片添加双击事件，双击后将内容覆盖到输入框并执行开始操作
                def double_click_to_input(event, text_to_input=text):
                    # 检查是否正在输出字符串，如果正在输出则不触发双击事件
                    # 使用更可靠的方式检测按钮是否被禁用
                    # 在Tkinter中，tk.DISABLED常量实际上等同于字符串'disabled'
                    # 同时检查两种形式是为了增强代码的健壮性，确保在不同平台或Tkinter版本下都能正常工作
                    if self.start_button['state'] in (tk.DISABLED, 'disabled'):
                        return

                    # 将内容设置到输入框
                    self.text_input.delete(0, tk.END)
                    self.text_input.insert(0, text_to_input)
                    # 执行开始按钮操作
                    self.start_simulation()

                card_frame.bind("<Double-1>", double_click_to_input)
                text_label.bind("<Double-1>", double_click_to_input)
                original_frame_style = card_frame['style']
                original_label_style = text_label['style']

                # 绑定鼠标进入和离开事件来切换样式
                card_frame.bind("<Enter>", lambda e, frame=card_frame, label=text_label: (
                    frame.config(style='Hover.TFrame'),
                    label.config(style='Hover.TLabel')
                ))
                card_frame.bind("<Leave>", lambda e, frame=card_frame, label=text_label, f_style=original_frame_style, l_style=original_label_style: (
                    frame.config(style=f_style),
                    label.config(style=l_style)
                ))
                text_label.bind("<Enter>", lambda e, frame=card_frame, label=text_label: (
                    frame.config(style='Hover.TFrame'),
                    label.config(style='Hover.TLabel')
                ))
                text_label.bind("<Leave>", lambda e, frame=card_frame, label=text_label, f_style=original_frame_style, l_style=original_label_style: (
                    frame.config(style=f_style),
                    label.config(style=l_style)
                ))

            # 确保网格列可以扩展
            content_frame.columnconfigure(0, weight=1)
            content_frame.columnconfigure(1, weight=1)
            content_frame.columnconfigure(2, weight=1)

    def hide_history(self):
        """隐藏历史记录区域"""
        self.history_frame.pack_forget()
        self.history_visible = False
        self.history_button.config(text="显示历史")

        # 恢复窗口原始高度
        self.root.geometry("420x150")

    def open_settings(self):
        """打开设置对话框"""
        # 创建对话框 - Notion风格
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.resizable(False, False)
        settings_window.configure(bg='#ffffff')
        settings_window.transient(self.root)  # 设置为主窗口的子窗口
        settings_window.grab_set()  # 模态对话框

        # 获取主窗口的位置和大小
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        # 计算设置对话框的大小（增大比例，确保所有设置项可见）
        settings_width = int(root_width * 0.85)  # 增加宽度比例
        settings_height = int(root_height * 0.85)  # 增加高度比例
        # 设置最小高度，确保有足够空间显示所有设置项
        min_height = 200
        if settings_height < min_height:
            settings_height = min_height
        settings_window.geometry(f"{settings_width}x{settings_height}")

        # 计算设置对话框的位置，使其位于主窗口中心
        settings_x = root_x + (root_width - settings_width) // 2
        settings_y = root_y + (root_height - settings_height) // 2
        settings_window.geometry(f"+{settings_x}+{settings_y}")

        # 创建圆角主框架
        main_frame = self.create_rounded_frame(settings_window, padding=12, bg_color='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 添加复选框 - Notion风格
        enter_checkbox = ttk.Checkbutton(
            main_frame,
            text="以回车键结束",
            variable=self.with_enter,
            onvalue=True,
            offvalue=False,
            style='Notion.TCheckbutton'
        )
        enter_checkbox.pack(anchor='w', pady=(6, 12))

        # 添加输入间隔设置
        delay_frame = ttk.Frame(main_frame, style='Notion.TFrame')
        delay_frame.pack(anchor='w', fill=tk.X, pady=(6, 12))

        delay_label = ttk.Label(delay_frame, text="输入间隔(毫秒):", style='Notion.TLabel')
        delay_label.pack(side=tk.LEFT, padx=(0, 6))

        delay_entry = ttk.Entry(delay_frame, width=10, textvariable=self.typing_delay, style='Notion.TEntry')
        delay_entry.pack(side=tk.LEFT)

        # 添加透明度设置（0-100）
        alpha_frame = ttk.Frame(main_frame, style='Notion.TFrame')
        alpha_frame.pack(anchor='w', fill=tk.X, pady=(6, 12))

        alpha_label = ttk.Label(alpha_frame, text="窗口透明度(10-100):", style='Notion.TLabel')
        alpha_label.pack(side=tk.LEFT, padx=(0, 6))

        alpha_entry = ttk.Entry(alpha_frame, width=10, textvariable=self.window_alpha, style='Notion.TEntry')
        alpha_entry.pack(side=tk.LEFT)

        # 删除了确定按钮，用户可以通过点击窗口右上角的关闭按钮来关闭设置对话框
        # 绑定关闭事件，保存设置
        settings_window.protocol("WM_DELETE_WINDOW", lambda: (self.save_settings(), settings_window.destroy()))

    def clear_input(self):
        """清空输入框"""
        self.text_input.delete(0, tk.END)
        self.status_var.set("就绪")
        self.text_input.focus()

    def simulate_typing(self, text):
        """模拟键盘输入"""
        # 等待2秒
        for i in range(2, 0, -1):
            self.status_var.set(f"将在{i}秒后开始输入...")
            time.sleep(1)

        self.status_var.set("正在输入...")

        # 计算延迟时间（只计算一次）
        delay_seconds = self.typing_delay.get() / 1000.0  # 转换为秒

        # 逐字符模拟输入，保留大小写
        for char in text:
            # 直接输入普通字符
            keyboard.write(char)
            # 使用预先计算好的间隔时间
            time.sleep(delay_seconds)

        # 如果勾选了以回车键结束，则按回车键
        if self.with_enter.get():
            keyboard.press_and_release('enter')

        self.status_var.set("输入完成！")
        # 恢复按钮状态和重新绑定Enter键
        self.root.after(0, lambda: (
            self.enable_buttons(),
            self.root.bind('<Return>', lambda event: self.start_simulation())
        ))

    def disable_buttons(self):
        """禁用按钮，防止重复点击"""
        self.start_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        self.history_button.config(state=tk.DISABLED)

    def enable_buttons(self):
        """启用按钮"""
        self.start_button.config(state=tk.NORMAL)
        self.clear_button.config(state=tk.NORMAL)
        self.history_button.config(state=tk.NORMAL)

    def start_simulation(self):
        """开始模拟输入"""
        text = self.text_input.get().strip()
        if not text:
            self.status_var.set("请先输入文本！")
            return

        # 将文本添加到历史记录中（去重并保持顺序）
        if text in self.history:
            # 如果文本已存在，先移除再添加到列表开头
            self.history.remove(text)
        self.history.insert(0, text)  # 添加到列表开头

        # 限制历史记录数量
        if len(self.history) > self.max_history_items:
            self.history = self.history[:self.max_history_items]  # 保留前50条

        # 保存历史记录到文件
        self.save_history()

        # 如果历史记录区域当前可见，则实时更新显示
        if self.history_visible:
            self.refresh_history_display()

        # 禁用按钮
        self.disable_buttons()
        # 临时解绑Enter键事件，防止自动按Enter导致的循环
        self.root.unbind('<Return>')

        # 在新线程中执行模拟输入，避免UI卡顿
        threading.Thread(target=self.simulate_typing, args=(text,), daemon=True).start()

    def load_history(self):
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            self.history = []

    def save_history(self):
        """保存历史记录到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def load_settings(self):
        """从文件加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # 加载设置项
                    if 'with_enter' in settings:
                        self.with_enter.set(settings['with_enter'])
                    if 'typing_delay' in settings:
                        self.typing_delay.set(settings['typing_delay'])
                    if 'window_alpha' in settings:
                        try:
                            self.window_alpha.set(int(settings['window_alpha']))
                        except Exception:
                            pass
            # 加载完成后立即应用透明度
            try:
                alpha = max(10, min(100, int(self.window_alpha.get()))) / 100.0
                self.root.attributes('-alpha', alpha)
            except Exception:
                pass
        except Exception as e:
            print(f"加载设置失败: {e}")

    def save_settings(self):
        """保存设置到文件"""
        try:
            # 保存时进行范围限制并立即应用透明度
            try:
                clamped_alpha = max(10, min(100, int(self.window_alpha.get())))
                self.window_alpha.set(clamped_alpha)
                self.root.attributes('-alpha', clamped_alpha / 100.0)
            except Exception:
                pass

            settings = {
                'with_enter': self.with_enter.get(),
                'typing_delay': self.typing_delay.get(),
                'window_alpha': self.window_alpha.get()
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = KeyboardSimulatorApp(root)
    root.mainloop()