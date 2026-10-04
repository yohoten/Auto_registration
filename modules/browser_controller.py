from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc
from config import Config


class BrowserController:
    def __init__(self, headless=None, proxy=None):
        self.headless = headless if headless is not None else Config.HEADLESS_MODE
        self.proxy = proxy
        self.driver = None

    def create_driver(self):
        """创建浏览器驱动"""
        options = uc.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        
        # 防检测设置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 添加一些额外的防检测选项
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        # 性能优化选项
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-translate")
        options.add_argument("--no-proxy-server")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-renderer-backgrounding")
        
        # 设置页面加载策略，加快页面加载速度
        options.page_load_strategy = 'eager'
        
        try:
            self.driver = uc.Chrome(options=options)
            
            # 执行JavaScript来隐藏自动化特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            
            # 设置超时
            self.driver.set_page_load_timeout(Config.BROWSER_TIMEOUT)
            
            return self.driver
        except WebDriverException as e:
            print(f"浏览器驱动创建失败: {e}")
            raise

    def wait_for_element(self, selector, by=By.CSS_SELECTOR, timeout=None):
        """等待元素出现"""
        timeout = timeout or Config.BROWSER_TIMEOUT
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except TimeoutException:
            print(f"等待元素超时: {selector}")
            raise

    def safe_click(self, element):
        """安全点击元素"""
        try:
            self.driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            print(f"点击元素失败: {e}")
            raise

    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"关闭浏览器失败: {e}")