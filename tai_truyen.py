import os
import pandas as pd
import re
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from tkinter import messagebox
import tkinter as tk  # <--- THÊM DÒNG NÀY
import sys

# Đảm bảo output UTF-8 trên Windows
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
    os.system('chcp 65001 >NUL')

# --- CÁC THAM SỐ CẤU HÌNH ---
MAX_CONCURRENT_DOWNLOADS = 20
MAX_RETRIES = 3
RETRY_DELAY = 2

# Hàm để làm sạch tên file
def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

# Hàm bất đồng bộ để tải và lưu một chương
async def download_chapter(session, semaphore, index, chapter_name, url, story_folder):
    """Tải một chương, với cơ chế giới hạn đồng thời và tự động thử lại."""
    file_name = f"{index:06d}-{clean_filename(chapter_name)}.html"
    file_path = os.path.join(story_folder, file_name)
    
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                            await f.write(soup.prettify())
                        print(f"[Thành công] Đã lưu chương {index}: {file_name}")
                        return True
                    else:
                        print(f"[Lỗi Status] Chương {index} (lần {attempt+1}/{MAX_RETRIES}) thất bại với mã: {response.status}")
                
            except Exception as e:
                print(f"[Lỗi Kết nối] Chương {index} (lần {attempt+1}/{MAX_RETRIES}): {type(e).__name__}")

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)

    print(f"[Bỏ qua] Không thể tải chương {index} sau {MAX_RETRIES} lần thử: {url}")
    return False

# Hàm chính để điều phối toàn bộ quá trình
async def main_download():
    csv_file = 'truyen_chapters.csv'
    
    try:
        df = pd.read_csv(csv_file, header=0)
    except FileNotFoundError:
        messagebox.showerror("Lỗi", f"Không tìm thấy file '{csv_file}' để bắt đầu tải.")
        return

    if df.empty or 'URL' not in df.columns or pd.isna(df['URL'].iloc[0]):
        messagebox.showerror("Lỗi", "File CSV trống hoặc cột URL không hợp lệ.")
        return

    first_url = df['URL'].iloc[0]
    match = re.search(r'/truyen/([^/]+)/', first_url)
    story_name = match.group(1) if match else 'downloaded_chapters'

    base_dir = 'truyen'
    story_folder = os.path.join(base_dir, story_name)

    if not os.path.exists(story_folder):
        os.makedirs(story_folder)
        print(f"Đã tạo thư mục: {story_folder}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
    
    tasks = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for index, row in enumerate(df.itertuples(index=False), start=1):
            task = download_chapter(session, semaphore, index, row.Chapter_Name, row.URL, story_folder)
            tasks.append(task)
        
        total_chapters = len(tasks)
        print(f"Bắt đầu tải {total_chapters} chương với tối đa {MAX_CONCURRENT_DOWNLOADS} luồng đồng thời...")
        
        results = await asyncio.gather(*tasks)
    
    success_count = sum(results)
    fail_count = len(results) - success_count
    
    summary_message = (
        f"Hoàn tất quá trình tải.\n\n"
        f"Thư mục: '{story_folder}'\n"
        f"Thành công: {success_count}\n"
        f"Thất bại/Bỏ qua: {fail_count}"
    )
    print("\n" + summary_message)
    messagebox.showinfo("Hoàn tất", summary_message)

# Chạy hàm main bất đồng bộ
if __name__ == "__main__":
    # Tạo một cửa sổ tkinter gốc và ẩn nó đi
    # để đảm bảo messagebox hiển thị đúng cách
    root = tk.Tk()  # <--- SỬA LẠI DÒNG NÀY
    root.withdraw()
    try:
        asyncio.run(main_download())
    finally:
        # Hủy cửa sổ gốc sau khi messagebox được đóng
        root.destroy()