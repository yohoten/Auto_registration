import time
import random
from faker import Faker
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException
from urllib.error import URLError
from config import Config


class RegistrationBot:
    def __init__(self, browser_controller, proxy_manager, database):
        self.browser = browser_controller
        self.proxy_manager = proxy_manager
        self.db = database
        self.faker = Faker()

    def generate_user_data(self):
        """生成随机用户数据"""
        username = self.faker.user_name() + str(random.randint(100, 999))
        password = self.faker.password(length=12)
        email = self.faker.email()
        phone = self.faker.phone_number()
        
        return {
            'username': username,
            'password': password,
            'email': email,
            'phone': phone
        }

    from modules.error_handler import ErrorHandler

    def register_account(self, target_url=None, user_data=None):
        """执行注册流程"""
        target_url = target_url or Config.REGISTER_URL
        if not user_data:
            user_data = self.generate_user_data()
        
        # 检查IP限制
        proxy_ip = self.browser.proxy
        if proxy_ip and not self.db.check_ip_limit(proxy_ip):
            error = Exception(f"IP {proxy_ip} 已达到每日注册限制")
            ErrorHandler.log_error(self.db, 'registration', error, proxy_ip)
            raise error
        
        try:
            # 访问注册页面
            self.browser.driver.get(target_url)
            time.sleep(random.uniform(2, 4))
            
            # 记录开始时间
            start_time = time.time()
            
            # 根据实际网站结构填写表单
            # 示例：查找并填写用户名
            try:
                username_input = self.browser.wait_for_element('#username, [name="username"]')
                username_input.clear()
                username_input.send_keys(user_data['username'])
            except (TimeoutException, NoSuchElementException):
                error = Exception("找不到用户名输入框")
                raise error
            
            # 填写密码
            try:
                password_input = self.browser.wait_for_element('#password, [name="password"]')
                password_input.clear()
                password_input.send_keys(user_data['password'])
            except (TimeoutException, NoSuchElementException):
                error = Exception("找不到密码输入框")
                raise error
            
            # 填写确认密码（如果有）
            try:
                confirm_input = self.browser.driver.find_element(By.CSS_SELECTOR, '#confirm_password, [name="confirm_password"]')
                confirm_input.clear()
                confirm_input.send_keys(user_data['password'])
            except NoSuchElementException:
                # 如果没有确认密码字段，忽略
                pass
            
            # 填写邮箱
            try:
                email_input = self.browser.wait_for_element('#email, [name="email"]')
                email_input.clear()
                email_input.send_keys(user_data['email'])
            except (TimeoutException, NoSuchElementException):
                error = Exception("找不到邮箱输入框")
                raise error
            
            # 处理验证码（如果需要）
            if not self.solve_captcha_if_needed():
                error = Exception("验证码处理失败")
                raise error
            
            # 提交表单
            try:
                submit_button = self.browser.wait_for_element('button[type=submit], input[type=submit]')
                self.browser.safe_click(submit_button)
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                error = Exception(f"提交按钮不可点击: {str(e)}")
                raise error
            
            time.sleep(random.uniform(3, 5))
            
            # 检查注册是否成功
            if self.check_registration_success():
                # 保存账号信息
                user_data['proxy_ip'] = proxy_ip
                account_id = self.db.save_account(user_data)
                
                # 更新IP使用记录
                if proxy_ip:
                    self.db.update_ip_usage(proxy_ip)
                
                # 计算耗时
                duration = round(time.time() - start_time, 2)
                
                # 记录成功日志
                self.db.log_operation({
                    'operation_type': 'registration',
                    'account_id': account_id,
                    'proxy_ip': proxy_ip,
                    'status': 'success',
                    'duration_seconds': duration,
                    'step_details': {
                        'username_set': True,
                        'password_set': True,
                        'email_set': True,
                        'captcha_passed': True,
                        'form_submitted': True
                    }
                })
                
                return {
                    'success': True, 
                    'account_id': account_id, 
                    'data': user_data,
                    'duration_seconds': duration
                }
            else:
                error = Exception("注册成功检查失败")
                raise error
                
        except Exception as e:
            # 计算耗时
            duration = round(time.time() - start_time, 2)
            error_info = ErrorHandler.log_error(self.db, 'registration', e, proxy_ip)
            error_info['duration_seconds'] = duration
            raise

    def solve_captcha_if_needed(self, max_retries=3):
        """处理验证码
        Args:
            max_retries (int): 最大重试次数
        Returns:
            bool: 验证码处理是否成功
        """
        try:
            captcha_input = self.browser.driver.find_element(
                By.CSS_SELECTOR, '#captcha, [name="captcha"]')
            
            # 实例化验证码识别模块
            from modules.captcha_model import CaptchaCNNModel
            captcha_solver = CaptchaCNNModel()
            
            for attempt in range(max_retries):
                try:
                    # 1. 获取验证码截图
                    captcha_img = self.browser.get_element_screenshot(captcha_input)
                    
                    # 2. 调用验证码识别
                    captcha_text = captcha_solver.predict(captcha_img)
                    
                    if not captcha_text:
                        raise ValueError("验证码识别失败")
                    
                    # 3. 填写验证码
                    captcha_input.clear()
                    captcha_input.send_keys(captcha_text)
                    
                    self.logger.info(f"第{attempt+1}次尝试验证码识别成功")
                    return True
                
                except Exception as e:
                    self.logger.warning(f"验证码识别失败: {str(e)}")
                    
                    # 点击刷新验证码按钮（如果有）
                    try:
                        refresh_btn = self.browser.driver.find_element(
                            By.CSS_SELECTOR, '.captcha-refresh, #reload-captcha')
                        refresh_btn.click()
                        time.sleep(2)  # 等待新验证码加载
                    except NoSuchElementException:
                        pass
            
            self.logger.error(f"经过{max_retries}次尝试仍无法识别验证码")
            return False
            
        except NoSuchElementException:
            # 如果没有找到验证码输入框，继续
            return True

    def check_registration_success(self):
        """检查注册是否成功"""
        # 根据网站成功后的特征判断
        # 例如：检查是否有欢迎信息、是否跳转到特定页面等
        try:
            # 尝试查找成功消息
            success_elements = [
                '.success-message',
                '.welcome-text',
                '.registration-success',
                '[data-testid="success-message"]',
                'h1',  # 或者检查标题变化
            ]
            
            for selector in success_elements:
                try:
                    success_element = self.browser.driver.find_element(By.CSS_SELECTOR, selector)
                    if success_element.is_displayed():
                        text = success_element.text.lower()
                        # 根据可能的成功提示文本判断
                        success_keywords = ['success', 'welcome', 'registered', 'activated', 'done', '完成', '成功', '注册']
                        if any(keyword in text for keyword in success_keywords):
                            return True
                except NoSuchElementException:
                    continue
                    
            # 检查URL变化
            current_url = self.browser.driver.current_url
            if 'dashboard' in current_url or 'home' in current_url or 'profile' in current_url:
                return True
                
        except Exception:
            pass
        
        return False