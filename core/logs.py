# !/usr/bin/env/python3
# -*- coding: utf-8 -*-
# @Author  : 影子
# @Time    : 2025/8/3 18:47
# @File    : logs.py
# @Software: PyCharm
# @Description: log日志方法的简单实现
from loguru import logger
from datetime import datetime

from core.paths import get_folder_path

log_name = datetime.now().strftime("%Y-%m-%d")  # 以时间命名日志文件，格式为"年-月-日"

logger.add(f"{get_folder_path()}{log_name}.log",  # 文件名称和路径
           format="{time:YYYY-MM-DD HH:mm:ss} "  # 日期时间
                  # "| {process.name} "  # 进程名称
                  # "| {thread.name} "  # 线程名称
                  "| {level} "  # 等级
                  "| {module}.{name}.{function}:{line} "  # 模块名.名称.方法名:行号
                  "| {name}"  # 调用日志记录的名称
                  "| {line} "  # 行号
                  "| {message}",  # 日志内容
           level="DEBUG",
           rotation="10 MB",
           encoding='utf-8',
           enqueue=True,  # 支持异步
           backtrace=True,  # 完整性描述
           diagnose=True
           )


def catch():
    # 可以在线程或主线程中捕获异常 @logger.catch
    return logger.catch()


if __name__ == '__main__':
    logger.debug("调试")
    logger.info("记录")
    logger.error("错误")
    logger.warning("警告")
    logger.success("成功")
    logger.critical("critical\n")
    # logger.exception("异常追踪")
