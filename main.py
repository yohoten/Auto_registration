import json
import csv
import time
import random
from datetime import datetime
import os
from config import Config
from database import Database
from modules.proxy_manager import ProxyManager
from modules.browser_controller import BrowserController
from modules.registration import RegistrationBot
from modules.multithread_registration import MultiThreadRegistration
from modules.account_validator import AccountValidator
from utils.logger import setup_logger


class AutoRegistrationSystem:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.db = Database()
        self.proxy_manager = ProxyManager()
        self.registration_bot = None
        
        # 确保必要的目录存在
        for dir_path in [Config.ACCOUNTS_INPUT_DIR, Config.ACCOUNTS_OUTPUT_DIR, Config.LOGS_DIR]:
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

    def import_accounts(self, file_path):
        """导入账号数据"""
        accounts = []
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
        elif file_path.endswith('.csv'):
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                accounts = list(reader)
        
        self.logger.info(f"Imported {len(accounts)} accounts from {file_path}")
        return accounts

    def export_accounts(self, output_format='json'):
        """导出账号数据"""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE status = "active"')
        accounts = cursor.fetchall()
        
        # 获取列名
        column_names = [description[0] for description in cursor.description]
        
        accounts_data = []
        for account in accounts:
            account_dict = dict(zip(column_names, account))
            accounts_data.append(account_dict)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'json':
            output_file = f"{Config.ACCOUNTS_OUTPUT_DIR}/accounts_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(accounts_data, f, indent=2, ensure_ascii=False, default=str)
        
        elif output_format == 'csv':
            output_file = f"{Config.ACCOUNTS_OUTPUT_DIR}/accounts_{timestamp}.csv"
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=column_names)
                writer.writeheader()
                writer.writerows(accounts_data)
        
        self.logger.info(f"Exported {len(accounts_data)} accounts to {output_file}")
        return output_file

    def export_logs(self, start_date=None, end_date=None):
        """导出日志"""
        cursor = self.db.conn.cursor()
        
        query = 'SELECT * FROM operation_logs WHERE 1=1'
        params = []
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        column_names = [description[0] for description in cursor.description]
        logs_data = []
        
        for log in logs:
            log_dict = dict(zip(column_names, log))
            # 解析details字段
            if log_dict.get('details'):
                try:
                    log_dict['details'] = json.loads(log_dict['details'])
                except:
                    pass
            logs_data.append(log_dict)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{Config.LOGS_DIR}/operations_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(logs_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Exported {len(logs_data)} logs to {output_file}")
        return output_file

    def batch_registration(self, count=10, use_multithreading=False, max_threads=3):
        """批量注册账号"""
        if use_multithreading:
            return self._batch_registration_multithreaded(count, max_threads)
        else:
            return self._batch_registration_single_threaded(count)

    def _batch_registration_single_threaded(self, count=10):
        """单线程批量注册账号"""
        successful_registrations = []
        failed_registrations = []
        
        for i in range(count):
            try:
                # 获取代理IP
                if Config.PROXY_ENABLED:
                    proxy = self.proxy_manager.get_available_proxy()
                    if not proxy:
                        self.logger.warning("No available proxies")
                        break
                else:
                    proxy = None
                
                # 创建浏览器实例
                browser = BrowserController(
                    headless=Config.HEADLESS_MODE,
                    proxy=proxy
                )
                browser.create_driver()
                
                # 创建注册机器人
                registration_bot = RegistrationBot(
                    browser_controller=browser,
                    proxy_manager=self.proxy_manager,
                    database=self.db
                )
                
                # 执行注册
                result = registration_bot.register_account(Config.REGISTER_URL)
                
                if result['success']:
                    successful_registrations.append(result)
                    self.logger.info(f"Successfully registered account {result['account_id']}")
                else:
                    failed_registrations.append(result)
                    self.logger.error(f"Failed to register account: {result.get('error', 'Unknown error')}")
                
                # 关闭浏览器
                browser.close()
                
                # 随机延迟，模拟人工操作
                time.sleep(random.uniform(5, 15))
                
                # 轮换代理IP
                if Config.PROXY_ENABLED and i % 3 == 0:
                    self.proxy_manager.rotate_proxy()
                
            except Exception as e:
                self.logger.error(f"Registration failed: {str(e)}")
                failed_registrations.append({'error': str(e)})
                
                # 检查是否是网络连接错误
                if "远程主机强迫关闭了一个现有的连接" in str(e) or "Connection reset by peer" in str(e):
                    self.logger.error("检测到网络连接错误，请检查:")
                    self.logger.error("1. 目标网站URL是否正确 (请参考 CONFIGURATION.md 进行配置)")
                    self.logger.error("2. 网络连接是否正常")
                    self.logger.error("3. 是否需要配置代理")
                
                continue
        
        # 生成报告
        report = {
            'total_attempted': count,
            'successful': len(successful_registrations),
            'failed': len(failed_registrations),
            'success_rate': len(successful_registrations) / count * 100 if count > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Batch registration completed: {report}")
        
        # 导出结果
        self.export_accounts()
        
        return report

    def _batch_registration_multithreaded(self, count=10, max_threads=3):
        """多线程批量注册账号"""
        multithread_reg = MultiThreadRegistration(
            config=Config,
            proxy_manager=self.proxy_manager,
            database=self.db,
            max_threads=max_threads
        )
        
        multithread_reg.start_registration_batch(count)
        
        # 等待完成
        import time
        while multithread_reg.get_progress()['queue_size'] > 0:
            progress = multithread_reg.get_progress()
            self.logger.info(f"Progress: {progress['queue_size']} tasks remaining, {progress['active_threads']} threads active")
            time.sleep(5)
        
        # 停止线程
        multithread_reg.stop()
        
        # 获取统计信息
        progress = multithread_reg.get_progress()
        successful = progress['successful_registrations']
        failed = progress['failed_registrations']
        
        report = {
            'total_attempted': count,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / count * 100 if count > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Multithreaded batch registration completed: {report}")
        
        # 导出结果
        self.export_accounts()
        
        return report

    def validate_accounts(self, count=10):
        """验证账号可用性"""
        validator = AccountValidator(Config, self.db)
        
        # 获取最近注册的账号进行验证
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT id, username, password, email, registration_date
            FROM accounts 
            WHERE validation_status IS NULL OR validation_status = 'pending'
            ORDER BY registration_date DESC
            LIMIT ?
        ''', (count,))
        
        accounts = []
        for row in cursor.fetchall():
            accounts.append({
                'id': row[0],
                'username': row[1],
                'password': row[2],
                'email': row[3]
            })
        
        if not accounts:
            self.logger.info("No accounts to validate")
            return
        
        self.logger.info(f"Starting validation for {len(accounts)} accounts")
        validator.start_validation(accounts_to_validate=accounts, max_threads=2)
        
        # 等待验证完成
        import time
        time.sleep(len(accounts) * 10)  # 粗略估算等待时间
        
        validator.stop_validation()
        
        stats = validator.get_validation_stats()
        self.logger.info(f"Validation completed: {stats}")

    def show_statistics(self):
        """显示统计信息"""
        stats = self.db.get_statistics()
        print("\n=== 统计信息 ===")
        print(f"总账号数: {stats['total_accounts']}")
        print(f"成功注册: {stats['successful_registrations']}")
        print(f"失败注册: {stats['failed_registrations']}")
        print(f"今日注册数: {stats['today_registrations']}")
        print("================")

    def interactive_menu(self):
        """交互式菜单"""
        while True:
            print("\n=== 自动注册系统 ===")
            print("1. 批量注册账号")
            print("2. 多线程批量注册账号")
            print("3. 验证账号可用性")
            print("4. 导入账号数据")
            print("5. 导出账号数据")
            print("6. 导出操作日志")
            print("7. 查看统计信息")
            print("8. 退出")
            
            choice = input("请选择操作: ")
            
            if choice == '1':
                count = int(input("请输入要注册的账号数量: "))
                result = self.batch_registration(count, use_multithreading=False)
                print(f"注册完成: {result}")
            
            elif choice == '2':
                count = int(input("请输入要注册的账号数量: "))
                max_threads = int(input("请输入最大线程数 (默认3): ") or "3")
                result = self.batch_registration(count, use_multithreading=True, max_threads=max_threads)
                print(f"注册完成: {result}")
            
            elif choice == '3':
                count = int(input("请输入要验证的账号数量: "))
                self.validate_accounts(count)
                print("验证完成")
            
            elif choice == '4':
                file_path = input("请输入文件路径: ")
                accounts = self.import_accounts(file_path)
                print(f"成功导入 {len(accounts)} 个账号")
            
            elif choice == '5':
                format_choice = input("导出格式 (json/csv): ").lower()
                if format_choice in ['json', 'csv']:
                    output_file = self.export_accounts(format_choice)
                    print(f"账号已导出到 {output_file}")
                else:
                    print("不支持的格式")
            
            elif choice == '6':
                output_file = self.export_logs()
                print(f"日志已导出到 {output_file}")
            
            elif choice == '7':
                self.show_statistics()
            
            elif choice == '8':
                print("退出系统")
                break
            
            else:
                print("无效选择")


def main():
    system = AutoRegistrationSystem()
    system.interactive_menu()


if __name__ == "__main__":
    main()