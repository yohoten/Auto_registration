import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
import os
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import json

from main import AutoRegistrationSystem
from config import Config


class TerminalRedirector:
    """终端输出重定向器"""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.update()

    def flush(self):
        pass


class AutoRegistrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("自动注册系统 - 专业版")
        self.root.geometry("1000x600")
        
        self.system = AutoRegistrationSystem()
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 终端输出区域
        terminal_frame = ttk.LabelFrame(main_frame, text="终端输出", padding=10)
        terminal_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 终端输出文本框
        self.terminal_output = scrolledtext.ScrolledText(
            terminal_frame, 
            wrap=tk.WORD,
            bg="black",
            fg="white",
            font=("Consolas", 10)
        )
        self.terminal_output.pack(fill=tk.BOTH, expand=True)
        
        # 重定向标准输出和错误输出
        self.stdout_redirector = TerminalRedirector(self.terminal_output)
        self.stderr_redirector = TerminalRedirector(self.terminal_output)
        
        # 配置按钮
        config_btn = ttk.Button(control_frame, text="配置", command=self.open_config_window)
        config_btn.pack(fill=tk.X, pady=5)
        
        # 注册功能按钮
        ttk.Label(control_frame, text="账号注册").pack(anchor=tk.W)
        
        self.reg_count_var = tk.StringVar(value="10")
        reg_count_frame = ttk.Frame(control_frame)
        reg_count_frame.pack(fill=tk.X, pady=2)
        ttk.Label(reg_count_frame, text="数量:").pack(side=tk.LEFT)
        ttk.Entry(reg_count_frame, textvariable=self.reg_count_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # 单线程注册
        single_thread_btn = ttk.Button(
            control_frame, 
            text="单线程注册", 
            command=self.single_thread_registration
        )
        single_thread_btn.pack(fill=tk.X, pady=5)
        
        # 多线程注册
        multi_thread_btn = ttk.Button(
            control_frame, 
            text="多线程注册", 
            command=self.multi_thread_registration
        )
        multi_thread_btn.pack(fill=tk.X, pady=5)
        
        # 线程数设置
        self.thread_count_var = tk.StringVar(value="3")
        thread_count_frame = ttk.Frame(control_frame)
        thread_count_frame.pack(fill=tk.X, pady=2)
        ttk.Label(thread_count_frame, text="线程数:").pack(side=tk.LEFT)
        ttk.Entry(thread_count_frame, textvariable=self.thread_count_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # 账号验证
        ttk.Label(control_frame, text="账号验证").pack(anchor=tk.W, pady=(10, 0))
        
        self.val_count_var = tk.StringVar(value="10")
        val_count_frame = ttk.Frame(control_frame)
        val_count_frame.pack(fill=tk.X, pady=2)
        ttk.Label(val_count_frame, text="数量:").pack(side=tk.LEFT)
        ttk.Entry(val_count_frame, textvariable=self.val_count_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        validate_btn = ttk.Button(
            control_frame, 
            text="验证账号", 
            command=self.validate_accounts
        )
        validate_btn.pack(fill=tk.X, pady=5)
        
        # 数据导入导出
        ttk.Label(control_frame, text="数据操作").pack(anchor=tk.W, pady=(10, 0))
        
        import_btn = ttk.Button(control_frame, text="导入数据", command=self.import_data)
        import_btn.pack(fill=tk.X, pady=2)
        
        export_acc_btn = ttk.Button(control_frame, text="导出账号", command=self.export_accounts)
        export_acc_btn.pack(fill=tk.X, pady=2)
        
        export_log_btn = ttk.Button(control_frame, text="导出日志", command=self.export_logs)
        export_log_btn.pack(fill=tk.X, pady=2)
        
        # 统计信息
        stat_btn = ttk.Button(control_frame, text="查看统计", command=self.show_statistics)
        stat_btn.pack(fill=tk.X, pady=10)
        
        # 清空终端
        clear_btn = ttk.Button(control_frame, text="清空终端", command=self.clear_terminal)
        clear_btn.pack(fill=tk.X, pady=5)
        
        # 初始化重定向
        self.redirect_outputs()
        
        # 显示欢迎信息
        self.terminal_output.insert(tk.END, "自动注册系统 - 专业版\n")
        self.terminal_output.insert(tk.END, "系统已就绪...\n")
        self.terminal_output.insert(tk.END, "PS> ")
        
    def redirect_outputs(self):
        """重定向输出流"""
        sys.stdout = self.stdout_redirector
        sys.stderr = self.stderr_redirector
        
    def restore_outputs(self):
        """恢复原始输出流"""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
    def open_config_window(self):
        """打开配置窗口"""
        config_window = tk.Toplevel(self.root)
        config_window.title("系统配置")
        config_window.geometry("600x500")
        
        # 配置项框架
        config_frame = ttk.Frame(config_window, padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True)
        
        # 网站配置
        ttk.Label(config_frame, text="网站配置", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        # 目标URL
        target_frame = ttk.Frame(config_frame)
        target_frame.pack(fill=tk.X, pady=2)
        ttk.Label(target_frame, text="目标网站:", width=15).pack(side=tk.LEFT)
        self.target_url_var = tk.StringVar(value=Config.TARGET_URL)
        ttk.Entry(target_frame, textvariable=self.target_url_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 注册URL
        register_frame = ttk.Frame(config_frame)
        register_frame.pack(fill=tk.X, pady=2)
        ttk.Label(register_frame, text="注册页面:", width=15).pack(side=tk.LEFT)
        self.register_url_var = tk.StringVar(value=Config.REGISTER_URL)
        ttk.Entry(register_frame, textvariable=self.register_url_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 登录URL
        login_frame = ttk.Frame(config_frame)
        login_frame.pack(fill=tk.X, pady=2)
        ttk.Label(login_frame, text="登录页面:", width=15).pack(side=tk.LEFT)
        self.login_url_var = tk.StringVar(value=Config.LOGIN_URL)
        ttk.Entry(login_frame, textvariable=self.login_url_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 代理配置
        ttk.Label(config_frame, text="代理配置", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 0))
        
        self.proxy_enabled_var = tk.BooleanVar(value=Config.PROXY_ENABLED)
        proxy_enabled_cb = ttk.Checkbutton(
            config_frame, 
            text="启用代理", 
            variable=self.proxy_enabled_var
        )
        proxy_enabled_cb.pack(anchor=tk.W)
        
        proxy_file_frame = ttk.Frame(config_frame)
        proxy_file_frame.pack(fill=tk.X, pady=2)
        ttk.Label(proxy_file_frame, text="代理文件:", width=15).pack(side=tk.LEFT)
        self.proxy_file_var = tk.StringVar(value=Config.PROXY_FILE)
        proxy_entry = ttk.Entry(proxy_file_frame, textvariable=self.proxy_file_var)
        proxy_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            proxy_file_frame, 
            text="浏览", 
            command=lambda: self.browse_file(self.proxy_file_var)
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # 浏览器配置
        ttk.Label(config_frame, text="浏览器配置", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 0))
        
        self.headless_mode_var = tk.BooleanVar(value=Config.HEADLESS_MODE)
        headless_cb = ttk.Checkbutton(
            config_frame, 
            text="无头模式（后台运行）", 
            variable=self.headless_mode_var
        )
        headless_cb.pack(anchor=tk.W)
        
        # 限制配置
        ttk.Label(config_frame, text="注册限制", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(10, 0))
        
        ip_limit_frame = ttk.Frame(config_frame)
        ip_limit_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ip_limit_frame, text="每IP限制:", width=15).pack(side=tk.LEFT)
        self.ip_limit_var = tk.StringVar(value=str(Config.MAX_REGISTRATION_PER_IP))
        ttk.Entry(ip_limit_frame, textvariable=self.ip_limit_var, width=10).pack(side=tk.LEFT)
        ttk.Label(ip_limit_frame, text="次/24小时").pack(side=tk.LEFT, padx=(5, 0))
        
        # 保存配置按钮
        ttk.Button(
            config_frame, 
            text="保存配置", 
            command=self.save_config
        ).pack(pady=20)
    
    def browse_file(self, var):
        """浏览文件"""
        filename = filedialog.askopenfilename()
        if filename:
            var.set(filename)
    
    def save_config(self):
        """保存配置到文件"""
        # 临时创建一个字典来保存配置
        config_content = f'''
class Config:
    # 网站配置
    TARGET_URL = "{self.target_url_var.get()}"
    REGISTER_URL = "{self.register_url_var.get()}"
    LOGIN_URL = "{self.login_url_var.get()}"

    # 注册限制
    MAX_REGISTRATION_PER_IP = {int(self.ip_limit_var.get())}
    REGISTRATION_INTERVAL = 86400  # 24小时

    # 代理设置
    PROXY_ENABLED = {self.proxy_enabled_var.get()}
    PROXY_FILE = "{self.proxy_file_var.get()}"

    # 浏览器设置
    HEADLESS_MODE = {self.headless_mode_var.get()}
    BROWSER_TIMEOUT = 30

    # 验证码设置
    CAPTCHA_SERVICE = "local"  # local, 2captcha, anticaptcha
    CAPTCHA_API_KEY = ""

    # 日志设置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    # 数据库设置
    DATABASE_PATH = "database/accounts.db"

    # 账户数据目录
    ACCOUNTS_INPUT_DIR = "accounts/input"
    ACCOUNTS_OUTPUT_DIR = "accounts/output"
    LOGS_DIR = "logs"
'''
        
        # 写入配置文件
        with open("config.py", "w", encoding="utf-8") as f:
            f.write(config_content)
        
        messagebox.showinfo("配置", "配置已保存，请重启程序以应用更改")
    
    def run_in_thread(self, func, *args):
        """在新线程中运行函数"""
        def wrapper():
            try:
                func(*args)
            except Exception as e:
                print(f"错误: {e}")
        
        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()
    
    def single_thread_registration(self):
        """单线程注册"""
        try:
            count = int(self.reg_count_var.get())
            print(f"开始单线程注册 {count} 个账号...")
            self.run_in_thread(self.system._batch_registration_single_threaded, count)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def multi_thread_registration(self):
        """多线程注册"""
        try:
            count = int(self.reg_count_var.get())
            threads = int(self.thread_count_var.get())
            print(f"开始多线程注册 {count} 个账号，使用 {threads} 个线程...")
            self.run_in_thread(self.system._batch_registration_multithreaded, count, threads)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def validate_accounts(self):
        """验证账号"""
        try:
            count = int(self.val_count_var.get())
            print(f"开始验证 {count} 个账号...")
            self.run_in_thread(self.system.validate_accounts, count)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def import_data(self):
        """导入数据"""
        filename = filedialog.askopenfilename(
            title="选择账号数据文件",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")]
        )
        if filename:
            try:
                accounts = self.system.import_accounts(filename)
                print(f"成功导入 {len(accounts)} 个账号")
            except Exception as e:
                print(f"导入失败: {e}")
    
    def export_accounts(self):
        """导出账号"""
        try:
            output_file = self.system.export_accounts('json')
            print(f"账号已导出到 {output_file}")
        except Exception as e:
            print(f"导出失败: {e}")
    
    def export_logs(self):
        """导出日志"""
        try:
            output_file = self.system.export_logs()
            print(f"日志已导出到 {output_file}")
        except Exception as e:
            print(f"导出失败: {e}")
    
    def show_statistics(self):
        """显示统计信息"""
        try:
            stats = self.system.db.get_statistics()
            print("\n=== 统计信息 ===")
            print(f"总账号数: {stats['total_accounts']}")
            print(f"成功注册: {stats['successful_registrations']}")
            print(f"失败注册: {stats['failed_registrations']}")
            print(f"今日注册数: {stats['today_registrations']}")
            print("================\n")
        except Exception as e:
            print(f"获取统计信息失败: {e}")
    
    def clear_terminal(self):
        """清空终端"""
        self.terminal_output.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = AutoRegistrationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()