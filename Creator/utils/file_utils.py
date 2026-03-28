import os
import shutil
import urllib.request
from PIL import Image
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
VERSION = "1.0"
def safe_download_texture(url, path, max_retries=3):
    """Безопасная загрузка текстуры с повторными попытками"""
    import time
    for attempt in range(max_retries):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            temp_path = path + ".tmp"
            urllib.request.urlretrieve(url, temp_path)
            
            if os.path.exists(path):
                os.remove(path)
            shutil.move(temp_path, path)
            
            print(f"Текстура {os.path.basename(path)} загружена")
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки (попытка {attempt + 1}): {e}")
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
                
            if attempt == max_retries - 1:
                return False
            time.sleep(1)
    return False

def download_files_parallel(download_tasks, progress_callback=None):
    """Параллельная загрузка файлов"""
    def download_file(task):
        url, path, name = task
        try:
            urllib.request.urlretrieve(url, path)
            return True, name
        except Exception as e:
            return False, (name, str(e))
    
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(download_file, task): task for task in download_tasks}
        
        for i, future in enumerate(as_completed(futures)):
            success, result = future.result()
            results.append((success, result))
            if progress_callback:
                progress_callback(i + 1, len(download_tasks), result[0] if success else result[0])
    
    return results

def create_directories(*paths):
    """Создание нескольких директорий"""
    for path in paths:
        os.makedirs(path, exist_ok=True)