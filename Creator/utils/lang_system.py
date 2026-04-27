#p/Creator/utils/lang_system.py
import json
import os
import locale
import re

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

lang = get_system_language()
print(f"Код языка системы: {lang}")

if lang == 'ru':
    print("Системный язык: Русский")
    LANGUAGE = "ru"
elif lang == 'en':
    print("System language: English")
    LANGUAGE = "en"
else:
    print(f"Другой язык: {lang}")
    LANGUAGE = "en"

class LangSystem:
    def __init__(self):
        self.current_lang = LANGUAGE
        self.translations = {}
        self.lang_dir = "Creator/langs"
        self.load_language()
    
    def get_lang_path(self):
        return os.path.join(self.lang_dir, f"{self.current_lang}.json")
    
    def load_language(self):
        """Загружает языковой файл из папки langs"""
        lang_file = self.get_lang_path()
        
        if not os.path.exists(self.lang_dir):
            os.makedirs(self.lang_dir)
        
        if not os.path.exists(lang_file):
            print(f"⚠️ Языковой файл не найден: {lang_file}")
            print(f"   Создайте файл {lang_file} с переводами")
            self.translations = {}
            return
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON в {lang_file}: {e}")
            self.translations = {}
    
    def translate(self, text):
        """
        Переводит текст.
        Поддерживает:
        1. Прямые ключи: LangT("Ошибка")
        2. f-строки с переменными: LangT(f"Файл {name} создан")
        """
        if not isinstance(text, str):
            return str(text)
        
        # Пробуем найти точное совпадение в словаре
        if text in self.translations:
            return self.translations[text]
        
        # Если не нашли, пробуем найти шаблон с плейсхолдерами
        # Например: "Файл {name} создан" ищет "Файл {} создан"
        for key, value in self.translations.items():
            if '{}' in key or '{' in key:
                # Конвертируем оба в regex паттерн
                pattern = key.replace('{', '\\{').replace('}', '([^}]+)')
                match = re.match(pattern, text)
                if match:
                    # Вставляем захваченные значения в перевод
                    result = value
                    for i, captured in enumerate(match.groups(), 1):
                        result = result.replace(f'{{{i}}}', captured)
                    return result
        
        # Если ничего не нашли, возвращаем оригинал
        return text
    
    def T(self, text):
        """Короткий алиас для translate"""
        return self.translate(text)

# Создаем глобальный экземпляр
lang_system = LangSystem()

# Функция для удобного использования
def LangT(text):
    return lang_system.translate(text)

# Функция для смены языка
def set_language(lang_code):
    lang_system.current_lang = lang_code
    lang_system.load_language()

# Функция для получения текущего языка
def get_current_language():
    return lang_system.current_lang