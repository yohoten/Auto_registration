import logging
import os
from datetime import datetime
from config import Config


def setup_logger(name=None, log_file=None, level=None):
    """
    设置日志记录器
    :param name: Logger名称
    :param log_file: 日志文件路径
    :param level: 日志级别
    :return: 配置好的logger对象
    """
    name = name or __name__
    level = level or getattr(logging, Config.LOG_LEVEL)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(Config.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件路径，也写入文件
    if log_file or Config.LOGS_DIR:
        log_dir = Config.LOGS_DIR
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        if not log_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(log_dir, f'auto_registration_{timestamp}.log')
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger