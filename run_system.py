import sys
import tkinter as tk
from tkinter import messagebox

def show_mode_selection():
    """显示模式选择窗口"""
    root = tk.Tk()
    root.title("自动注册系统 - 模式选择")
    root.geometry("400x200")
    root.resizable(False, False)
    
    # 设置窗口居中
    root.eval('tk::PlaceWindow . center')
    
    def start_cli():
        root.destroy()
        import main
        main.main()
    
    def start_gui():
        root.destroy()
        import ui_main
        ui_main.main()
    
    # 主容器
    main_container = tk.Frame(root, bg="#f0f0f0")
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 标题
    title_label = tk.Label(
        main_container, 
        text="自动注册系统", 
        font=("Arial", 18, "bold"),
        bg="#f0f0f0",
        fg="#333"
    )
    title_label.pack(pady=(0, 10))
    
    # 描述
    desc_label = tk.Label(
        main_container, 
        text="请选择运行模式", 
        font=("Arial", 12),
        bg="#f0f0f0",
        fg="#666"
    )
    desc_label.pack(pady=(0, 20))
    
    # 按钮框架
    button_frame = tk.Frame(main_container, bg="#f0f0f0")
    button_frame.pack(pady=10)
    
    # CLI按钮
    cli_button = tk.Button(
        button_frame,
        text="命令行界面 (CLI)",
        font=("Arial", 11),
        width=15,
        height=2,
        bg="#4a86e8",
        fg="white",
        activebackground="#3a76d8",
        relief=tk.FLAT,
        command=start_cli
    )
    cli_button.pack(side=tk.LEFT, padx=10)
    
    # GUI按钮
    gui_button = tk.Button(
        button_frame,
        text="图形用户界面 (GUI)",
        font=("Arial", 11),
        width=15,
        height=2,
        bg="#6aa84f",
        fg="white",
        activebackground="#5a983f",
        relief=tk.FLAT,
        command=start_gui
    )
    gui_button.pack(side=tk.LEFT, padx=10)
    
    # 退出按钮
    exit_btn = tk.Button(
        main_container,
        text="退出",
        font=("Arial", 10),
        width=10,
        command=root.destroy,
        bg="#e06666",
        fg="white",
        activebackground="#d05656",
        relief=tk.FLAT
    )
    exit_btn.pack(pady=(20, 0))
    
    # 绑定ESC键退出
    root.bind('<Escape>', lambda e: root.destroy())
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap('icon.ico')  # 如果没有图标文件则忽略
    except tk.TclError:
        pass  # 忽略图标错误
    
    root.mainloop()


if __name__ == "__main__":
    show_mode_selection()