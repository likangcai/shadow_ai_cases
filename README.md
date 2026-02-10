# AI 测试用例生成器

## 项目简介

AI 测试用例生成器是一个基于大语言模型的测试用例自动生成工具，支持通过上传文件或手动输入需求来快速生成高质量的测试用例，并提供测试用例评审功能，帮助测试人员提高工作效率。

## 功能特性

- **多种需求输入方式**：支持上传文件（支持多种格式）或手动输入需求文本
- **智能测试用例生成**：基于大语言模型自动生成符合要求的测试用例
- **测试用例评审**：支持通过评审模型对生成的测试用例进行评审和优化
- **多种导出格式**：支持导出为 JSON、Excel、CSV、Markdown 等多种格式
- **响应式设计**：适配不同屏幕尺寸，提供良好的用户体验
- **分页展示**：支持分页查看生成的测试用例
- **自定义提示词**：支持自定义生成提示词和评审提示词
- **可配置测试用例数量**：支持指定生成的测试用例数量

## 技术栈

- **后端**：Python 3.x, Flask
- **前端**：HTML, CSS, JavaScript, LayUI
- **大语言模型**：OpenAI API
- **数据处理**：Pandas, OpenPyXL
- **文件处理**：Pillow, PyMuPDF, python-docx
- **数据库**：SQLite
- **日志**：Loguru

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://gitee.com/yingzi_shadow/shadow_ai_cases.git
cd Shadow_AI_Cases

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
env\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

编辑 `config.yaml` 文件，配置大语言模型相关信息：

```yaml
# 生成模型配置
llm_default:
  provider: openai  # 模型提供商
  model: gpt-4o-mini  # 模型名称
  api_key: your_api_key  # API密钥
  base_url: https://api.openai.com/v1  # API基础URL

# 评审模型配置，建议评审模型和生成模型不同，可以是同一个厂商的不同模型，也可以是不同厂商的不同模型
llm_review:
  provider: openai
  model: gpt-4o-mini
  api_key: your_api_key
  base_url: https://api.openai.com/v1
```

### 3. 启动服务

```bash
# 启动开发服务器
python app.py

# 或使用其他端口
python app.py --port 5001
```

服务启动后，访问 `http://localhost:5001` 即可使用。

## 配置说明

### 模型配置

项目支持两种方式配置模型：

1. **配置文件**：通过 `config.yaml` 文件配置（见上文）
2. **数据库配置**：首次使用时会自动创建数据库，可在后续使用中通过界面配置

### 环境变量

| 环境变量 | 说明 | 默认值 |
|---------|------|-------|
| FLASK_APP | Flask应用入口 | app.py |
| FLASK_ENV | 运行环境 | development |
| PORT | 服务端口 | 5001 |

## 使用方法

### 1. 生成测试用例

1. **输入需求**：
   - 方式一：点击「选择文件」按钮上传需求文档
   - 方式二：在「手动输入需求」文本框中直接输入需求

2. **配置选项**：
   - **导出格式**：选择生成的测试用例导出格式（JSON、Excel、CSV、Markdown）
   - **测试用例数量**：指定要生成的测试用例数量
   - **启用评审**：选择是否启用测试用例评审功能
   - **生成提示词**：点击「设置生成提示词」按钮自定义生成提示词
   - **评审提示词**：点击「设置评审提示词」按钮自定义评审提示词

3. **生成用例**：点击「生成测试用例」按钮开始生成

4. **查看结果**：生成完成后，页面会显示生成的测试用例，可通过分页查看更多

5. **下载结果**：点击页面底部的下载链接下载生成的测试用例

### 2. 手动输入需求

如果您不想上传文件，可以直接在「手动输入需求」文本框中输入需求内容，然后点击「生成测试用例」按钮即可。

### 3. 测试用例评审

1. **启用评审**：在配置选项中开启「启用评审」开关
2. **生成用例**：点击「生成测试用例」按钮
3. **查看评审结果**：系统会先生成测试用例，然后通过评审模型对其进行评审和优化，最终显示评审后的测试用例

## 项目结构

```
Shadow_AI_Cases/
├── app.py              # 主应用文件
├── config.yaml         # 配置文件
├── requirements.txt    # 依赖文件
├── core/               # 核心功能模块
│   ├── database.py     # 数据库操作
│   ├── exporter.py     # 导出功能
│   ├── llm_client.py   # 大语言模型客户端
│   ├── loader.py       # 文件加载器
│   ├── logs.py         # 日志配置
│   └── paths.py        # 路径管理
├── static/             # 静态文件
│   ├── layui/          # LayUI框架
│   ├── result/         # 导出结果
│   └── upload/         # 上传文件
├── templates/          # 模板文件
│   └── index.html      # 首页模板
└── logs/               # 日志文件
```

## API 文档

### 1. 生成测试用例

**请求**：
- URL: `/api/generate`
- Method: POST
- Content-Type: multipart/form-data

**参数**：
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| file | file | 否 | 需求文件 |
| demand_text | string | 否 | 手动输入的需求文本 |
| prompt | string | 否 | 自定义生成提示词 |
| format | string | 否 | 导出格式（json/xls/xlsx/csv/md） |
| enable_review | string | 否 | 是否启用评审（on/off） |
| review_prompt | string | 否 | 自定义评审提示词 |
| test_case_count | integer | 否 | 测试用例数量 |

**响应**：
```json
{
  "code": 0,
  "task_id": "uuid",
  "url": "/static/result/uuid.json",
  "count": 10,
  "data": [
    {
      "用例编号": "TC001",
      "用例标题": "测试标题",
      "前置条件": "前置条件",
      "操作步骤": ["步骤1", "步骤2"],
      "预期结果": "预期结果",
      "优先级": "高"
    }
  ]
}
```

### 2. 分页获取测试用例

**请求**：
- URL: `/api/page/<task_id>`
- Method: GET

**参数**：
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| task_id | string | 是 | 任务ID |
| page | integer | 否 | 页码 |
| limit | integer | 否 | 每页数量 |

**响应**：
```json
{
  "code": 0,
  "count": 10,
  "data": [
    {
      "用例编号": "TC001",
      "用例标题": "测试标题",
      "前置条件": "前置条件",
      "操作步骤": ["步骤1", "步骤2"],
      "预期结果": "预期结果",
      "优先级": "高"
    }
  ]
}
```

### 3. 检查评审模型配置

**请求**：
- URL: `/api/check_review_config`
- Method: GET

**响应**：
```json
{
  "code": 0,
  "configured": true,
  "provider": "openai",
  "model": "gpt-4o-mini"
}
```

## 常见问题

### 1. 生成测试用例失败

- 检查网络连接是否正常
- 检查 API 密钥是否正确
- 检查模型配置是否正确
- 查看日志文件获取详细错误信息

### 2. 评审功能不可用

- 检查评审模型是否已配置
- 检查评审模型的 API 密钥是否正确
- 查看日志文件获取详细错误信息

### 3. 导出文件格式异常

- 对于 Excel 和 CSV 格式，双击单元格可查看完整内容
- 对于 Markdown 格式，使用支持 HTML 的 Markdown 查看器

### 4. 页面显示异常

- 刷新页面尝试
- 清除浏览器缓存
- 检查浏览器控制台是否有错误信息

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 联系方式
如有问题或建议，欢迎通过 Issue 反馈。

- 作者：影子
- 邮箱：<yingzilkq@163.com>
- 仓库地址：https://gitee.com/yingzi_shadow/shadow_ai_cases
- 微信公众号：前行的影子
---

**感谢使用 AI 测试用例生成器！** 🚀
