# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2025/8/5 12:00
# @Software  : PyCharm
# @FileName  : exporter.py
# -----------------------------
"""输出文件逻辑处理"""
import csv
import json
from typing import List, Dict

import pandas as pd

from core.logs import logger


def export(cases: List[Dict], fmt: str, file_path: str):
    """统一导出"""
    try:
        if fmt == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cases, f, ensure_ascii=False, indent=2)
        elif fmt in {"xls", "xlsx"}:
            # 处理所有字段的换行符
            processed_cases = []
            for c in cases:
                processed_case = c.copy()
                
                # 处理操作步骤
                steps = processed_case.get('操作步骤', '')
                if isinstance(steps, list):
                    # 使用Excel可识别的换行符
                    processed_case['操作步骤'] = '\r\n'.join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                else:
                    # 处理字符串中的换行符
                    steps_str = str(steps)
                    processed_case['操作步骤'] = steps_str.replace('\\n', '\r\n').replace('\n', '\r\n')
                
                # 处理其他字段
                for key in processed_case:
                    if key != '操作步骤':
                        value = processed_case[key]
                        if isinstance(value, str):
                            processed_case[key] = value.replace('\\n', '\r\n').replace('\n', '\r\n')
                
                processed_cases.append(processed_case)
            
            # 创建DataFrame并设置单元格格式为自动换行
            df = pd.DataFrame(processed_cases)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='测试用例')
                # 获取工作表
                worksheet = writer.sheets['测试用例']
                # 设置所有单元格自动换行
                for column in worksheet.columns:
                    for cell in column:
                        cell.alignment = cell.alignment.copy(wrapText=True)
        elif fmt == "csv":
            # 处理所有字段的换行符
            processed_cases = []
            for c in cases:
                processed_case = c.copy()
                
                # 处理操作步骤
                steps = processed_case.get('操作步骤', '')
                if isinstance(steps, list):
                    # 使用CSV可识别的换行符
                    processed_case['操作步骤'] = '\r\n'.join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                else:
                    # 处理字符串中的换行符
                    steps_str = str(steps)
                    processed_case['操作步骤'] = steps_str.replace('\\n', '\r\n').replace('\n', '\r\n')
                
                # 处理其他字段
                for key in processed_case:
                    if key != '操作步骤':
                        value = processed_case[key]
                        if isinstance(value, str):
                            processed_case[key] = value.replace('\\n', '\r\n').replace('\n', '\r\n')
                
                processed_cases.append(processed_case)
            pd.DataFrame(processed_cases).to_csv(file_path, index=False, quoting=csv.QUOTE_ALL)
        elif fmt == "md":
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("| 用例编号 | 用例标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |\n")
                f.write("| --- | --- | --- | --- | --- | --- |\n")
                for c in cases:
                    # 处理操作步骤可能是列表的情况
                    steps = c.get('操作步骤', '')
                    if isinstance(steps, list):
                        steps_str = '<br>'.join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                    else:
                        steps_str = str(steps).replace('\\n', '<br>').replace('\n', '<br>')
                    
                    # 处理其他字段中的换行符
                    case_id = str(c.get('用例编号', '')).replace('\\n', '<br>').replace('\n', '<br>')
                    case_title = str(c.get('用例标题', '')).replace('\\n', '<br>').replace('\n', '<br>')
                    precondition = str(c.get('前置条件', '')).replace('\\n', '<br>').replace('\n', '<br>')
                    expected_result = str(c.get('预期结果', '')).replace('\\n', '<br>').replace('\n', '<br>')
                    priority = str(c.get('优先级', '')).replace('\\n', '<br>').replace('\n', '<br>')
                    
                    f.write(
                        f"| {case_id} | {case_title} | {precondition} | {steps_str} | {expected_result} | {priority} |\n")
        else:
            raise ValueError("不支持的导出格式")
    except Exception as e:
        logger.error(f"导出失败: {e}")
        raise RuntimeError(f"导出失败: {e}")


if __name__ == '__main__':
    aa = '''
    [
    {
        "用例编号": "TC001",
        "用例标题": "验证用户名长度在8到20个字符之间且不包含特殊字符",
        "前置条件": "用户已打开登录页面",
        "操作步骤": [
            "输入用户名为7个字符（如：abcdefg）",
            "点击登录按钮"
        ],
        "预期结果": "系统提示用户名长度不符合要求",
        "优先级": "高"
    },
    {
        "用例编号": "TC002",
        "用例标题": "验证用户名长度在8到20个字符之间且不包含特殊字符",
        "前置条件": "用户已打开登录页面",
        "操作步骤": [
            "输入用户名为21个字符（如：abcdefghijklmnopqrstu）",
            "点击登录按钮"
        ],
        "预期结果": "系统提示用户名长度不符合要求",
        "优先级": "高"
    }
]
    '''
    export(json.loads(aa), "md", "test.md")
