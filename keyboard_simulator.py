import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
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
        self.root.geometry("380x132")  # 初始窗口尺寸（可能会被设置覆盖）

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
        self.is_typing = False  # 是否正在输入，防止重复触发
        self.ultra_compact = tk.BooleanVar(value=False)  # 极致紧凑模式（折叠历史时更小）
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
        # 界面构建完成后，先以完整模式渲染一次
        self.root.update_idletasks()
        self.show_full_ui_once()
        # 然后根据设置，若为极致紧凑则延迟切换，避免首屏抖动
        if bool(self.ultra_compact.get()):
            self.root.after(50, self.enter_ultra_compact_mode)

        # 创建菜单栏
        self.create_menu()

        # 创建主框架 - 使用自定义圆角框架
        self.main_frame = self.create_rounded_frame(root, padding=4, bg_color='#ffffff')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 创建说明标签
        self.label = ttk.Label(self.main_frame, text="请输入想要模拟的文本:", style='Notion.TLabel')
        self.label.pack(anchor='w', pady=(0, 2))

        # 创建输入框和状态文本组合容器
        self.input_container = ttk.Frame(self.main_frame, style='Notion.TFrame')
        self.input_container.pack(fill=tk.X, pady=(0, 2))

        # 创建文本输入框 - Notion风格（圆角、柔和边框）
        self.text_input = ttk.Entry(self.input_container, width=32, style='Notion.TEntry')
        self.text_input.pack(fill=tk.X, pady=(0, 1))
        self.text_input.focus()

        # 创建状态标签 - 放置在输入框同一容器内
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_label = ttk.Label(self.input_container, textvariable=self.status_var, style='Notion.Status.TLabel')
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

        # 创建历史记录区域框架（初始化不pack，避免紧凑模式下边缘闪现）
        self.history_frame = ttk.Frame(self.root, style='Notion.TFrame')

        # 绑定Enter键触发开始模拟
        self.root.bind('<Return>', lambda event: self.start_simulation())
        self.root.bind('<Escape>', lambda event: self.clear_input())
        self.root.bind('<Control-u>', lambda event: self.toggle_ultra_compact_mode())
        self.root.bind('<Control-U>', lambda event: self.toggle_ultra_compact_mode())

        # 界面构建完成后再应用紧凑UI与按钮可见性，再设置窗口尺寸，避免初始化阶段布局异常
        self.root.update_idletasks()
        self.update_button_visibility()
        self.update_compact_ui()
        self.apply_window_geometry()

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

    def apply_window_chrome(self):
        """根据极致紧凑模式设置窗口是否无边框（当前需求：即使极致紧凑也保留边框）"""
        try:
            # 始终保留系统边框
            self.root.overrideredirect(False)
        except Exception:
            pass

    def apply_compact_styles(self):
        """根据极致紧凑模式调整字体与控件内边距，并在退出时恢复"""
        try:
            if not hasattr(self, '_regular_entry_padding'):
                self._regular_entry_padding = 6
            compact_font = (self.font_config[0], max(7, self.font_config[1]-1))

            if bool(self.ultra_compact.get()):
                # 缩小主框架内边距与pack外边距
                try:
                    self.main_frame.configure(padding=1)
                except Exception:
                    pass
                try:
                    self.main_frame.pack_configure(padx=2, pady=1)
                except Exception:
                    pass
                try:
                    self.input_container.pack_configure(pady=(0, 0), padx=2)
                except Exception:
                    pass
                try:
                    self.text_input.pack_configure(pady=(0, 0))
                except Exception:
                    pass
                # 极致紧凑：显示状态行（紧凑排布在输入框下方）
                try:
                    if not self.status_label.winfo_ismapped():
                        self.status_label.pack(anchor='w')
                    # 紧凑模式不增加额外垂直间距
                    self.status_label.pack_configure(anchor='w')
                except Exception:
                    pass

                # 字体与样式更紧凑
                self.style.configure('Notion.TEntry', font=compact_font, padding=1)
                self.style.configure('Notion.Status.TLabel', font=compact_font)
                # 输入框字符宽度更小，避免水平溢出
                try:
                    self.text_input.configure(width=18)
                except Exception:
                    pass
            else:
                # 恢复常规边距
                try:
                    self.main_frame.configure(padding=4)
                except Exception:
                    pass
                try:
                    self.main_frame.pack_configure(padx=4, pady=4)
                except Exception:
                    pass
                try:
                    self.input_container.pack_configure(pady=(0, 2), padx=4)
                except Exception:
                    pass
                try:
                    self.text_input.pack_configure(pady=(0, 1))
                except Exception:
                    pass

                # 恢复常规字体与样式
                self.style.configure('Notion.TEntry', font=self.font_config, padding=self._regular_entry_padding)
                self.style.configure('Notion.Status.TLabel', font=self.font_config)
                # 恢复状态行显示
                try:
                    if not self.status_label.winfo_ismapped():
                        self.status_label.pack(anchor='w')
                except Exception:
                    pass
                # 恢复输入框宽度
                try:
                    self.text_input.configure(width=32)
                except Exception:
                    pass
        except Exception:
            pass

    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_move(self, event):
        try:
            x = event.x_root - getattr(self, '_drag_x', 0)
            y = event.y_root - getattr(self, '_drag_y', 0)
            self.root.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def enable_dragging(self):
        if getattr(self, '_drag_bound', False):
            return
        try:
            self.main_frame.bind('<Button-1>', self._start_move)
            self.main_frame.bind('<B1-Motion>', self._do_move)
            self._drag_bound = True
        except Exception:
            pass

    def disable_dragging(self):
        if not getattr(self, '_drag_bound', False):
            return
        try:
            self.main_frame.unbind('<Button-1>')
            self.main_frame.unbind('<B1-Motion>')
            self._drag_bound = False
        except Exception:
            pass

    def update_compact_ui(self):
        """在极致紧凑模式下隐藏提示标签并去除标题栏；恢复时反之"""
        self.apply_window_chrome()
        try:
            if bool(self.ultra_compact.get()):
                # 隐藏提示标签
                if self.label.winfo_ismapped():
                    self.label.pack_forget()
                # 极致紧凑模式下保留边框，不启用自定义拖动
                self.disable_dragging()
                # 应用紧凑样式
                self.apply_compact_styles()
                # 隐藏菜单栏以节省高度
                try:
                    if not hasattr(self, '_menubar_cached'):
                        self._menubar_cached = self.root['menu'] if 'menu' in self.root.keys() else None
                    self.root.config(menu="")
                except Exception:
                    pass
                # 从布局树中临时移除按钮与历史
                self.detach_optional_ui()
            else:
                # 显示提示标签（保持在输入容器之前）
                if not self.label.winfo_ismapped():
                    try:
                        self.label.pack(anchor='w', pady=(0, 2), before=self.input_container)
                    except Exception:
                        self.label.pack(anchor='w', pady=(0, 2))
                # 非极致模式下同样不需要自定义拖动
                self.disable_dragging()
                # 恢复常规样式
                self.apply_compact_styles()
                # 恢复菜单栏
                try:
                    if getattr(self, '_menubar_cached', None) is not None:
                        self.root.config(menu=self._menubar_cached)
                except Exception:
                    pass
                # 恢复按钮与历史容器
                self.attach_optional_ui()
        except Exception:
            pass

    def update_button_visibility(self):
        """根据极致紧凑模式显示/隐藏按钮区域"""
        try:
            if bool(self.ultra_compact.get()):
                # 隐藏按钮栏
                if self.button_frame.winfo_ismapped():
                    self.button_frame.pack_forget()
                # 禁用按钮，防止透过快捷方式以外的误触
                try:
                    self.start_button.config(state=tk.DISABLED)
                    self.clear_button.config(state=tk.DISABLED)
                    self.history_button.config(state=tk.DISABLED)
                except Exception:
                    pass
            else:
                # 显示按钮栏（保持原布局）
                if not self.button_frame.winfo_ismapped():
                    # 若有保存的原pack信息则恢复，否则用默认
                    try:
                        if hasattr(self, '_button_pack_info') and self._button_pack_info:
                            self.button_frame.pack(**self._button_pack_info)
                        else:
                            self.button_frame.pack(fill=tk.X, side=tk.BOTTOM)
                    except Exception:
                        self.button_frame.pack(fill=tk.X, side=tk.BOTTOM)
                # 启用按钮
                try:
                    self.start_button.config(state=tk.NORMAL)
                    self.clear_button.config(state=tk.NORMAL)
                    self.history_button.config(state=tk.NORMAL)
                except Exception:
                    pass
        except Exception:
            pass

    def enforce_history_hidden_if_compact(self):
        """极致紧凑模式下强制隐藏历史区域并标记状态"""
        try:
            if bool(self.ultra_compact.get()):
                self.history_visible = False
                try:
                    if self.history_frame.winfo_ismapped():
                        self.history_frame.pack_forget()
                except Exception:
                    pass
        except Exception:
            pass

    def detach_optional_ui(self):
        """在极致紧凑模式下，将按钮栏和历史区域从布局树中临时移除并记录pack信息"""
        try:
            # 保存并移除按钮栏
            try:
                if self.button_frame.winfo_manager():
                    self._button_pack_info = self.button_frame.pack_info()
                else:
                    self._button_pack_info = None
            except Exception:
                self._button_pack_info = None
            try:
                if self.button_frame.winfo_ismapped():
                    self.button_frame.pack_forget()
            except Exception:
                pass

            # 历史区域不应显示，直接移除
            try:
                if self.history_frame.winfo_ismapped():
                    self.history_frame.pack_forget()
            except Exception:
                pass
        except Exception:
            pass

    def attach_optional_ui(self):
        """退出极致紧凑模式后，按原pack信息恢复按钮栏与历史区域（若需）"""
        try:
            # 恢复按钮栏
            if not self.button_frame.winfo_ismapped():
                try:
                    if hasattr(self, '_button_pack_info') and self._button_pack_info:
                        self.button_frame.pack(**self._button_pack_info)
                    else:
                        self.button_frame.pack(fill=tk.X, side=tk.BOTTOM)
                except Exception:
                    self.button_frame.pack(fill=tk.X, side=tk.BOTTOM)

            # 历史区域仅当标记为可见时恢复
            if self.history_visible and not self.history_frame.winfo_ismapped():
                try:
                    self.history_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
                except Exception:
                    pass
        except Exception:
            pass

    def apply_window_geometry(self):
        """根据是否显示历史和极致紧凑模式应用窗口尺寸"""
        try:
            # 先刷新布局，避免测量异常
            self.root.update_idletasks()
            # 极致紧凑模式强制折叠历史
            self.enforce_history_hidden_if_compact()
            if self.history_visible:
                # 展开历史时保证可读
                self.root.minsize(360, 200)
                self.root.geometry("380x220")
            else:
                # 折叠历史时，若开启极致紧凑模式，进一步缩小
                if bool(self.ultra_compact.get()):
                    self.root.minsize(165, 50)
                    self.root.geometry("165x50")
                else:
                    self.root.minsize(360, 120)
                    self.root.geometry("380x132")
        except Exception:
            pass

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)

        # 创建设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="设置", command=self.open_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="关于", command=self.open_about)

        # 添加到菜单栏
        menubar.add_cascade(label="选项", menu=settings_menu)

        # 设置菜单栏
        self.root.config(menu=menubar)

    def toggle_history(self):
        """切换历史记录区域的显示/隐藏"""
        # 极致紧凑模式下禁止切换历史
        if bool(self.ultra_compact.get()):
            return
        if self.history_visible:
            self.hide_history()
        else:
            self.show_history()

    def show_history(self):
        """在主界面下方显示历史记录"""
        # 显示历史记录区域
        self.history_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.history_visible = True
        self.history_button.config(text="隐藏历史")

        # 更新窗口尺寸与按钮显示，并根据极致紧凑模式更新无边框与提示标签
        self.apply_window_geometry()
        self.update_button_visibility()
        self.update_compact_ui()

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
            empty_label.pack(pady=8)
        else:
            # 显示所有历史记录，让用户可以通过滚动查看全部
            display_history = self.history

            # 创建3列的网格布局来显示小卡片
            for i, text in enumerate(display_history):
                # 计算行列位置
                row = i // 3
                col = i % 3

                # 创建小卡片框架
                card_frame = ttk.Frame(content_frame, style='Notion.TFrame', padding=2)
                card_frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

                # 设置固定大小，增加宽度以容纳更长的文本
                card_frame.configure(width=96, height=56)

                # 添加阴影和圆角效果
                card_frame.config(relief="solid", borderwidth=1)

                # 文本标签（小卡片样式）
                # 截取部分文本显示在卡片上
                display_text = text[:20] + '...' if len(text) > 20 else text
                text_label = ttk.Label(card_frame, text=display_text, style='Notion.TLabel', wraplength=90, justify="left")
                text_label.pack(fill=tk.BOTH, expand=True, pady=2)

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
                    # 正在输入则直接忽略，等待完成
                    if getattr(self, 'is_typing', False):
                        return "break"
                    # 使用更可靠的方式检测按钮是否被禁用
                    if self.start_button['state'] in (tk.DISABLED, 'disabled'):
                        return "break"

                    # 将内容设置到输入框
                    self.text_input.delete(0, tk.END)
                    self.text_input.insert(0, text_to_input)
                    # 执行开始按钮操作
                    self.start_simulation()
                    return "break"

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

        # 恢复窗口尺寸与按钮显示，并根据极致紧凑模式更新无边框与提示标签
        self.apply_window_geometry()
        self.update_button_visibility()
        self.update_compact_ui()

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
        main_frame = self.create_rounded_frame(settings_window, padding=8, bg_color='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 添加复选框 - Notion风格
        enter_checkbox = ttk.Checkbutton(
            main_frame,
            text="以回车键结束",
            variable=self.with_enter,
            onvalue=True,
            offvalue=False,
            style='Notion.TCheckbutton'
        )
        enter_checkbox.pack(anchor='w', pady=(4, 8))

        # 添加输入间隔设置
        delay_frame = ttk.Frame(main_frame, style='Notion.TFrame')
        delay_frame.pack(anchor='w', fill=tk.X, pady=(4, 8))

        delay_label = ttk.Label(delay_frame, text="输入间隔(毫秒):", style='Notion.TLabel')
        delay_label.pack(side=tk.LEFT, padx=(0, 6))

        delay_entry = ttk.Entry(delay_frame, width=10, textvariable=self.typing_delay, style='Notion.TEntry')
        delay_entry.pack(side=tk.LEFT)

        # 添加透明度设置（0-100）
        alpha_frame = ttk.Frame(main_frame, style='Notion.TFrame')
        alpha_frame.pack(anchor='w', fill=tk.X, pady=(4, 8))

        alpha_label = ttk.Label(alpha_frame, text="窗口透明度(10-100):", style='Notion.TLabel')
        alpha_label.pack(side=tk.LEFT, padx=(0, 6))

        alpha_entry = ttk.Entry(alpha_frame, width=10, textvariable=self.window_alpha, style='Notion.TEntry')
        alpha_entry.pack(side=tk.LEFT)

        # 极致紧凑模式开关
        compact_checkbox = ttk.Checkbutton(
            main_frame,
            text="极致紧凑模式",
            variable=self.ultra_compact,
            onvalue=True,
            offvalue=False,
            style='Notion.TCheckbutton'
        )
        compact_checkbox.pack(anchor='w', pady=(4, 8))

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
        # 恢复按钮状态、重置输入标记并重新绑定Enter键
        def _finish_reset():
            self.is_typing = False
            self.enable_buttons()
            self.root.bind('<Return>', lambda event: self.start_simulation())
        self.root.after(0, _finish_reset)

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
        # 防重入：若正在输入，忽略新的触发
        if getattr(self, 'is_typing', False):
            self.status_var.set("正在输入中，请稍候...")
            return
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

        # 标记正在输入并禁用按钮
        self.is_typing = True
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
                    if 'ultra_compact' in settings:
                        try:
                            self.ultra_compact.set(bool(settings['ultra_compact']))
                        except Exception:
                            pass
            # 加载完成后立即应用透明度
            try:
                alpha = max(10, min(100, int(self.window_alpha.get()))) / 100.0
                self.root.attributes('-alpha', alpha)
            except Exception:
                pass
            # 按设置应用窗口尺寸
            self.apply_window_geometry()
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
                'window_alpha': self.window_alpha.get(),
                'ultra_compact': bool(self.ultra_compact.get())
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
        # 保存后根据当前状态应用窗口尺寸、按钮可见性与极致紧凑UI
        self.apply_window_geometry()
        self.update_button_visibility()
        self.update_compact_ui()

    def enter_ultra_compact_mode(self):
        """显式进入极致紧凑模式：执行一轮强制性UI与布局调整"""
        try:
            self.ultra_compact.set(True)
            # 强制隐藏历史与可选UI
            self.enforce_history_hidden_if_compact()
            self.detach_optional_ui()
            # 更新按钮/紧凑UI/几何
            self.update_button_visibility()
            self.update_compact_ui()
            self.apply_window_geometry()
            # 切换时添加淡入动画：先降低到10%，再淡入到目标透明度
            try:
                final_pct = max(10, min(100, int(self.window_alpha.get())))
                self._set_window_alpha_pct(10)
                self._fade_to_alpha_pct(final_pct, total_ms=200, steps=10)
            except Exception:
                pass
            # 持久化设置
            self.save_settings()
        except Exception:
            pass

    def exit_ultra_compact_mode(self):
        """退出极致紧凑模式：恢复完整UI、容器、菜单与几何"""
        try:
            self.ultra_compact.set(False)
            # 恢复按钮与历史容器
            self.attach_optional_ui()
            # 更新按钮/紧凑UI/几何
            self.update_button_visibility()
            self.update_compact_ui()
            self.apply_window_geometry()
            # 淡入到目标透明度（保持当前设置）
            try:
                final_pct = max(10, min(100, int(self.window_alpha.get())))
                self._fade_to_alpha_pct(final_pct, total_ms=150, steps=8)
            except Exception:
                pass
            # 持久化设置
            self.save_settings()
        except Exception:
            pass

    def toggle_ultra_compact_mode(self):
        try:
            if bool(self.ultra_compact.get()):
                self.exit_ultra_compact_mode()
            else:
                self.enter_ultra_compact_mode()
        except Exception:
            pass

    def show_full_ui_once(self):
        """强制以完整模式渲染一次：用于启动初始外观始终为完整模式"""
        try:
            # 恢复菜单栏
            try:
                if getattr(self, '_menubar_cached', None) is not None:
                    self.root.config(menu=self._menubar_cached)
            except Exception:
                pass
            # 恢复提示标签（保持在输入容器之前）
            try:
                if not self.label.winfo_ismapped():
                    self.label.pack(anchor='w', pady=(0, 2), before=self.input_container)
            except Exception:
                try:
                    self.label.pack(anchor='w', pady=(0, 2))
                except Exception:
                    pass
            # 恢复按钮栏
            try:
                if not self.button_frame.winfo_ismapped():
                    if hasattr(self, '_button_pack_info') and self._button_pack_info:
                        self.button_frame.pack(**self._button_pack_info)
                    else:
                        self.button_frame.pack(fill=tk.X, side=tk.BOTTOM)
                self.start_button.config(state=tk.NORMAL)
                self.clear_button.config(state=tk.NORMAL)
                self.history_button.config(state=tk.NORMAL)
            except Exception:
                pass
            # 历史保持折叠（默认）
            try:
                if self.history_frame.winfo_ismapped():
                    self.history_frame.pack_forget()
                self.history_visible = False
                self.history_button.config(text="显示历史")
            except Exception:
                pass
            # 恢复常规样式
            self.apply_compact_styles()
            # 应用完整模式的窗口几何（忽略极致紧凑标记）
            try:
                self.root.update_idletasks()
                self.root.minsize(360, 120)
                self.root.geometry("380x132")
            except Exception:
                pass
        except Exception:
            pass

    def _set_window_alpha_pct(self, pct):
        try:
            clamped = max(10, min(100, int(pct)))
            self.root.attributes('-alpha', clamped / 100.0)
        except Exception:
            pass

    def _fade_to_alpha_pct(self, target_pct, total_ms=200, steps=10):
        """以动画方式将窗口透明度淡入到目标百分比（非阻塞）。"""
        try:
            target = max(10, min(100, int(target_pct)))
            # 读取当前alpha
            try:
                current_alpha = float(self.root.attributes('-alpha'))
            except Exception:
                current_alpha = max(0.10, min(1.0, (self.window_alpha.get() or 100) / 100.0))
            current = int(round(current_alpha * 100))
            if steps <= 0:
                self._set_window_alpha_pct(target)
                return
            step_count = steps
            delta = (target - current) / float(step_count)
            interval = max(10, int(total_ms / step_count))

            def _step(i=1, val=current):
                try:
                    next_val = int(round(val + delta))
                    self._set_window_alpha_pct(next_val)
                    if i < step_count:
                        self.root.after(interval, _step, i + 1, next_val)
                except Exception:
                    pass

            _step()
        except Exception:
            pass

    def open_about(self):
        """显示关于/用户须知对话框"""
        try:
            info = (
                "用户须知\n\n"
                "快捷键：\n"
                "- Enter：开始\n"
                "- Esc：清空\n"
                "- Ctrl+U：切换极致紧凑模式\n\n"
                "极致紧凑模式：\n"
                "- 隐藏按钮与历史，仅保留快捷键操作\n"
                "- 可在设置中启用/关闭，或用 Ctrl+U 快速切换\n\n"
            )
            messagebox.showinfo("关于", info)
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = KeyboardSimulatorApp(root)
    root.mainloop()