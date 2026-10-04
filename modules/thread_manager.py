import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import uuid

class ThreadPoolManager:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.active_tasks = {}
        self.lock = threading.Lock()
        
    def submit_task(self, task_func, *args, **kwargs):
        """提交单个任务"""
        task_id = str(uuid.uuid4())
        future = self.executor.submit(task_func, *args, **kwargs)
        
        with self.lock:
            self.active_tasks[task_id] = {
                'future': future,
                'status': 'pending',
                'start_time': time.time()
            }
        
        # 添加回调处理结果
        future.add_done_callback(lambda f: self._task_done_callback(task_id, f))
        
        return task_id
    
    def _task_done_callback(self, task_id, future):
        """任务完成回调"""
        with self.lock:
            self.active_tasks[task_id]['status'] = 'completed'
            self.active_tasks[task_id]['end_time'] = time.time()
            
            try:
                result = future.result()
                self.active_tasks[task_id]['result'] = result
                self.active_tasks[task_id]['success'] = True
            except Exception as e:
                self.active_tasks[task_id]['result'] = str(e)
                self.active_tasks[task_id]['success'] = False
                self.active_tasks[task_id]['error'] = str(e)
    
    def batch_submit(self, task_list: List[Dict[str, Any]]):
        """批量提交任务"""
        task_ids = []
        for task_info in task_list:
            task_id = self.submit_task(
                task_info['func'],
                *task_info.get('args', []),
                **task_info.get('kwargs', {})
            )
            task_ids.append(task_id)
        return task_ids
    
    def wait_completion(self, timeout=None):
        """等待所有任务完成"""
        self.executor.shutdown(wait=True)
    
    def get_task_status(self, task_id=None):
        """获取任务状态"""
        with self.lock:
            if task_id:
                return self.active_tasks.get(task_id)
            return self.active_tasks.copy()
    
    def get_statistics(self):
        """获取统计信息"""
        with self.lock:
            total = len(self.active_tasks)
            completed = sum(1 for t in self.active_tasks.values() if t['status'] == 'completed')
            pending = total - completed
            success = sum(1 for t in self.active_tasks.values() if t.get('success'))
            
            return {
                'total_tasks': total,
                'completed': completed,
                'pending': pending,
                'success': success,
                'failure': completed - success if completed > 0 else 0
            }