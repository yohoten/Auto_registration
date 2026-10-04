class Config:
    # 网站配置
    TARGET_URL = "https://example.com"  # 需要替换为实际的目标网站
    REGISTER_URL = "https://example.com/register"  # 需要替换为实际的注册页面URL
    LOGIN_URL = "https://example.com/login"  # 需要替换为实际的登录页面URL

    # 注册限制
    MAX_REGISTRATION_PER_IP = 3
    REGISTRATION_INTERVAL = 86400  # 24小时

    # 代理设置
    PROXY_ENABLED = True
    PROXY_FILE = "proxies.txt"

    # 浏览器设置
    HEADLESS_MODE = False  # 调试时设为False，生产环境可以设为True
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