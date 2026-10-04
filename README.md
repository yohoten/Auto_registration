# 网站自动注册系统

这是一个使用Python开发的网站自动注册系统，支持代理IP轮换、验证码处理和日志记录等功能。

## 功能特性

- 自动注册账号
- 代理IP管理（绕过IP限制）
- 随机用户数据生成
- 验证码处理（预留接口）
- 日志记录和导出
- 数据导入导出
- 统计报告
- **全新图形用户界面**：终端样式反馈，便捷配置功能
- **双模式运行**：支持命令行和图形界面模式

## 技术栈

- Python 3.9.13
- Selenium WebDriver
- Undetected ChromeDriver
- SQLite数据库
- Faker（随机数据生成）
- Tkinter（GUI界面）

## 安装依赖

```bash
 pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

```bash
PS D:\Auto_registration> py -3.13 -m venv venv
PS D:\Auto_registration> .\venv\Scripts\Activate.ps1
(venv) PS D:\Auto_registration> 
```

## 配置

编辑 [config.py](file:///d:/Auto_registration/config.py) 文件以适应您的需求：

- 修改目标网站URL
- 设置代理IP限制
- 配置浏览器选项
- 调整日志级别

或者使用全新的图形界面进行配置（推荐）。

## 使用方法

### 启动系统（推荐方式）

```bash
python run_system.py
```

此命令将启动模式选择界面，您可以选择使用命令行界面（CLI）或图形用户界面（GUI）。

### 图形用户界面（GUI）功能

- **终端样式输出窗口**：显示系统运行状态和日志
- **一键配置**：便捷修改系统配置
- **单/多线程注册**：灵活选择注册模式
- **账号验证**：验证已注册账号的可用性
- **数据导入导出**：方便的数据管理
- **实时统计**：查看系统运行统计信息

### 传统命令行界面（CLI）使用方法

#### 1. 准备代理IP

在 [proxies.txt](file:///d:/Auto_registration/proxies.txt) 文件中添加代理IP，每行一个，格式为 `IP:端口`：

```
proxy1.example.com:8080
proxy2.example.com:8080
123.45.67.89:3128
```

#### 2. 运行系统

```bash
python main.py
```

#### 3. 选择功能

在交互式菜单中选择相应功能：

- 批量注册账号
- 导入账号数据
- 导出账号数据
- 导出操作日志
- 查看统计信息

## 目录结构

```
auto_registration/
├── run_system.py         # 模式选择启动器
├── main.py              # 原始命令行主程序
├── ui_main.py           # 全新图形界面主程序
├── config.py            # 配置文件
├── database.py          # 数据库操作
├── proxies.txt          # 代理IP列表
├── requirements.txt     # 依赖包
├── README.md            # 说明文档
├── CONFIGURATION.md     # 配置指南
├── QUICK_START.md       # 快速启动指南
├── accounts/
│   ├── input/           # 导入账号文件
│   └── output/          # 导出账号文件
├── logs/                # 日志目录
├── modules/
│   ├── proxy_manager.py # 代理管理
│   ├── browser_controller.py # 浏览器控制
│   └── registration.py  # 注册逻辑
└── utils/
    └── logger.py        # 日志工具
```

## 注意事项

1. **合法合规**: 本系统仅供授权的测试和学习目的，请遵守相关法律法规
2. **频率控制**: 避免对目标网站造成过大压力，合理设置注册间隔
3. **代理质量**: 确保代理IP的稳定性和匿名性
4. **网站适配**: 根据目标网站的具体HTML结构调整选择器
5. **验证码处理**: 对于需要验证码的网站，需要集成打码服务

## 扩展功能

- 多线程支持：提高注册效率
- 验证码自动识别：集成第三方打码平台
- 分布式部署：多服务器协同工作
- **全新GUI界面**：终端样式反馈，直观易用
- 自动化测试：验证账号可用性
- 
## 步骤 2: 配置目标网站

编辑 [config.py](file:///d:/Auto_registration/config.py) 文件，将示例 URL 替换为您要注册的目标网站：

```python
# 网站配置 - 修改为您的目标网站
TARGET_URL = "https://example.com"           # 替换为目标网站主页
REGISTER_URL = "https://example.com/register" # 替换为目标网站注册页
LOGIN_URL = "https://example.com/login"      # 替换为目标网站登录页
```

## 步骤 3: 检查表单字段

检查目标网站的注册页面 HTML 结构，确保 [registration.py](file:///d:/Auto_registration/modules/registration.py) 中的选择器与目标网站匹配：

- 用户名字段: 通常是 `#username` 或 `[name="username"]`
- 密码字段: 通常是 `#password` 或 `[name="password"]`
- 邮箱字段: 通常是 `#email` 或 `[name="email"]`
- 提交按钮: 通常是 `button[type=submit]`

## 步骤 4: 运行系统

```bash
python main.py
```

## 常见问题

1. **网络连接错误**: 确认目标网站 URL 是否正确，以及网络连接是否正常
2. **元素找不到**: 检查表单字段选择器是否与目标网站匹配
3. **验证码问题**: 如需处理验证码，需要配置相应的打码服务

## 重要提醒

请确保您的使用符合目标网站的服务条款和法律法规。

## 贡献

欢迎提交Issue和Pull Request来改进此项目。# Auto_registration
