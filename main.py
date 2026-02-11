# -*- coding: utf-8 -*-
# -----------------------------
# @Author    : 影子
# @Time      : 2025/8/6 09:04
# @Software  : PyCharm
# @FileName  : main.py
# -----------------------------
import os
import uuid
import json
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(
    title="AI 测试用例生成器",
    description="基于FastAPI的测试用例自动生成工具",
    version="1.0.1"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="templates")

llm = LLMClient()
review_llm = LLMClient(model_type="review")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    首页
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/generate")
async def generate(
        request: Request,
        prompt: str = Form(default=""),
        format: str = Form(default="json"),
        enable_review: str = Form(default=None),
        review_prompt: str = Form(default=""),
        test_case_count: str = Form(default=""),
        demand_text: str = Form(default=""),
        file: UploadFile = File(default=None)
):
    """
    生成用例
    """
    try:
        out_fmt = format
        enable_review = enable_review == "on"
        test_case_count = int(test_case_count) if test_case_count else None

        # 只有当没有手动输入需求时，才检查文件
        if not demand_text:
            if not file:
                return JSONResponse({"code": 1, "msg": "未上传文件，请先上传！"})
        else:
            # 有手动输入需求时，文件可选
            pass

        # 保存用户配置到数据库
        update_user_config(enable_review, test_case_count)

        # 校验评审功能配置
        if enable_review:
            review_model_config = get_llm_model_config("review")
            if not review_model_config:
                logger.warning("未配置评审模型，跳过评审环节。")
                enable_review = False

        if demand_text:
            # 使用手动输入的需求
            req_text = demand_text
            logger.debug(f"手动输入的需求: {demand_text}")
        else:
            # 保存上传文件
            suffix = os.path.splitext(file.filename)[1].lower()
            tmp_name = uuid.uuid4().hex + suffix
            tmp_path = os.path.join(UPLOAD_DIR, tmp_name)
            logger.debug(f"上传文件保存路径: {tmp_path}")

            # 保存文件内容
            with open(tmp_path, "wb") as buffer:
                buffer.write(await file.read())

            # 解析需求
            req_text = load_text(tmp_path)
            print(f"需求文本:", {req_text})

        # 记录需求字符数
        logger.info(f"需求字符数: {len(req_text)}")

        # 调用大模型生成用例
        cases = await llm.generate_cases(req_text, prompt, test_case_count)
        logger.info(f"生成用例完成，共 {len(cases)} 个测试用例")
        
        # 记录生成用例字符数
        cases_json = json.dumps(cases, ensure_ascii=False)
        logger.info(f"生成用例字符数: {len(cases_json)}")

        # 根据用户选择是否启用评审
        if enable_review:
            logger.info("启用评审功能，开始评审测试用例")
            # 调用评审专家评审用例，传递用户设置的用例数量
            reviewed_cases = await review_llm.review_cases(req_text, cases, review_prompt, test_case_count)
            logger.info(f"评审完成，生成 {len(reviewed_cases)} 个评审通过的测试用例")
            
            # 记录评审用例字符数
            reviewed_cases_json = json.dumps(reviewed_cases, ensure_ascii=False)
            logger.info(f"评审用例字符数: {len(reviewed_cases_json)}")
            
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
        return JSONResponse({
            "code": 0,
            "task_id": task_id,
            "url": f"/static/result/{task_id}.{out_fmt}",
            "count": len(final_cases),
            "data": first_page
        })

    except Exception as e:
        logger.error(e)
        return JSONResponse({"code": 2, "msg": str(e)})


@app.get("/api/check_review_config")
async def check_review_config():
    """
    检查评审模型配置状态
    """
    review_model_config = get_llm_model_config("review")
    if review_model_config:
        return JSONResponse({
            "code": 0,
            "configured": True,
            "provider": review_model_config.get("provider", ""),
            "model": review_model_config.get("model", "")
        })
    else:
        return JSONResponse({
            "code": 1,
            "configured": False,
            "msg": "检测到未配置评审模型，请先配置相关信息。"
        })


@app.get("/api/page/{task_id}")
async def page(task_id: str, page: int = 1, limit: int = 10):
    """
    分页获取用例
    """
    all_cases = PAGE_CACHE.get(task_id, [])
    start = (page - 1) * limit
    end = start + limit
    return JSONResponse({
        "code": 0,
        "count": len(all_cases),
        "data": all_cases[start:end]
    })


@app.get("/static/result/{filename}")
async def download(filename: str):
    """
    下载导出文件
    """
    file_path = os.path.join(RESULT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        return JSONResponse({"code": 1, "msg": "文件不存在"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main.py:app", host="0.0.0.0", port=5001, reload=True)