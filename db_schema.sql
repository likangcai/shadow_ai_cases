-- SQLite数据库表结构设计

-- 用户配置表
CREATE TABLE IF NOT EXISTS user_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enable_review BOOLEAN DEFAULT 1,  -- 是否启用专家评审，默认启用
    test_case_count INTEGER DEFAULT NULL,  -- 测试用例数量，NULL表示不限制
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 模型配置表
CREATE TABLE IF NOT EXISTS llm_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,  -- 模型类型：default（默认生成）或review（评审）
    provider TEXT NOT NULL,  -- 模型提供商
    api_key TEXT NOT NULL,  -- API密钥
    base_url TEXT NOT NULL,  -- API基础URL
    model TEXT NOT NULL,  -- 模型名称
    status BOOLEAN DEFAULT 0,  -- 状态：0=禁用，1=启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(type, provider, model)  -- 确保同一类型、提供商和模型的配置唯一
);

-- 创建索引，提高查询性能
CREATE INDEX IF NOT EXISTS idx_llm_models_type_status ON llm_models(type, status);

-- 初始化默认用户配置
INSERT OR IGNORE INTO user_configs (enable_review, test_case_count) VALUES (1, NULL);

-- 初始化默认模型配置（从config.yaml中获取）
INSERT OR IGNORE INTO llm_models (type, provider, api_key, base_url, model, status) 
VALUES ('default', 'DeepSeek', 'ak_1u725L5sG', 'https://api.模型地址.chat/openai', '模型名称', 1);

-- 初始化评审模型配置（默认与默认模型相同）
INSERT OR IGNORE INTO llm_models (type, provider, api_key, base_url, model, status) 
VALUES ('review', 'DeepSeek', 'ak_1u725', 'https://api.模型地址.chat/openai', '模型名称', 1);
