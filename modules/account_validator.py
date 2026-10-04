import threading
import time
import random
from queue import Queue, Empty
from typing import List, Dict, Any
from selenium.webdriver.common.by import By

class AccountValidator:
    def __init__(self, config, database):
        self.config = config
        self.db = database
        self.validation_queue = Queue()
        self.result_queue = Queue()
        self.validation_threads = []
        self.is_running = False
        
    def start_validation(self, accounts_to_validate=None, max_threads=3):
        """开始验证账号"""
        self.is_running = True
        
        # 如果未指定要验证的账号，则从数据库获取未验证的账号
        if accounts_to_validate is None:
            accounts_to_validate = self._get_unvalidated_accounts()
        
        # 添加验证任务到队列
        for account in accounts_to_validate:
            self.validation_queue.put(account)
        
        # 启动验证线程
        for i in range(min(max_threads, len(accounts_to_validate))):
            thread = threading.Thread(
                target=self._validation_worker,
                args=(f"Validator-{i+1}",)
            )
            thread.daemon = True
            self.validation_threads.append(thread)
            thread.start()
        
        # 启动结果处理线程
        result_thread = threading.Thread(target=self._result_processor)
        result_thread.daemon = True
        result_thread.start()
    
    def _validation_worker(self, worker_name):
        """验证工作线程"""
        while self.is_running and not self.validation_queue.empty():
            try:
                account = self.validation_queue.get(timeout=1)
                
                if account:
                    print(f"{worker_name} 开始验证账号: {account['username']}")
                    
                    # 执行验证
                    result = self._validate_single_account(account, worker_name)
                    
                    # 推送结果
                    self.result_queue.put(result)
                    
                    # 标记任务完成
                    self.validation_queue.task_done()
                    
                    # 随机延迟
                    time.sleep(random.uniform(1, 3))
                
            except Queue.Empty:
                continue
            except Exception as e:
                print(f"{worker_name} 验证错误: {e}")
                time.sleep(1)
    
    def _validate_single_account(self, account, worker_name):
        """验证单个账号"""
        from modules.browser_controller import BrowserController
        
        # 创建浏览器实例
        browser = BrowserController(headless=True)
        browser.create_driver()
        
        try:
            # 访问登录页面
            browser.driver.get(self.config.LOGIN_URL)
            time.sleep(random.uniform(2, 4))
            
            # 查找并填写登录表单
            # 根据目标网站的实际结构调整选择器
            try:
                username_field = browser.wait_for_element('#username, input[name="username"]')
                username_field.send_keys(account['username'])
                
                password_field = browser.wait_for_element('#password, input[name="password"], input[type="password"]')
                password_field.send_keys(account['password'])
                
                # 提交表单
                submit_button = browser.wait_for_element('button[type="submit"], input[type="submit"]')
                browser.safe_click(submit_button)
                
                # 等待登录完成
                time.sleep(random.uniform(3, 5))
                
                # 检查登录是否成功
                validation_result = self._check_login_success(browser.driver)
                
                # 记录验证结果
                self._record_validation_result(account['id'], validation_result)
                
                return {
                    'account_id': account['id'],
                    'username': account['username'],
                    'valid': validation_result['success'],
                    'details': validation_result,
                    'worker': worker_name,
                    'timestamp': time.time()
                }
                
            except Exception as e:
                # 表单填写或提交失败
                self._record_validation_result(account['id'], {
                    'success': False,
                    'error': f'Form submission failed: {str(e)}'
                })
                
                return {
                    'account_id': account['id'],
                    'username': account['username'],
                    'valid': False,
                    'error': str(e),
                    'worker': worker_name,
                    'timestamp': time.time()
                }
        except Exception as e:
            # 浏览器操作失败
            self._record_validation_result(account['id'], {
                'success': False,
                'error': f'Browser operation failed: {str(e)}'
            })
            
            return {
                'account_id': account['id'],
                'username': account['username'],
                'valid': False,
                'error': str(e),
                'worker': worker_name,
                'timestamp': time.time()
            }
            
        finally:
            browser.close()
    
    def _check_login_success(self, driver):
        """检查登录是否成功"""
        success_indicators = [
            # 成功登录后可能出现的元素
            '.welcome-message',
            '.user-menu',
            '.logout-button',
            '.dashboard',
            'text=欢迎',
            'text=Welcome',
            'text=我的账户'
        ]
        
        # 检查是否有错误消息
        error_indicators = [
            '.error-message',
            '.alert-danger',
            'text=密码错误',
            'text=账号不存在',
            'text=登录失败'
        ]
        
        try:
            # 检查成功指标
            for indicator in success_indicators:
                try:
                    if indicator.startswith('text='):
                        # 处理文本匹配逻辑
                        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '" + indicator[5:] + "')]")
                        if all_elements:
                            element = all_elements[0]
                            if element.is_displayed():
                                return {
                                    'success': True,
                                    'indicator': indicator,
                                    'message': 'Login successful'
                                }
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, indicator)
                        if element.is_displayed():
                            return {
                                'success': True,
                                'indicator': indicator,
                                'message': 'Login successful'
                            }
                except:
                    continue
            
            # 检查错误指标
            for indicator in error_indicators:
                try:
                    if indicator.startswith('text='):
                        # 处理文本匹配逻辑
                        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '" + indicator[5:] + "')]")
                        if all_elements:
                            element = all_elements[0]
                            if element.is_displayed():
                                return {
                                    'success': False,
                                    'indicator': indicator,
                                    'message': element.text[:100]  # 截取前100个字符
                                }
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, indicator)
                        if element.is_displayed():
                            return {
                                'success': False,
                                'indicator': indicator,
                                'message': element.text[:100]  # 截取前100个字符
                            }
                except:
                    continue
            
            # 检查URL变化
            current_url = driver.current_url
            if current_url != self.config.LOGIN_URL:
                # 可能已跳转到其他页面，视为成功
                return {
                    'success': True,
                    'indicator': 'url_redirect',
                    'message': f'Redirected to: {current_url}'
                }
            
            # 默认视为失败
            return {
                'success': False,
                'indicator': 'none',
                'message': 'No success or error indicators found'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_unvalidated_accounts(self, limit=100):
        """获取未验证的账号"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT id, username, password, email 
            FROM accounts 
            WHERE validation_status IS NULL OR validation_status = 'pending'
            LIMIT ?
        ''', (limit,))
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                'id': row[0],
                'username': row[1],
                'password': row[2],
                'email': row[3]
            })
        
        return accounts
    
    def _record_validation_result(self, account_id, result):
        """记录验证结果到数据库"""
        cursor = self.db.conn.cursor()
        
        validation_status = 'valid' if result['success'] else 'invalid'
        validation_time = time.time()
        
        cursor.execute('''
            UPDATE accounts 
            SET validation_status = ?, 
                validation_time = ?,
                validation_details = ?
            WHERE id = ?
        ''', (
            validation_status,
            validation_time,
            str(result),
            account_id
        ))
        
        self.db.conn.commit()
    
    def _result_processor(self):
        """处理验证结果"""
        while self.is_running:
            try:
                result = self.result_queue.get(timeout=1)
                if result:
                    self._log_validation_result(result)
                    
                    # 更新统计信息
                    self._update_validation_stats(result['valid'])
                    
            except Empty:
                continue
            except Exception as e:
                print(f"结果处理错误: {e}")
                time.sleep(1)
    
    def _log_validation_result(self, result):
        """记录验证结果日志"""
        log_data = {
            'operation_type': 'account_validation',
            'account_id': result.get('account_id'),
            'status': 'success' if result.get('valid') else 'failed',
            'message': f"Account validation {'successful' if result.get('valid') else 'failed'} for {result.get('username')}",
            'details': result
        }
        
        self.db.log_operation(log_data)
    
    def _update_validation_stats(self, is_valid):
        """更新验证统计"""
        # 可以在这里实现实时统计更新
        pass
    
    def stop_validation(self):
        """停止验证"""
        self.is_running = False
        
        for thread in self.validation_threads:
            thread.join(timeout=5)
        
        # 等待队列中的任务完成
        self.validation_queue.join()
    
    def get_validation_stats(self):
        """获取验证统计"""
        cursor = self.db.conn.cursor()
        
        # 统计验证结果
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN validation_status = 'valid' THEN 1 ELSE 0 END) as valid,
                SUM(CASE WHEN validation_status = 'invalid' THEN 1 ELSE 0 END) as invalid,
                SUM(CASE WHEN validation_status IS NULL THEN 1 ELSE 0 END) as unvalidated
            FROM accounts
        ''')
        
        stats = cursor.fetchone()
        
        return {
            'total_accounts': stats[0],
            'valid_accounts': stats[1],
            'invalid_accounts': stats[2],
            'unvalidated_accounts': stats[3],
            'validation_rate': stats[1] / stats[0] * 100 if stats[0] > 0 else 0
        }