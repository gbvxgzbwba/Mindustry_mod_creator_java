import os
import sys
VERSION = "1.0"
def resource_path(relative_path):
    """Получаем путь к файлу при запуске из .exe и из .py"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def safe_navigation(target_func, *args):
    """Простая навигация без задержки"""
    try:
        if args:
            target_func(*args)
        else:
            target_func()
    except Exception as e:
        print(f"Ошибка навигации: {e}")
    finally:
        import gc
        gc.collect()

def name_exists_in_content(mod_folder, name, new_type):
    """Проверка существования имени в контенте"""
    import os
    from tkinter import messagebox
    
    content_path = os.path.join(mod_folder, "content", "blocks")

    if not os.path.exists(content_path):
        return False

    for block_type in os.listdir(content_path):
        type_folder = os.path.join(content_path, block_type)
        if not os.path.isdir(type_folder):
            continue

        for file_name in os.listdir(type_folder):
            base_name, ext = os.path.splitext(file_name)
            if base_name == name:
                if block_type == new_type:
                    result = messagebox.askquestion(
                        "Предупреждение",
                        f"Блок с именем '{name}' уже существует в типе '{new_type}'.\nВы хотите продолжить и обновить блок?",
                        icon='warning'
                    )
                    if result == "no":
                        return True
                    else:
                        return False
                else:
                    messagebox.showerror(
                        "Ошибка",
                        f"Имя '{name}' уже используется в типе '{block_type}', а вы создаёте '{new_type}'."
                    )
                    return True
    return False