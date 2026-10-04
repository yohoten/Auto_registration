"""
数据库模块占位符
TODO: 实现完整的数据库功能
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import Config


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.connection = None
        self.cursor = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        
        # 创建账户表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                proxy_ip TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # 创建IP使用记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                usage_date DATE NOT NULL,
                registration_count INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建操作日志表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                account_id INTEGER,
                proxy_ip TEXT,
                status TEXT NOT NULL,
                duration_seconds REAL,
                step_details TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建错误日志表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                proxy_ip TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
    
    def check_ip_limit(self, ip_address: str) -> bool:
        """检查IP是否达到每日注册限制"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute(
                'SELECT registration_count FROM ip_usage WHERE ip_address = ? AND usage_date = ?',
                (ip_address, today)
            )
            result = self.cursor.fetchone()
            
            if result:
                registration_count = result[0]
                return registration_count < Config.MAX_DAILY_REGISTRATIONS_PER_IP
            else:
                # 如果没有记录，说明今天还没使用过
                return True
        except Exception as e:
            print(f"检查IP限制失败: {e}")
            return True  # 出错时允许继续
    
    def save_account(self, user_data: Dict[str, Any]) -> int:
        """保存账户信息"""
        try:
            self.cursor.execute('''
                INSERT INTO accounts (username, password, email, phone, proxy_ip)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_data.get('username'),
                user_data.get('password'),
                user_data.get('email'),
                user_data.get('phone'),
                user_data.get('proxy_ip')
            ))
            self.connection.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"保存账户失败: {e}")
            return -1
    
    def update_ip_usage(self, ip_address: str):
        """更新IP使用记录"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 检查是否已有今天的记录
            self.cursor.execute(
                'SELECT id, registration_count FROM ip_usage WHERE ip_address = ? AND usage_date = ?',
                (ip_address, today)
            )
            result = self.cursor.fetchone()
            
            if result:
                # 更新现有记录
                record_id, current_count = result
                self.cursor.execute(
                    'UPDATE ip_usage SET registration_count = ?, last_used = CURRENT_TIMESTAMP WHERE id = ?',
                    (current_count + 1, record_id)
                )
            else:
                # 插入新记录
                self.cursor.execute('''
                    INSERT INTO ip_usage (ip_address, usage_date, registration_count)
                    VALUES (?, ?, 1)
                ''', (ip_address, today))
            
            self.connection.commit()
        except Exception as e:
            print(f"更新IP使用记录失败: {e}")
    
    def log_operation(self, operation_data: Dict[str, Any]):
        """记录操作日志"""
        try:
            step_details = json.dumps(operation_data.get('step_details', {})) if operation_data.get('step_details') else None
            
            self.cursor.execute('''
                INSERT INTO operation_logs (operation_type, account_id, proxy_ip, status, duration_seconds, step_details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                operation_data.get('operation_type'),
                operation_data.get('account_id'),
                operation_data.get('proxy_ip'),
                operation_data.get('status'),
                operation_data.get('duration_seconds'),
                step_details
            ))
            self.connection.commit()
        except Exception as e:
            print(f"记录操作日志失败: {e}")
    
    def log_error(self, module_name: str, error_type: str, error_message: str, proxy_ip: str = None):
        """记录错误日志"""
        try:
            self.cursor.execute('''
                INSERT INTO error_logs (module_name, error_type, error_message, proxy_ip)
                VALUES (?, ?, ?, ?)
            ''', (module_name, error_type, error_message, proxy_ip))
            self.connection.commit()
        except Exception as e:
            print(f"记录错误日志失败: {e}")
    
    def get_accounts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取账户列表"""
        try:
            self.cursor.execute('''
                SELECT id, username, password, email, phone, proxy_ip, created_at, status
                FROM accounts
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            accounts = []
            for row in self.cursor.fetchall():
                accounts.append({
                    'id': row[0],
                    'username': row[1],
                    'password': row[2],
                    'email': row[3],
                    'phone': row[4],
                    'proxy_ip': row[5],
                    'created_at': row[6],
                    'status': row[7]
                })
            return accounts
        except Exception as e:
            print(f"获取账户列表失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 全局数据库实例
_db_instance = None


def get_database() -> Database:
    """获取数据库实例（单例模式）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance