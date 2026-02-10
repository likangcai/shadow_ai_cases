# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2025/8/5 12:00
# @Software  : PyCharm
# @FileName  : llm_client.py
# -----------------------------
import json
from typing import List, Dict, Optional

import openai
import yaml

from core.logs import logger
from core.paths import get_file_path
from core.database import get_llm_model_config


def clean_markdown_json(content: str) -> str:
    """
    输入：
    - content: Markdown 格式的 JSON 字符串
    输出：
    - 清除 Markdown 格式的 JSON 字符串
    """

    if content.startswith('```'):  # 去除开头的 ``` 或 ```json 等标记（可能包含语言类型）
        # 匹配开头的 ```[语言类型]（如 ```json）
        end_of_start = content.find('\n', 3)  # 找到第一个换行符的位置（``` 后可能有语言类型）
        if end_of_start != -1:
            content = content[end_of_start:].lstrip()  # 保留换行后的内容

    # 去除结尾的 ```
    if content.endswith('```'):
        content = content[:-3].rstrip()  # 去掉最后的三个反引号，并去除尾部空白
    return content


class LLMClient:
    """
    LLM 客户端
    """

    def __init__(self, model_type: str = "default", cfg_path=get_file_path("config.yaml")):
        """
        初始化LLM客户端
        :param model_type: 模型类型：default（默认生成）或review（评审）
        :param cfg_path: 配置文件路径
        """
        # 先尝试从数据库读取配置
        db_config = get_llm_model_config(model_type)

        if db_config:
            # 使用数据库配置
            logger.info(f"使用数据库中的{model_type}模型配置: {db_config['provider']} - {db_config['model']}")
            self.client = openai.OpenAI(api_key=db_config["api_key"], base_url=db_config.get("base_url"))
            self.model = db_config["model"]
            self.cfg_path = cfg_path
            self.model_type = model_type
        else:
            # 使用配置文件作为备份
            logger.info(f"数据库中未找到{model_type}模型配置，使用配置文件")
            with open(cfg_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 根据模型类型选择配置
            config_key = "llm_default" if model_type == "default" else "llm_review"
            if config_key in config:
                cfg = config[config_key]
                logger.info(f"使用配置文件中的{config_key}配置: {cfg['provider']} - {cfg['model']}")
            else:
                # 兼容旧格式
                cfg = config.get("llm", {})
                logger.warning(f"配置文件中未找到{config_key}，使用旧格式llm配置")

            self.client = openai.OpenAI(api_key=cfg["api_key"], base_url=cfg.get("base_url"))
            self.model = cfg["model"]
            self.cfg_path = cfg_path
            self.model_type = model_type

    def generate_cases(self, requirement: str, custom_prompt: str = "", test_case_count: Optional[int] = None) -> List[
        Dict]:
        """
        调用 LLM 生成测试用例
        :param requirement: 测试需求
        :param custom_prompt: 自定义的 LLM 输入提示
        :param test_case_count: 测试用例数量，None表示不限制
        :return:
        """
        with open(get_file_path("config.yaml"), encoding="utf-8") as f:
            config = yaml.safe_load(f)

        prompt = custom_prompt or config["prompt"]["default"]
        prompt = prompt.replace("{requirement_text}", requirement)

        # 添加测试用例数量信息
        if test_case_count:
            prompt = prompt.replace("测试用例数量: 请生成不少于10个测试用例",
                                    f"测试用例数量: 请生成{test_case_count}个测试用例")

        # logger.debug(f"大模型提示词：{prompt}")
        print(f"大模型提示词：{prompt}")

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": requirement}
        ]
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                # response_format={'type': 'json_object'}
            )
            content = resp.choices[0].message.content.strip()
            # logger.debug(f"LLM输出：{content}")
            print(f"LLM输出：{content}")

            # 添加对空内容的检查
            if not content:
                logger.error("LLM 返回空内容，请稍后再试")
                raise RuntimeError("LLM 返回空内容，请稍后再试")
            return json.loads(clean_markdown_json(content))
        except openai.APIConnectionError as e:
            logger.error(e)
            raise RuntimeError(f"LLM 调用失败: 连接错误，请检查网络设置或API地址配置")
        except openai.AuthenticationError as e:
            logger.error(e)
            raise RuntimeError(f"LLM 调用失败: 认证错误，请检查API密钥是否正确")
        except openai.RateLimitError as e:
            logger.error(e)
            raise RuntimeError(f"LLM 调用失败: 请求过于频繁，请稍后再试")
        except openai.APIError as e:
            logger.error(e)
            raise RuntimeError(f"LLM 调用失败: API错误，{e.message}")
        except json.JSONDecodeError as e:
            logger.error(e)
            raise RuntimeError(f"LLM 调用失败: 返回结果不是有效的JSON格式，请稍后再试")
        except Exception as e:
            logger.error(e)
            raise RuntimeError(f"LLM 调用失败: {str(e)}")

    def review_cases(self, requirement: str, cases: List[Dict], custom_review_prompt: str = "") -> List[Dict]:
        """
        调用 LLM 评审测试用例
        :param requirement: 原始测试需求
        :param cases: 生成的测试用例列表
        :param custom_review_prompt: 自定义的评审提示词
        :return: 评审通过并综合整理后的测试用例
        """
        with open(get_file_path("config.yaml"), encoding="utf-8") as f:
            config = yaml.safe_load(f)

        prompt = custom_review_prompt or config["prompt"].get("review", config["prompt"]["default"])

        # 将测试用例转换为字符串
        cases_str = json.dumps(cases, ensure_ascii=False, indent=2)

        # 替换占位符变量
        prompt = prompt.replace("{requirement_text}", requirement)
        prompt = prompt.replace("{test_cases}", cases_str)

        # logger.debug(f"评审专家提示词：{prompt}")
        print(f"评审专家提示词：{prompt}")

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请根据上述提示词评审以下测试用例"}
        ]

        try:
            resp = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.3)
            content = resp.choices[0].message.content.strip()
            print(f"评审专家输出：{content}")

            # 添加对空内容的检查
            if not content:
                logger.error("评审专家返回空内容，请稍后再试")
                raise RuntimeError("评审专家返回空内容，请稍后再试")

            return json.loads(clean_markdown_json(content))
        except openai.APIConnectionError as e:
            logger.error(e)
            raise RuntimeError(f"评审专家调用失败: 连接错误，请检查网络设置或API地址配置")
        except openai.AuthenticationError as e:
            logger.error(e)
            raise RuntimeError(f"评审专家调用失败: 认证错误，请检查API密钥是否正确")
        except openai.RateLimitError as e:
            logger.error(e)
            raise RuntimeError(f"评审专家调用失败: 请求过于频繁，请稍后再试")
        except openai.APIError as e:
            logger.error(e)
            raise RuntimeError(f"评审专家调用失败: API错误，{e.message}")
        except json.JSONDecodeError as e:
            logger.error(e)
            raise RuntimeError(f"评审专家调用失败: 返回结果不是有效的JSON格式，请稍后再试")
        except Exception as e:
            logger.error(e)
            raise RuntimeError(f"评审专家调用失败: {str(e)}")


if __name__ == '__main__':
    tw = '''
    登录功能验证：
    1、用户名长度为8到20个字符，不能包含特殊字符
    2、密码长度为6到8个字符，必须包含大小写字母和数字
    3、系统用户名和密码正确，登录成功，
    4、系统用户名和密码错误，提示账户或密码错误，
    5、超过5次错误，锁定10分钟
    '''

    llm = LLMClient()
    try:
        cases = llm.generate_cases(tw)
        print(cases)
    except Exception as e:
        print(f"错误: {e}")
