# generator.py
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io import BytesIO
import os
import warnings
import uuid

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

def create_retry_session():
    retry_strategy = Retry(total=3, status_forcelist=[429, 500, 502, 503, 504],
                           allowed_methods=["GET"], backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

def safe_text(text):
    try:
        return str(text).encode('utf-8', 'ignore').decode('utf-8')
    except:
        return str(text)

def generate_info_cards(input_file_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    df = pd.read_excel(input_file_path)

    FONT_PATHS = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    font_path = next((f for f in FONT_PATHS if os.path.exists(f)), None)
    font_title = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
    font_content = ImageFont.truetype(font_path, 24) if font_path else ImageFont.load_default()

    session = create_retry_session()
    output_files = []

    for _, row in df.iterrows():
        try:
            asin = safe_text(row.get("ASIN", str(uuid.uuid4())))
            img_url = row.get('商品主图链接') or row.get('图片URL')
            product_img = None
            if pd.notna(img_url) and str(img_url).startswith('http'):
                r = session.get(img_url, timeout=(10, 30), verify=False)
                r.raise_for_status()
                product_img = Image.open(BytesIO(r.content))
                product_img.thumbnail((600, 600))

            img = Image.new('RGB', (800, 420), color=(250, 250, 250))
            draw = ImageDraw.Draw(img)

            if product_img:
                product_img = product_img.resize((380, int(380 * product_img.height / product_img.width)))
                img.paste(product_img, (20, (420 - product_img.height) // 2))
            else:
                draw.text((100, 200), "No Image", fill="#999999", font=font_title)

            info_lines = []
            fields = [
                ('价格', '价格'),
                ('近30天销量', '近30天销量'),
                ('评分', '评分'),
                ('FBA运费', 'FBA运费'),
                ('上架天数', '上架天数'),
                ('卖家所属地', '卖家所属地'),
                ('配送方式', '配送方式'),
                ('变体数', '变体数'),
                ('小类排名', '小类排名'),
            ]
            for label, key in fields:
                if pd.notna(row.get(key)):
                    info_lines.append(f"{label}: {safe_text(row[key])}")

            text_y = 20
            draw.text((440, text_y), f"产品信息 - {asin}", fill="#333333", font=font_title)
            text_y += 50
            for line in info_lines:
                draw.text((440, text_y), line, fill="#555555", font=font_content)
                text_y += 34

            out_path = os.path.join(output_folder, f"{asin}.png")
            img.save(out_path)
            output_files.append(out_path)
        except Exception as e:
            output_files.append(f"Error: {e}")
    
    return output_files
