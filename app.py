# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2025/8/5 12:01
# @Software  : PyCharm
# @FileName  : app.py
# -----------------------------
import os
import uuid

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from core.exporter import export
from core.llm_client import LLMClient
from core.loader import load_text
from core.logs import logger
from core.database import init_db, update_user_config, get_llm_model_config

# 全局缓存，生产环境可换成 Redis
PAGE_CACHE = {}  # key = task_id, value = 全部用例列表

UPLOAD_DIR = f"static{os.sep}upload"
RESULT_DIR = f"static{os.sep}result"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# 初始化数据库
init_db()

app = Flask(__name__)
CORS(app)
llm = LLMClient()
review_llm = LLMClient(model_type="review")


@app.after_request
def after_request(response):
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


@app.route("/")
def index():
    """
    首页
    :return:
    """
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    """
    生成用例
    :return: 成功返回用例列表
    """
    try:
        custom_prompt = request.form.get("prompt", "")
        out_fmt = request.form.get("format", "json")
        enable_review = request.form.get("enable_review") == "on"
        custom_review_prompt = request.form.get("review_prompt", "")
        test_case_count = request.form.get("test_case_count", "")
        test_case_count = int(test_case_count) if test_case_count else None
        
        # 检查是否有手动输入的需求
        demand_text = request.form.get('demand_text', '')
        
        # 只有当没有手动输入需求时，才检查文件
        if not demand_text:
            file = request.files.get("file")
            if not file:
                return jsonify({"code": 1, "msg": "未上传文件，请先上传！"})
        else:
            # 有手动输入需求时，文件可选
            file = request.files.get("file")
        
        # 保存用户配置到数据库
        update_user_config(enable_review, test_case_count)
        
        # 校验评审功能配置
        if enable_review:
            review_model_config = get_llm_model_config("review")
            if not review_model_config:
                logger.warning("未配置评审模型，跳过评审环节。")
                enable_review = False

        logger.debug(f"手动输入的需求: {demand_text}")

        if demand_text:
            # 使用手动输入的需求
            req_text = demand_text
            logger.debug("使用手动输入的需求")
        else:
            # 保存上传文件
            suffix = os.path.splitext(file.filename)[1].lower()
            tmp_name = uuid.uuid4().hex + suffix
            tmp_path = os.path.join(UPLOAD_DIR, secure_filename(tmp_name))
            logger.debug(f"上传文件保存路径: {tmp_path}")
            file.save(tmp_path)

            # 解析需求
            req_text = load_text(tmp_path)
            # logger.debug(f"需求文本: {req_text}")
            print(f"需求文本:", {req_text})

        # 调用大模型生成用例
        cases = llm.generate_cases(req_text, custom_prompt, test_case_count)
        logger.info(f"生成用例完成，共 {len(cases)} 个测试用例")
        
        # 根据用户选择是否启用评审
        if enable_review:
            logger.info("启用评审功能，开始评审测试用例")
            # 调用评审专家评审用例
            reviewed_cases = review_llm.review_cases(req_text, cases, custom_review_prompt)
            logger.info(f"评审完成，生成 {len(reviewed_cases)} 个评审通过的测试用例")
            final_cases = reviewed_cases
        else:
            logger.info("未启用评审功能，使用原始生成的测试用例")
            final_cases = cases

        # 缓存全部用例并导出
        task_id = uuid.uuid4().hex
        logger.info(f"生成用例任务ID: {task_id}")
        PAGE_CACHE[task_id] = final_cases  # 缓存最终用例
        out_path = os.path.join(RESULT_DIR, task_id + "." + out_fmt)
        logger.debug(f"导出文件保存路径: {out_path}")
        export(final_cases, out_fmt, out_path)
        # 只返回第一页
        first_page = final_cases[:10]
        return jsonify({
            "code": 0,
            "task_id": task_id,
            "url": f"/static/result/{task_id}.{out_fmt}",
            "count": len(final_cases),
            "data": first_page
        })

    except Exception as e:
        logger.error(e)
        return jsonify({"code": 2, "msg": str(e)})


@app.route("/api/check_review_config")
def check_review_config():
    """
    检查评审模型配置状态
    :return: 评审模型配置状态
    """
    review_model_config = get_llm_model_config("review")
    if review_model_config:
        return jsonify({
            "code": 0,
            "configured": True,
            "provider": review_model_config.get("provider", ""),
            "model": review_model_config.get("model", "")
        })
    else:
        return jsonify({
            "code": 1,
            "configured": False,
            "msg": "检测到未配置评审模型，请先配置相关信息。"
        })


@app.route("/api/page/<task_id>")
def page(task_id):
    """
    分页获取用例
    :param task_id: 根据任务ID获取用例
    :return: 成功返回用例列表
    """
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    all_cases = PAGE_CACHE.get(task_id, [])
    start = (page - 1) * limit
    end = start + limit
    return jsonify({
        "code": 0,
        "count": len(all_cases),
        "data": all_cases[start:end]
    })


@app.route("/static/result/<path:filename>")
def download(filename):
    """
    下载导出文件
    :param filename: 导出的文件名
    :return:
    """
    return send_from_directory(RESULT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
