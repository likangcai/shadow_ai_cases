# -*- coding: utf-8 -*-
# ----------------------------
# @Author:    影子
# @Software:  PyCharm
# @时间:       2025/8/2 下午2:36
# @项目:       chengxu
# @FileName:  paths.py
# ----------------------------
import os
from pathlib import Path


def get_folder_path(name="logs"):
    """
    获取指定文件夹的路径，如果不存在则返回错误信息。
    name: 文件夹名称
    """
    try:
        # 获取当前文件的路径
        current_file_path = Path(__file__).resolve()
        # 获取目标文件夹的路径
        target_directory = current_file_path.parent.parent / name
        # 检查文件夹是否存在，如果不存在则创建
        if not target_directory.exists():
            target_directory.mkdir(parents=True)
        # 返回目标文件夹的路径
        return str(target_directory) + "\\"
    except Exception as e:
        print(f"发生错误: {e}")
        return None


def get_file_path(file_name):
    """
    获取指定文件名的文件路径，如果文件不存在则返回错误信息。
    file_name: 文件名
    """
    try:
        # 获取当前文件路径
        current_file_path = Path(__file__).resolve()
        # 获取目标文件的路径
        target_file_path = current_file_path.parent.parent / file_name
        # 检查文件是否存在
        if not target_file_path.exists():
            raise FileNotFoundError(f"文件不存在: {target_file_path}")
        # 返回目标文件的路径
        return str(target_file_path)
    except Exception as e:
        print(f"发生错误: {e}")
        return None


if __name__ == '__main__':
    print(get_folder_path(name="static"))
    print(get_file_path(file_name="config.yaml"))
