import json
import os
import sys
import locale
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
        
        # Определяем язык системы
        system_lang = get_system_language()
        
        # Устанавливаем язык (сначала пробуем системный, если доступен)
        if system_lang in self.available_languages:
            self.current_lang = system_lang
            print(f"Установлен системный язык: {system_lang}")
        elif self.available_languages:
            self.current_lang = self.available_languages[0]
            print(f"Установлен первый доступный язык: {self.current_lang}")
        else:
            print("⚠️ Нет доступных языковых файлов!")
        
        self.load_language()
    
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
        """
        Простой перевод текста
        """
        if not isinstance(text, str):
            return str(text)
        
        # Пробуем найти перевод
        result = self.translations.get(text, text)
        
        # Для отладки (раскомментируйте если нужно)
        # if text != result:
        #     print(f"Перевод: '{text}' -> '{result}'")
        
        return result
    
    # Добавляем недостающие методы
    def get_available_languages(self):
        """Возвращает список доступных языков (коды)"""
        return self.available_languages
    
    def get_available_languages_display(self):
        """Возвращает список отображаемых имен языков"""
        return [self.available_languages_display.get(lang, lang) for lang in self.available_languages]
    
    def get_language_display_name(self, lang_code):
        """Возвращает отображаемое имя для кода языка"""
        return self.available_languages_display.get(lang_code, lang_code)
    
    def set_language(self, lang_code):
        """Устанавливает новый язык"""
        if lang_code in self.available_languages:
            self.current_lang = lang_code
            self.load_language()
            return True
        return False
    
    def get_current_language(self):
        """Возвращает текущий язык"""
        return self.current_language  # Исправлено: было self.current_lang, но есть метод
    
    # Исправляем get_current_language
    def get_current_language(self):
        """Возвращает текущий язык"""
        return self.current_lang


# Создаем глобальный экземпляр
lang_system = LangSystem()


def LangT(text):
    """
    Простая функция перевода, возвращает строку
    """
    return lang_system.translate(text)


# Экспортируем все необходимые функции
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