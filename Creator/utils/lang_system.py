import json
import os
import sys
import locale
import eel
from pathlib import Path

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу (работает и в .py, и в .exe)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_system_language():
    try:
        system_locale, encoding = locale.getdefaultlocale()
        if system_locale:
            language_code = system_locale.split('_')[0]
            return language_code
        return None
    except Exception as e:
        print(f"Ошибка при получении языка системы: {e}")
        return None

class LangSystem:
    def __init__(self):
        self.current_lang = "ru"
        self.translations = {}
        self.available_languages = []
        self.available_languages_display = {}
        
        # Определяем пути для поиска языковых файлов
        self.lang_search_paths = []
        
        # 1. Путь в AppData (пользовательские языки)
        appdata = os.getenv('APPDATA') or os.path.expanduser("~")
        appdata_langs = Path(appdata) / "MindustryModCreator" / "langs"
        if appdata_langs.exists():
            self.lang_search_paths.append(str(appdata_langs))
            print(f"Поиск языков в AppData: {appdata_langs}")
        
        # 2. Путь во встроенных ресурсах (для EXE)
        try:
            builtin_path = resource_path("Creator/langs")
            if os.path.exists(builtin_path):
                self.lang_search_paths.append(builtin_path)
                print(f"Поиск языков в ресурсах: {builtin_path}")
        except Exception as e:
            print(f"Ошибка доступа к ресурсам: {e}")
        
        # 3. Путь в рабочей директории (для разработки)
        dev_path = os.path.join(os.path.dirname(__file__), "..", "langs")
        if os.path.exists(dev_path):
            self.lang_search_paths.append(os.path.abspath(dev_path))
            print(f"Поиск языков в dev: {os.path.abspath(dev_path)}")
        
        # 4. Путь в папке с программой
        if getattr(sys, 'frozen', False):
            program_path = os.path.join(os.path.dirname(sys.executable), "Creator", "langs")
            if os.path.exists(program_path):
                self.lang_search_paths.append(program_path)
                print(f"Поиск языков в программе: {program_path}")
        
        # Сканируем доступные языки
        self.scan_available_languages()
        
        # Загружаем язык из настроек, если есть
        self.load_language_from_settings()
        
        # Если не загрузили из настроек, пробуем системный
        if not self.translations:
            self.load_system_language()
        
        # Если всё ещё нет, загружаем первый доступный
        if not self.translations and self.available_languages:
            self.current_lang = self.available_languages[0]
            self.load_language()
            print(f"Установлен первый доступный язык: {self.current_lang}")
    
    def load_language_from_settings(self):
        """Загружает язык из файла настроек"""
        try:
            appdata = os.getenv('APPDATA') or os.path.expanduser("~")
            settings_file = Path(appdata) / "MindustryModCreator" / "settings.json"
            
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    saved_lang = settings.get("language", "ru")
                    
                    if saved_lang in self.available_languages:
                        self.current_lang = saved_lang
                        self.load_language()
                        print(f"Загружен язык из настроек: {saved_lang}")
                        return True
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
        return False
    
    def load_system_language(self):
        """Загружает системный язык"""
        system_lang = get_system_language()
        if system_lang and system_lang in self.available_languages:
            self.current_lang = system_lang
            self.load_language()
            print(f"Установлен системный язык: {system_lang}")
            return True
        return False
    
    def get_lang_display_name(self, lang_code, search_path=None):
        """Возвращает отображаемое имя языка из файла"""
        paths_to_check = []
        if search_path:
            paths_to_check.append(search_path)
        paths_to_check.extend(self.lang_search_paths)
        
        for path in paths_to_check:
            lang_file = os.path.join(path, f"{lang_code}.json")
            if os.path.exists(lang_file):
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if "__language_name__" in data:
                            return data["__language_name__"]
                        elif "language_name" in data:
                            return data["language_name"]
                except:
                    pass
        return lang_code
    
    def scan_available_languages(self):
        """Сканирует все JSON файлы в папках langs"""
        self.available_languages = []
        self.available_languages_display = {}
        found_files = set()
        
        for search_path in self.lang_search_paths:
            if os.path.exists(search_path):
                try:
                    print(f"Сканируем: {search_path}")
                    for file in os.listdir(search_path):
                        if file.endswith('.json'):
                            lang_code = file[:-5]
                            if lang_code not in found_files:
                                found_files.add(lang_code)
                                self.available_languages.append(lang_code)
                                display_name = self.get_lang_display_name(lang_code, search_path)
                                self.available_languages_display[lang_code] = display_name
                                print(f"  Найден язык: {lang_code} -> {display_name}")
                except Exception as e:
                    print(f"Ошибка сканирования {search_path}: {e}")
        
        self.available_languages.sort()
        print(f"Всего найдено языков: {len(self.available_languages)}")
        
        if not self.available_languages:
            print("⚠️ Языковые файлы не найдены! Создайте JSON файлы в папке Creator/langs/")
    
    def get_lang_path(self, lang_code=None):
        """Ищет файл языка во всех возможных путях"""
        if lang_code is None:
            lang_code = self.current_lang
        
        for search_path in self.lang_search_paths:
            lang_file = os.path.join(search_path, f"{lang_code}.json")
            if os.path.exists(lang_file):
                return lang_file
        return None
    
    def load_language(self, lang_code=None):
        """Загружает языковой файл"""
        if lang_code:
            self.current_lang = lang_code
        
        lang_file = self.get_lang_path()
        
        if not lang_file:
            print(f"⚠️ Языковой файл не найден для {self.current_lang}")
            print(f"   Поиск в: {self.lang_search_paths}")
            self.translations = {}
            return False
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            print(f"✅ Загружен языковой файл: {lang_file}")
            print(f"   Содержит переводов: {len(self.translations)}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON в {lang_file}: {e}")
            self.translations = {}
        except Exception as e:
            print(f"❌ Ошибка загрузки {lang_file}: {e}")
            self.translations = {}
        return False
    
    def translate(self, text):
        """Простой перевод текста"""
        if not isinstance(text, str):
            return str(text)
        
        # Пробуем найти перевод
        result = self.translations.get(text, text)
        return result
    
    def translate_batch(self, keys):
        """Перевод нескольких ключей сразу для HTML"""
        result = {}
        for key in keys:
            if key is None:
                result["null"] = None
            else:
                result[key] = self.translations.get(key, key)
        return result
    
    def get_available_languages(self):
        return self.available_languages
    
    def get_available_languages_display(self):
        return [self.available_languages_display.get(lang, lang) for lang in self.available_languages]
    
    def get_language_display_name(self, lang_code):
        return self.available_languages_display.get(lang_code, lang_code)
    
    def set_language(self, lang_code):
        if lang_code in self.available_languages:
            self.current_lang = lang_code
            self.load_language()
            return True
        return False
    
    def get_current_language(self):
        return self.current_lang


# Создаем глобальный экземпляр
lang_system = LangSystem()


def LangT(text):
    """Простая функция перевода для Python кода"""
    return lang_system.translate(text)


# ============= ФУНКЦИИ ДЛЯ ВНЕШНЕГО ИСПОЛЬЗОВАНИЯ =============

def set_language(lang_code):
    return lang_system.set_language(lang_code)

def get_current_language():
    return lang_system.get_current_language()

def get_available_languages():
    return lang_system.get_available_languages()

def get_available_languages_display():
    return lang_system.get_available_languages_display()

def get_language_display_name(lang_code):
    return lang_system.get_language_display_name(lang_code)


# ============= EEL ФУНКЦИИ ДЛЯ ВЕБ-ИНТЕРФЕЙСА =============

@eel.expose
def request_translations(keys):
    """HTML отправляет список ключей, получает переводы"""
    return lang_system.translate_batch(keys)

@eel.expose
def get_current_lang_info():
    """Возвращает информацию о текущем языке для HTML"""
    return {
        "code": lang_system.get_current_language(),
        "name": lang_system.get_language_display_name(lang_system.get_current_language()),
        "available": lang_system.get_available_languages(),
        "available_names": lang_system.get_available_languages_display()
    }

@eel.expose
def switch_language(lang_code, keys):
    """Смена языка и получение переводов для указанных ключей"""
    success = lang_system.set_language(lang_code)
    if success:
        return {
            "success": True,
            "current_lang": lang_system.get_current_language(),
            "translations": lang_system.translate_batch(keys)
        }
    return {"success": False, "error": "Language not available"}