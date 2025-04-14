from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import base64
from io import BytesIO
import os
import uuid
from generator import generate_info_cards  # 你原来的生成函数

app = FastAPI()

# 允许跨域，确保 Dify 可以访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to the API. Use /process_base64 to submit base64 Excel."}

@app.post("/process_base64")
async def process_excel_base64(file_base64: str = Body(...)):
    # 创建临时目录
    temp_id = str(uuid.uuid4())
    temp_input_path = f"/tmp/{temp_id}.xlsx"
    output_dir = f"/tmp/{temp_id}_out"
    os.makedirs(output_dir, exist_ok=True)

    # 将 base64 保存为文件
    with open(temp_input_path, "wb") as f:
        f.write(base64.b64decode(file_base64))

    # 调用你原来的图片生成函数
    result_files = generate_info_cards(temp_input_path, output_dir)

    # 假设你返回的 result_files 是文件路径列表，转为下载链接（你可以加 CDN 或改成别的格式）
    result_urls = [f"https://info-card-generator.onrender.com/files/{os.path.basename(f)}" for f in result_files]

    return {
        "success": True,
        "result_urls": result_urls,
        "count": len(result_urls)
    }

# 静态文件访问接口（用于暴露图片）
from fastapi.staticfiles import StaticFiles
app.mount("/files", StaticFiles(directory="/tmp", html=True), name="files")
