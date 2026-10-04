import time
from datetime import datetime
from typing import Dict, Any

class ErrorHandler:
    """集中管理错误处理逻辑"""
    
    @staticmethod
    def classify_error(error: Exception) -> Dict[str, Any]:
        """分类错误类型
        Args:
            error (Exception): 错误对象
        Returns:
            dict: 包含错误类型和详细信息的字典
        """
        error_msg = str(error)
        
        # 网络相关错误
        net_errors = [
            "远程主机强迫关闭了一个现有的连接",
            "Connection reset by peer",
            "timed out",
            "网络连接错误"
        ]
        
        # 验证码相关错误
        captcha_errors = [
            "验证码错误",
            "captcha failed",
            "验证码识别失败"
        ]
        
        # 表单相关错误
        form_errors = [
            "找不到用户名输入框",
            "找不到密码输入框",
            "找不到邮箱输入框",
            "提交按钮不可点击"
        ]
        
        # 账号相关错误
        account_errors = [
            "用户名已存在",
            "email已注册",
            "账号限制"
        ]
        
        error_type = "unknown"
        if any(e in error_msg for e in net_errors):
            error_type = "network"
        elif any(e in error_msg for e in captcha_errors):
            error_type = "captcha"
        elif any(e in error_msg for e in form_errors):
            error_type = "form"
        elif any(e in error_msg for e in account_errors):
            error_type = "account"
        
        return {
            'type': error_type,
            'message': error_msg,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def get_failed_step_details(error: Exception) -> Dict[str, bool]:
        """获取失败步骤详情
        Args:
            error (Exception): 错误对象
        Returns:
            dict: 步骤状态字典
        """
        error_msg = str(error)
        steps = {
            'username_set': False,
            'password_set': False,
            'email_set': False,
            'captcha_passed': False,
            'form_submitted': False
        }
        
        # 根据错误信息判断已经完成的步骤
        if "找不到用户名输入框" not in error_msg:
            steps['username_set'] = True
            
            if "找不到密码输入框" not in error_msg:
                steps['password_set'] = True
                
                if "找不到邮箱输入框" not in error_msg:
                    steps['email_set'] = True
                    
                    if "验证码处理失败" not in error_msg:
                        steps['captcha_passed'] = True
                        
                        if "提交按钮不可点击" not in error_msg:
                            steps['form_submitted'] = True
        
        return steps

    @staticmethod
    def log_error(db, operation_type: str, error: Exception, proxy_ip: str = None) -> Dict[str, Any]:
        """记录错误日志
        Args:
            db: 数据库实例
            operation_type (str): 操作类型
            error (Exception): 错误对象
            proxy_ip (str): 使用的代理IP
        Returns:
            dict: 错误信息字典
        """
        error_info = ErrorHandler.classify_error(error)
        error_info['proxy_ip'] = proxy_ip
        
        db.log_operation({
            'operation_type': operation_type,
            'status': 'failed',
            'error_info': error_info,
            'step_details': ErrorHandler.get_failed_step_details(error)
        })
        
        return error_info
