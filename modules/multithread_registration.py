import threading
import time
import random
from queue import Queue
from typing import List, Dict

class MultiThreadRegistration:
    def __init__(self, config, proxy_manager, database, max_threads=5):
        self.config = config
        self.proxy_manager = proxy_manager
        self.db = database
        self.max_threads = max_threads
        self.thread_pool = []
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.running = False
        self.proxy_lock = threading.Lock()
        self.proxy_usage = {}
        self.successful_registrations = 0
        self.failed_registrations = 0
        self.lock = threading.Lock()
        
    def start_registration_batch(self, registration_count):
        """启动批量注册
        Args:
            registration_count (int): 需要注册的账号数量
        """
        self.running = True
        self._init_thread_pool(min(self.max_threads, registration_count))
        
        # 添加任务到队列（带优先级）
        for i in range(registration_count):
            priority = 0  # 默认优先级
            if i % 5 == 0:  # 每5个任务提高一次优先级
                priority = 1
            
            self.task_queue.put({
                'task_id': i,
                'target_url': self.config.REGISTER_URL,
                'priority': priority
            }, priority)
        
        # 添加停止信号
        for _ in range(len(self.thread_pool)):
            self.task_queue.put(None, 0)  # 最低优先级

    def _init_thread_pool(self, initial_size):
        """初始化线程池"""
        for i in range(initial_size):
            self._add_worker(f"Worker-{i+1}")

    def _add_worker(self, worker_name):
        """添加工作线程"""
        thread = threading.Thread(
            target=self._registration_worker,
            args=(worker_name,)
        )
        thread.daemon = True
        thread.start()
        self.thread_pool.append(thread)
        self.logger.info(f"Added new worker: {worker_name}")

    def _adjust_thread_pool(self):
        """动态调整线程池大小"""
        active_threads = sum(1 for t in self.thread_pool if t.is_alive())
        queue_size = self.task_queue.qsize()
        
        # 如果队列积压且线程未达上限，增加线程
        if queue_size > 5 and active_threads < self.max_threads:
            new_workers = min(queue_size // 3, self.max_threads - active_threads)
            for i in range(new_workers):
                worker_name = f"Dynamic-Worker-{len(self.thread_pool)+1}"
                self._add_worker(worker_name)
        
        # 如果队列空且线程过多，减少线程
        elif queue_size == 0 and active_threads > 1:
            for _ in range(min(2, active_threads - 1)):
                self.task_queue.put(None, 0)  # 发送停止信号
    
    from modules.error_handler import ErrorHandler

    def _registration_worker(self, worker_name):
        """工作线程函数"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    break
                
                # 获取代理IP
                proxy = self._get_available_proxy(worker_name)
                
                if not proxy:
                    error = Exception("No available proxy")
                    ErrorHandler.log_error(self.db, 'registration', error)
                    self.result_queue.put({
                        'worker': worker_name,
                        'task_id': task['task_id'],
                        'status': 'failed',
                        'error': str(error)
                    })
                    # 更新失败计数
                    with self.lock:
                        self.failed_registrations += 1
                    continue
                
                try:
                    # 执行注册
                    result = self._execute_registration(
                        task['target_url'], 
                        proxy, 
                        worker_name
                    )
                    
                    self.result_queue.put({
                        'worker': worker_name,
                        'task_id': task['task_id'],
                        'status': 'success' if result['success'] else 'failed',
                        'result': result,
                        'proxy': proxy
                    })
                    
                    # 更新计数
                    with self.lock:
                        if result['success']:
                            self.successful_registrations += 1
                        else:
                            self.failed_registrations += 1
                    
                except Exception as e:
                    ErrorHandler.log_error(self.db, 'registration', e, proxy)
                    self.result_queue.put({
                        'worker': worker_name,
                        'task_id': task['task_id'],
                        'status': 'failed',
                        'error': str(e),
                        'proxy': proxy
                    })
                    
                    # 更新失败计数
                    with self.lock:
                        self.failed_registrations += 1
                
                finally:
                    # 任务完成，标记
                    self.task_queue.task_done()
                    
                    # 随机延迟，避免请求过于密集
                    time.sleep(random.uniform(1, 3))
                    
            except queue.Empty:
                continue
    
    def _get_available_proxy(self, worker_name):
        """为工作线程获取可用的代理IP
        实现智能代理分配策略：
        1. 优先使用最近最少使用的代理
        2. 避免单个代理被过多线程使用
        3. 自动轮换高失败率的代理
        """
        with self.proxy_lock:
            # 获取所有可用代理
            available_proxies = self.proxy_manager.get_all_proxies()
            
            if not available_proxies:
                return None
                
            # 计算每个代理的得分
            proxy_scores = []
            for proxy in available_proxies:
                # 检查IP限制
                if not self.db.check_ip_limit(proxy):
                    continue
                    
                # 初始化使用记录
                if proxy not in self.proxy_usage:
                    self.proxy_usage[proxy] = {
                        'usage_count': 0,
                        'last_used': 0,
                        'workers': set(),
                        'success_rate': 1.0
                    }
                
                # 计算得分 (越高越好)
                score = 0
                
                # 1. 最近使用时间权重 (越久未使用得分越高)
                time_since_last_use = time.time() - self.proxy_usage[proxy]['last_used']
                score += min(time_since_last_use / 60, 10)  # 最大10分
                
                # 2. 使用次数权重 (使用越少得分越高)
                score += 10 - min(self.proxy_usage[proxy]['usage_count'], 10)
                
                # 3. 当前使用线程数权重 (使用线程越少得分越高)
                current_workers = len(self.proxy_usage[proxy]['workers'])
                score += 5 - min(current_workers, 5)
                
                # 4. 成功率权重 (成功率越高得分越高)
                score += self.proxy_usage[proxy]['success_rate'] * 5
                
                proxy_scores.append((proxy, score))
            
            if not proxy_scores:
                return None
                
            # 选择得分最高的代理
            best_proxy = max(proxy_scores, key=lambda x: x[1])[0]
            
            # 更新代理使用记录
            self.proxy_usage[best_proxy]['usage_count'] += 1
            self.proxy_usage[best_proxy]['last_used'] = time.time()
            self.proxy_usage[best_proxy]['workers'].add(worker_name)
            
            return best_proxy
    
    def _execute_registration(self, target_url, proxy, worker_name):
        """执行注册任务"""
        # 这里集成原有的注册逻辑
        from modules.registration import RegistrationBot
        from modules.browser_controller import BrowserController
        
        # 创建浏览器实例
        browser = BrowserController(
            headless=True,
            proxy=proxy
        )
        browser.create_driver()
        
        # 创建注册机器人
        registration_bot = RegistrationBot(
            browser_controller=browser,
            proxy_manager=self.proxy_manager,
            database=self.db
        )
        
        try:
            result = registration_bot.register_account(target_url)
            return result
        finally:
            browser.close()
    
    def stop(self):
        """停止所有工作线程"""
        self.running = False
        for thread in self.thread_pool:
            thread.join(timeout=5)
    
    def get_progress(self):
        """获取进度信息"""
        return {
            'queue_size': self.task_queue.qsize(),
            'active_threads': sum(1 for t in self.thread_pool if t.is_alive()),
            'proxy_usage': self.proxy_usage,
            'successful_registrations': self.successful_registrations,
            'failed_registrations': self.failed_registrations
        }