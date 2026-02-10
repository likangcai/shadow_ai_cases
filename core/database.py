#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库操作模块，此处使用轻量数据库sqlite3，也可以根据实际情况更换为其他数据库如MYSQL/PG等
"""
import sqlite3
import os
import json
from typing import Dict, List, Optional
from datetime import datetime

from core.logs import logger

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.db")


def init_db():
    """
    初始化数据库
    """
    try:
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enable_review BOOLEAN DEFAULT 1,  -- 是否启用专家评审，默认启用
            test_case_count INTEGER DEFAULT NULL,  -- 测试用例数量，NULL表示不限制
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 更新时间
        )
        ''')
        
        # 创建模型配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS llm_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,  -- 模型类型：default（默认生成）或review（评审）
            provider TEXT NOT NULL,  -- 模型提供商
            api_key TEXT NOT NULL,  -- API密钥
            base_url TEXT NOT NULL,  -- API基础URL
            model TEXT NOT NULL,  -- 模型名称
            status BOOLEAN DEFAULT 0,  -- 状态：0=禁用，1=启用
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 更新时间
            UNIQUE(type, provider, model)  -- 确保同一类型、提供商和模型的配置唯一
        )
        ''')
        
        # 创建索引，提高根据类型和状态查询模型配置的性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_models_type_status ON llm_models(type, status)')
        
        # 初始化默认用户配置
        cursor.execute('INSERT OR IGNORE INTO user_configs (enable_review, test_case_count) VALUES (1, NULL)')
        
        # 提交并关闭连接
        conn.commit()
        conn.close()
        
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def get_user_config() -> Dict:
    """
    获取用户配置
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_configs ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'enable_review': bool(row['enable_review']),
                'test_case_count': row['test_case_count'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        else:
            # 如果没有配置，返回默认值
            return {
                'enable_review': True,
                'test_case_count': None
            }
    except Exception as e:
        logger.error(f"获取用户配置失败: {e}")
        # 返回默认值
        return {
            'enable_review': True,
            'test_case_count': None
        }


def update_user_config(enable_review: bool, test_case_count: Optional[int]) -> bool:
    """
    更新用户配置
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查是否已有配置
        cursor.execute('SELECT COUNT(*) FROM user_configs')
        count = cursor.fetchone()[0]
        
        if count > 0:
            # 更新现有配置
            cursor.execute('''
            UPDATE user_configs 
            SET enable_review = ?, test_case_count = ?, updated_at = ?
            WHERE id = (SELECT MAX(id) FROM user_configs)
            ''', (enable_review, test_case_count, datetime.now().isoformat()))
        else:
            # 插入新配置
            cursor.execute('''
            INSERT INTO user_configs (enable_review, test_case_count, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ''', (enable_review, test_case_count, datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"用户配置更新成功: enable_review={enable_review}, test_case_count={test_case_count}")
        return True
    except Exception as e:
        logger.error(f"更新用户配置失败: {e}")
        return False


def get_llm_model_config(model_type: str) -> Optional[Dict]:
    """
    获取指定类型的启用模型配置
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM llm_models 
        WHERE type = ? AND status = 1 
        ORDER BY id DESC LIMIT 1
        ''', (model_type,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'type': row['type'],
                'provider': row['provider'],
                'api_key': row['api_key'],
                'base_url': row['base_url'],
                'model': row['model'],
                'status': bool(row['status'])
            }
        else:
            return None
    except Exception as e:
        logger.error(f"获取模型配置失败: {e}")
        return None


def add_llm_model_config(model_type: str, provider: str, api_key: str, base_url: str, model: str, status: bool) -> bool:
    """
    添加或更新模型配置
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 如果要启用该模型，先禁用同类型的其他模型
        if status:
            cursor.execute('''
            UPDATE llm_models 
            SET status = 0, updated_at = ?
            WHERE type = ? AND status = 1
            ''', (datetime.now().isoformat(), model_type))
        
        # 尝试插入新配置
        try:
            cursor.execute('''
            INSERT INTO llm_models (type, provider, api_key, base_url, model, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (model_type, provider, api_key, base_url, model, status, datetime.now().isoformat(), datetime.now().isoformat()))
        except sqlite3.IntegrityError:
            # 如果已存在，更新配置
            cursor.execute('''
            UPDATE llm_models 
            SET api_key = ?, base_url = ?, status = ?, updated_at = ?
            WHERE type = ? AND provider = ? AND model = ?
            ''', (api_key, base_url, status, datetime.now().isoformat(), model_type, provider, model))
        
        conn.commit()
        conn.close()
        
        logger.info(f"模型配置更新成功: type={model_type}, provider={provider}, model={model}, status={status}")
        return True
    except Exception as e:
        logger.error(f"更新模型配置失败: {e}")
        return False


def get_all_llm_models(model_type: Optional[str] = None) -> List[Dict]:
    """
    获取所有模型配置
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if model_type:
            cursor.execute('SELECT * FROM llm_models WHERE type = ? ORDER BY status DESC, id DESC', (model_type,))
        else:
            cursor.execute('SELECT * FROM llm_models ORDER BY type, status DESC, id DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row['id'],
            'type': row['type'],
            'provider': row['provider'],
            'api_key': row['api_key'],
            'base_url': row['base_url'],
            'model': row['model'],
            'status': bool(row['status']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        } for row in rows]
    except Exception as e:
        logger.error(f"获取模型配置列表失败: {e}")
        return []


def disable_llm_model(model_id: int) -> bool:
    """
    禁用模型
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE llm_models 
        SET status = 0, updated_at = ?
        WHERE id = ?
        ''', (datetime.now().isoformat(), model_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"模型禁用成功: id={model_id}")
        return True
    except Exception as e:
        logger.error(f"禁用模型失败: {e}")
        return False


def enable_llm_model(model_id: int) -> bool:
    """
    启用模型（会自动禁用同类型的其他模型）
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取模型信息
        cursor.execute('SELECT type FROM llm_models WHERE id = ?', (model_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        model_type = row[0]
        
        # 禁用同类型的其他模型
        cursor.execute('''
        UPDATE llm_models 
        SET status = 0, updated_at = ?
        WHERE type = ? AND status = 1
        ''', (datetime.now().isoformat(), model_type))
        
        # 启用指定模型
        cursor.execute('''
        UPDATE llm_models 
        SET status = 1, updated_at = ?
        WHERE id = ?
        ''', (datetime.now().isoformat(), model_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"模型启用成功: id={model_id}, type={model_type}")
        return True
    except Exception as e:
        logger.error(f"启用模型失败: {e}")
        return False


if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 测试获取用户配置
    config = get_user_config()
    print(f"用户配置: {config}")
    
    # 测试获取模型配置
    model_config = get_llm_model_config('default')
    print(f"默认模型配置: {model_config}")
