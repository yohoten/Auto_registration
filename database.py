import sqlite3
from datetime import datetime
import json
import os
from config import Config


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        
        # 确保数据库目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """创建必要的数据表"""
        cursor = self.conn.cursor()
        
        # 账号表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                phone TEXT,
                registration_date TIMESTAMP,
                status TEXT,
                proxy_ip TEXT,
                site_id INTEGER,
                validation_status TEXT,
                validation_time TIMESTAMP,
                validation_details TEXT
            )
        ''')
        
        # 代理使用记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxy_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proxy_ip TEXT,
                registration_date DATE,
                usage_count INTEGER DEFAULT 0,
                UNIQUE(proxy_ip, registration_date)
            )
        ''')
        
        # 操作日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                operation_type TEXT,
                account_id INTEGER,
                proxy_ip TEXT,
                status TEXT,
                message TEXT,
                details TEXT
            )
        ''')
        
        self.conn.commit()

    def check_ip_limit(self, proxy_ip):
        """检查IP是否超过每日限制"""
        cursor = self.conn.cursor()
        today = datetime.now().date()
        
        cursor.execute('''
            SELECT usage_count FROM proxy_usage 
            WHERE proxy_ip = ? AND registration_date = ?
        ''', (proxy_ip, today))
        
        result = cursor.fetchone()
        if result and result[0] >= Config.MAX_REGISTRATION_PER_IP:
            return False
        return True

    def update_ip_usage(self, proxy_ip):
        """更新IP使用次数"""
        cursor = self.conn.cursor()
        today = datetime.now().date()
        
        cursor.execute('''
            INSERT INTO proxy_usage (proxy_ip, registration_date, usage_count)
            VALUES (?, ?, 1)
            ON CONFLICT(proxy_ip, registration_date) 
            DO UPDATE SET usage_count = usage_count + 1
        ''', (proxy_ip, today))
        
        self.conn.commit()

    def save_account(self, account_data):
        """保存账号信息"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, password, email, phone, 
                                 registration_date, status, proxy_ip)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            account_data['username'],
            account_data['password'],
            account_data.get('email'),
            account_data.get('phone'),
            datetime.now(),
            'active',
            account_data.get('proxy_ip')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_account_by_id(self, account_id):
        """通过ID获取账号信息"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None

    def log_operation(self, log_data):
        """记录操作日志"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO operation_logs 
            (timestamp, operation_type, account_id, proxy_ip, status, message, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(),
            log_data['operation_type'],
            log_data.get('account_id'),
            log_data.get('proxy_ip'),
            log_data['status'],
            log_data['message'],
            json.dumps(log_data.get('details', {}))
        ))
        self.conn.commit()

    def get_statistics(self):
        """获取系统统计数据"""
        cursor = self.conn.cursor()
        
        # 总账号数
        cursor.execute("SELECT COUNT(*) FROM accounts")
        total_accounts = cursor.fetchone()[0]
        
        # 成功注册数
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'")
        successful_registrations = cursor.fetchone()[0]
        
        # 失败数
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE status = 'failed'")
        failed_registrations = cursor.fetchone()[0]
        
        # 今日注册数
        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*) FROM operation_logs WHERE operation_type = 'registration' AND date(timestamp) = ?", (today,))
        today_registrations = cursor.fetchone()[0]
        
        return {
            'total_accounts': total_accounts,
            'successful_registrations': successful_registrations,
            'failed_registrations': failed_registrations,
            'today_registrations': today_registrations
        }