import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


class FileLogger:
    """文件日志生成器"""

    def __init__(self, log_dir='logs', name='app', level=logging.INFO, max_mb=10, backup_count=5):
        """
        初始化文件日志生成器

        参数:
            log_dir: 日志目录
            name: 日志名称
            level: 日志级别
            max_mb: 单个文件最大MB数
            backup_count: 备份文件数量
        """
        self.log_dir = log_dir
        self.name = name

        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)

        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 避免重复添加handler
        if not self.logger.handlers:
            self._add_handlers(max_mb, backup_count)

    def _add_handlers(self, max_mb, backup_count):
        """添加处理器"""

        # 日志文件路径（按日期命名）
        log_file = os.path.join(
            self.log_dir,
            f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        )

        # 文件处理器（轮转）
        max_bytes = max_mb * 1024 * 1024
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """获取logger对象"""
        return self.logger

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)


# 创建全局日志生成函数
def create_file_logger(name='app', log_dir='logs'):
    """快速创建文件日志生成器"""
    return FileLogger(log_dir=log_dir, name=name)


# 使用示例
if __name__ == '__main__':
    # 方式1：使用类
    log = FileLogger('logs', 'myapp')
    log.info("程序启动")
    log.error("发生错误", )

