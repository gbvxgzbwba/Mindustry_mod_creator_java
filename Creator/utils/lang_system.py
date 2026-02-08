import json
import os
import locale

def get_system_language():
    try:
        # Получаем текущую локаль системы
        system_locale, encoding = locale.getdefaultlocale()
        if system_locale:
            # Извлекаем код языка (первые 2 символа)
            language_code = system_locale.split('_')[0]
            return language_code
        return None
    except Exception as e:
        print(f"Ошибка при получении языка системы: {e}")
        return None

# Использование
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
        self.lang_dir = "mindustry_mod_creator/Creator/langs"  # Папка с языковыми файлами
        self.load_language()
    
    def get_lang_path(self):
        """Возвращает путь к языковому файлу"""
        return os.path.join(self.lang_dir, f"{self.current_lang}.json")
    
    def load_language(self):
        """Загружает языковой файл из папки langs"""
        lang_file = self.get_lang_path()
        
        # Создаем папку langs, если она не существует
        if not os.path.exists(self.lang_dir):
            os.makedirs(self.lang_dir)
        
        if not os.path.exists(lang_file):
            # Создаем файл по умолчанию, если он не существует
            self.create_default_lang_file()
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"{LangT("Ошибка загрузки языкового файла:")} {e}")
            self.translations = {}
    
    def create_default_lang_file(self):
        """Создает файл с переводом по умолчанию в папке langs"""
        default_translations = {
            "error": "Ошибка",
            "success": "Успех"
        }
        
        lang_file = self.get_lang_path()
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(default_translations, f, ensure_ascii=False, indent=4)
    
    def set_language(self, lang_code):
        """Устанавливает язык"""
        self.current_lang = lang_code
        self.load_language()
    
    def translate(self, code):
        """Переводит код в текст"""
        return self.translations.get(code, f"[{code}]")
    
    def T(self, code):
        """Короткий алиас для translate"""
        return self.translate(code)

# Создаем глобальный экземпляр
lang_system = LangSystem()

# Функция для удобного использования
def LangT(code):
    return lang_system.translate(code)

# Функция для смены языка
def set_language(lang_code):
    lang_system.set_language(lang_code)

# Функция для получения текущего языка
def get_current_language():
    return lang_system.current_lang