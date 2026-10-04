import redis
import json
import pickle
from typing import Dict, Any
import time

class RedisTaskQueue:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.task_queue_key = 'registration:tasks'
        self.result_queue_key = 'registration:results'
        self.worker_status_key = 'registration:workers'
    
    def push_task(self, task_data: Dict[str, Any]):
        """推送任务到队列"""
        task_id = f"task_{int(time.time() * 1000)}_{hash(str(task_data))}"
        task_data['task_id'] = task_id
        task_data['created_at'] = time.time()
        task_data['status'] = 'pending'
        
        # 序列化任务数据
        task_serialized = json.dumps(task_data)
        
        # 推送到队列
        self.redis_client.lpush(self.task_queue_key, task_serialized)
        
        return task_id
    
    def pop_task(self, timeout=0):
        """从队列获取任务"""
        result = self.redis_client.brpop(self.task_queue_key, timeout=timeout)
        if result:
            task_data = json.loads(result[1])
            task_data['assigned_at'] = time.time()
            task_data['status'] = 'processing'
            return task_data
        return None
    
    def push_result(self, result_data: Dict[str, Any]):
        """推送结果到结果队列"""
        result_serialized = json.dumps(result_data)
        self.redis_client.lpush(self.result_queue_key, result_serialized)
    
    def get_pending_tasks_count(self):
        """获取待处理任务数量"""
        return self.redis_client.llen(self.task_queue_key)
    
    def register_worker(self, worker_id, worker_info):
        """注册工作节点"""
        worker_key = f"{self.worker_status_key}:{worker_id}"
        worker_info['last_heartbeat'] = time.time()
        worker_info['status'] = 'active'
        
        self.redis_client.hset(
            worker_key,
            mapping=worker_info
        )
        
        # 设置过期时间（30秒无心跳则认为离线）
        self.redis_client.expire(worker_key, 30)
    
    def update_worker_heartbeat(self, worker_id):
        """更新工作节点心跳"""
        worker_key = f"{self.worker_status_key}:{worker_id}"
        self.redis_client.hset(worker_key, 'last_heartbeat', time.time())
        self.redis_client.expire(worker_key, 30)
    
    def get_active_workers(self):
        """获取活跃的工作节点"""
        worker_keys = self.redis_client.keys(f"{self.worker_status_key}:*")
        workers = []
        
        for key in worker_keys:
            worker_data = self.redis_client.hgetall(key)
            if worker_data:
                workers.append({
                    'id': key.split(':')[-1],
                    **worker_data
                })
        
        return workers