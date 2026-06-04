"""
日志模块
"""
import logging
import sys
from functools import wraps
import time


def get_logger(name="stock_trade"):
    """获取统一配置的日志记录器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def retry(max_attempts=3, delay=1, logger=None):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔（秒）
        logger: 日志记录器
    """
    if logger is None:
        logger = get_logger()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"[最终失败] {func.__name__}: {e}")
                        raise
                    logger.warning(f"[重试 {attempt+1}/{max_attempts}] {func.__name__}: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator
