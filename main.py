import tkinter as tk
from tkinter import messagebox
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re
import time
import os
import sys
# --- PHẦN CODE MỚI ---
import subprocess # Import module để chạy tiến trình bên ngoài

# --------------------

# Ensure UTF-8 output on Windows consoles to avoid UnicodeEncodeError
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
    os.system('chcp 65001 >NUL')

# --- Selenium Imports ---
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def get_chapter_data_from_source(page_source, base_url, all_chapters_set):
    """Parses the page source to extract chapter names and URLs."""
    soup = BeautifulSoup(page_source, 'html.parser')
    chapter_list_div = soup.find('div', id='chapters')
    if not chapter_list_div:
        return []

    links = chapter_list_div.find_all('a', href=re.compile(r'/truyen/'))
    
    new_chapters = []
    for link in links:
        chapter_title = link.text.strip()
        chapter_url = urljoin(base_url, link['href'])
        chapter_tuple = (chapter_title, chapter_url)

        if chapter_title and chapter_tuple not in all_chapters_set:
            new_chapters.append({'Chapter_Name': chapter_title, 'URL': chapter_url})
            all_chapters_set.add(chapter_tuple)
    return new_chapters


def scrape_chapters_selenium(story_url):
    """
    Scrapes all chapters by controlling a web browser to click through pages.
    """
    try:
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        driver = uc.Chrome(options=chrome_options, version_main=139)
        
    except Exception as e:
        messagebox.showerror("Driver Error", f"Failed to start Undetected WebDriver.\nError: {e}")
        return False

    driver.get(story_url)

    all_chapters = []
    all_chapters_set = set() 

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "chapters"))
        )

        total_pages = 1
        try:
            goto_button = driver.find_element(By.ID, 'goto-page')
            total_pages = int(goto_button.get_attribute('data-total'))
        except NoSuchElementException:
            print("Could not find 'goto-page' button, assuming single page.")

        initial_chapters = get_chapter_data_from_source(driver.page_source, story_url, all_chapters_set)
        all_chapters.extend(initial_chapters)
        
        for page_num in range(2, total_pages + 1):
            try:
                old_chapter_list = driver.find_element(By.ID, 'chapters')
                input_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "goto-page-number"))
                )
                input_box.clear()
                input_box.send_keys(str(page_num))
                go_button = driver.find_element(By.ID, "goto-page")
                driver.execute_script("arguments[0].click();", go_button)
                time.sleep(2)

                new_chapters = get_chapter_data_from_source(driver.page_source, story_url, all_chapters_set)
                all_chapters.extend(new_chapters)
                
                print(f"Scraped page {page_num}/{total_pages}")

            except TimeoutException:
                messagebox.showwarning("Warning", f"Could not load page {page_num}. Moving on.")
                break
            except Exception as e:
                messagebox.showwarning("Warning", f"An error occurred on page {page_num}: {e}. Moving on.")
                break
    finally:
        driver.quit()

    if not all_chapters:
        messagebox.showinfo("No Chapters Found", "Could not find any chapters for the given URL.")
        return False

    df = pd.DataFrame(all_chapters)
    csv_filename = "truyen_chapters.csv"
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    # messagebox.showinfo("Success", f"Successfully downloaded {len(all_chapters)} chapters. Saved to {csv_filename}")
    return True

def on_submit():
    """Handles the submit button click event."""
    url = url_entry.get()
    if not url.startswith("https://ntruyen.top/truyen/"):
        messagebox.showerror("Invalid URL", "Please enter a valid story URL from ntruyen.top.")
        return
    scrape_chapters_selenium(url)

# --- GUI Setup ---
root = tk.Tk()
root.title("Ntruyen Story Downloader")
root.attributes('-topmost', True)

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()
label = tk.Label(frame, text="Enter ntruyen.top story URL:")
label.pack()
url_entry = tk.Entry(frame, width=80)
url_entry.pack()
# submit_button = tk.Button(frame, text="1. Lấy danh sách chương", command=on_submit)
# submit_button.pack(pady=5)


# --- CÁC HÀM VÀ NÚT MỚI ---

def run_download():
    """Chạy script tai_truyen.py như một tiến trình riêng."""
    if not os.path.exists('truyen_chapters.csv'):
        messagebox.showerror("Lỗi", "File 'truyen_chapters.csv' không tồn tại. Vui lòng lấy danh sách chương trước.")
        return
    
    script_to_run = 'tai_truyen.py'
    
    try:
        subprocess.run([sys.executable, script_to_run], check=True)
    except FileNotFoundError:
        messagebox.showerror("Lỗi File", f"Không tìm thấy script '{script_to_run}'. Vui lòng đảm bảo file này tồn tại trong cùng thư mục.")
    except subprocess.CalledProcessError:
        messagebox.showerror("Lỗi Thực Thi", f"Script '{script_to_run}' đã chạy và gặp lỗi. Vui lòng kiểm tra cửa sổ console để biết chi tiết.")
    except Exception as e:
        messagebox.showerror("Lỗi Không Mong Muốn", f"Đã xảy ra lỗi khi cố gắng chạy script: {e}")


def delete_csv_file():
    """Xóa file truyen_chapters.csv."""
    csv_file = 'truyen_chapters.csv'
    if os.path.exists(csv_file):
        try:
            os.remove(csv_file)
        except OSError as e:
            messagebox.showerror("Lỗi", f"Không thể xóa file: {e}")
    else:
        messagebox.showinfo("Thông tin", f"File '{csv_file}' không tồn tại để xóa.")

def run_full_flow():
    """Chạy toàn bộ quy trình: Lấy list -> Tải truyện -> Xóa list."""
    url = url_entry.get()
    if not url.startswith("https://ntruyen.top/truyen/"):
        messagebox.showerror("URL không hợp lệ", "Vui lòng nhập URL truyện hợp lệ từ ntruyen.top.")
        return
    
    success = scrape_chapters_selenium(url)
    
    if success:
        run_download()
        delete_csv_file()


# Tạo một frame mới cho các nút điều khiển
controls_frame = tk.Frame(root, padx=10, pady=5)
controls_frame.pack()

# Thay 3 nút 1/2/3 bằng một Menubutton (dropdown) nhỏ hình mũi tên xuống
menu_btn = tk.Menubutton(controls_frame, text="▼", relief=tk.RAISED, width=3)
menu = tk.Menu(menu_btn, tearoff=0)
menu.add_command(label="1. Lấy danh sách chương", command=on_submit)
menu.add_command(label="2. Tải truyện từ file CSV", command=run_download)
menu.add_command(label="3. Xóa file CSV", command=delete_csv_file)
menu_btn.config(menu=menu)
menu_btn.grid(row=0, column=0, padx=5, pady=5)

# Xóa các nút riêng lẻ (đã thay bằng dropdown)
# download_button = tk.Button(controls_frame, text="2. Tải truyện từ file CSV", command=run_download)
# download_button.grid(row=0, column=0, padx=5, pady=5)
# delete_button = tk.Button(controls_frame, text="3. Xóa file CSV", command=delete_csv_file)
# delete_button.grid(row=0, column=1, padx=5, pady=5)

# Nút chạy tất cả đổi thành RUN DOWNLOAD
run_all_button = tk.Button(root, text="RUN DOWNLOAD", command=run_full_flow, fg="blue", font=("Helvetica", 10, "bold"))
run_all_button.pack(pady=10, padx=10, fill=tk.X)

root.mainloop()