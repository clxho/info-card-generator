from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import shutil
import os
import zipfile
import uuid
from generator import generate_info_cards

app = FastAPI()

# 根路径，避免 404 错误
@app.get("/")
def read_root():
    return {"message": "Welcome to the API. Use /process to upload files."}

@app.post("/process")
async def process_excel(file: UploadFile = File(...)):
    temp_id = str(uuid.uuid4())
    # 使用系统临时目录
    input_path = f"/tmp/{temp_id}.xlsx"
    output_folder = f"/tmp/{temp_id}_out"
    zip_path = f"/tmp/{temp_id}.zip"

    # 保存上传的文件
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 生成处理后的文件
    result_files = generate_info_cards(input_path, output_folder)

    # 压缩结果文件
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_path in result_files:
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=os.path.basename(file_path))

    return {"download_url": f"/download/{os.path.basename(zip_path)}"}

@app.get("/download/{filename}")
def download_file(filename: str):
    # 使用正确的路径返回文件
    file_path = f"/tmp/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/zip', filename=filename)
    else:
        return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=10000)
