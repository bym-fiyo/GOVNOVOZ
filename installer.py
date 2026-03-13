#!/usr/bin/env python3
"""
GOVNOVOZ v6.4 — Финальная версия
"""

import sys
import re
import os
import shutil
import subprocess
import platform
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import argparse
import random

# ========== КОНФИГУРАЦИЯ ==========
VERSION = "6.4"
GOVNO_EXTENSIONS = ['.govno', '.navoz']

# ========== СООБЩЕНИЯ ==========
ERROR_MESSAGES = {
    'syntax': ["💩 НЕ ПО ПОНЯТИЯМ!", "🤢 ЭТО ГОВНО НЕ КОМПИЛИРУЕТСЯ!"],
    'file_not_found': ["🔍 ГДЕ ГОВНО?", "🌾 НАВОЗ ПОТЕРЯЛСЯ!"],
    'name_error': ["🤔 ЧТО ЗА ГОВНО? Переменная не определена!"],
    'generic': ["💥 ГОВНО УПАЛО!", "🚨 АВАРИЯ!"],
}

SUCCESS_MESSAGES = ["✅ ГОВНО УСПЕШНО ВЫВЕЗЕНО!", "🚛 ГОВНО ДОЕХАЛО!"]
WELCOME_MESSAGES = ["💩 ДОБРО ПОЖАЛОВАТЬ!", "🚛 ГОВНОВОЗ ПРИБЫЛ!"]


class GovnoErrorHandler:
    @staticmethod
    def format_error(error_type: str, error_msg: str, line: int = None, code: str = None) -> str:
        header = random.choice(ERROR_MESSAGES.get(error_type, ERROR_MESSAGES['generic']))
        lines = ["\n" + "=" * 60, f"💩 {header}", "=" * 60]
        if line: lines.append(f"📍 Строка: {line}")
        if code: lines.append(f"📄 Код: {code.strip()}")
        lines.append(f"🔍 Детали: {error_msg}")
        lines.append("=" * 60 + "\n")
        return "\n".join(lines)
    
    @staticmethod
    def success(message: str) -> str:
        return f"\n{random.choice(SUCCESS_MESSAGES)}\n   {message}\n"


class GovnovozCompiler:
    """Компилятор Govnovoz — ФИНАЛЬНАЯ ВЕРСИЯ"""
    
    def __init__(self):
        self.python_code = []
        self.indent_level = 0
        self.line_number = 0
        self.source_file = None
        self.error_handler = GovnoErrorHandler()
        self.variables = set()  # Отслеживаем объявленные переменные
        
        # ========== КОМАНДЫ ==========
        self.commands = {
            # Блоки
            'погнали': 'def main():',
            'закончили': '',
            'замутим': 'def',
            'высрать': 'return',
            
            # Присваивание
            'загрузили': '=',
            
            # Комментарии
            'пометка': '#',
            
            # Условия
            'если': 'if',
            'тогда': 'else:',
            'илиесли': 'elif',
            
            # Циклы
            'крутим': 'while',
            'перебираем': 'for',
            'стоп': 'break',
            'дальше': 'continue',
            
            # Импорты
            'тащим': 'import',
            'оттуда': 'from',
            
            # Логика
            'и': 'and',
            'или': 'or',
            'не_': 'not',
            'в': 'in',
            
            # Сравнения
            'больше': '>',
            'меньше': '<',
            'ровно': '==',
            'не': '!=',
            'не_меньше': '>=',
            'не_больше': '<=',
            
            # Типы
            'слово': 'str',
            'цифра': 'int',
            'дробное': 'float',
            'логика': 'bool',
            'списочек': 'list',
            'словарик': 'dict',
            
            # Математика
            'плюс': '+',
            'минус': '-',
            'умножить': '*',
            'разделить': '/',
            'целочисленно': '//',
            'остаток': '%',
            'степень': '**',
        }
        
        # Алиасы для обратной совместимости
        self.aliases = {
            'говно': 'погнали',
            'говно_конец': 'закончили',
            'говнище': 'замутим',
            'говнецо': 'высрать',
            'говняшка': 'высер',
            'говнись': 'засрать',
            'говно_в_говно': 'загрузили',
            'проебали': 'пометка',
            'если_говно': 'если',
            'иначе_говно': 'тогда',
            'или_говно': 'илиесли',
            'пока_говно': 'крутим',
            'для_говна': 'перебираем',
            'свали_говно': 'стоп',
            'продолжай_говнить': 'дальше',
            'притащи_говно': 'тащим',
            'из_говна': 'оттуда',
            'и_говно': 'и',
            'или_говно_тоже': 'или',
            'не_говно': 'не_',
            'говно_в': 'в',
            'говнее_чем': 'больше',
            'менее_говно': 'меньше',
            'такое_же_говно': 'ровно',
            'не_говно': 'не',
            'говно_текст': 'слово',
            'говно_цифра': 'цифра',
            'говно_плавающее': 'дробное',
            'говно_правда': 'логика',
            'сложи_говно': 'плюс',
            'вычти_говно': 'минус',
            'умножь_говно': 'умножить',
            'подели_говно': 'разделить',
            'остаток_от_говна': 'остаток',
            'степень_говна': 'степень',
        }
    
    def compile(self, source_code: str, source_file: str = None) -> Tuple[bool, str]:
        """Компиляция говна в Python"""
        self.source_file = source_file
        lines = source_code.split('\n')
        self.line_number = 0
        self.variables = set()
        
        try:
            if not source_code.strip():
                return False, self.error_handler.format_error('generic', 'Пустое говно!')
            
            self.python_code = [
                '#!/usr/bin/env python3',
                f'# Скомпилировано с помощью GOVNOVOZ v{VERSION}',
                f'# Файл: {source_file if source_file else "неизвестное говно"}',
                '',
                'import sys',
                'import math',
                '',
            ]
            
            i = 0
            while i < len(lines):
                line = lines[i].rstrip()
                self.line_number = i + 1
                
                if not line:
                    self.python_code.append('')
                    i += 1
                    continue
                
                # Комментарии
                if line.startswith('==') or line.startswith('пометка'):
                    comment = line.lstrip('=пометка ').strip()
                    self.python_code.append(f"{'    ' * self.indent_level}# {comment}")
                    i += 1
                    continue
                
                # Блоки
                if line.strip() == 'погнали':
                    if self.indent_level > 0:
                        return False, self.error_handler.format_error('syntax', 'Нельзя открыть блок внутри блока!', self.line_number, line)
                    self.python_code.append('def main():')
                    self.indent_level = 1
                    i += 1
                    continue
                    
                elif line.strip() == 'закончили':
                    if self.indent_level == 0:
                        return False, self.error_handler.format_error('syntax', 'Закрыли блок, который не открывали!', self.line_number, line)
                    self.indent_level = max(0, self.indent_level - 1)
                    i += 1
                    continue
                
                # Проверка отступов
                if self.indent_level > 0 and not line.startswith(' ' * 4 * (self.indent_level - 1)) and line.strip():
                    return False, self.error_handler.format_error('indent', f'Отступ должен быть {4 * self.indent_level} пробелов!', self.line_number, line)
                
                # Компиляция строки
                try:
                    compiled_line = self.compile_line(line)
                    if compiled_line:
                        self.python_code.append(f"{'    ' * self.indent_level}{compiled_line}")
                except Exception as e:
                    return False, self.error_handler.format_error('syntax', str(e), self.line_number, line)
                
                i += 1
            
            if self.indent_level > 0:
                return False, self.error_handler.format_error('syntax', 'Блок не закрыт!', self.line_number)
            
            if any('def main' in line for line in self.python_code):
                self.python_code.extend(['', 'if __name__ == "__main__":', '    main()'])
            
            return True, '\n'.join(self.python_code)
            
        except Exception as e:
            return False, self.error_handler.format_error('generic', str(e), self.line_number)
    
    def compile_line(self, line: str) -> str:
        """Компиляция строки — ФИНАЛЬНАЯ ВЕРСИЯ"""
        
        # Сохраняем строки в кавычках
        strings = {}
        def save_string(match):
            key = f"__STR{len(strings)}__"
            strings[key] = match.group(0)
            return key
        
        # Проверка кавычек
        quote_count = line.count('"') + line.count("'")
        if quote_count % 2 != 0:
            raise ValueError("Кавычки не закрыты!")
        
        # Временно заменяем строки
        line = re.sub(r'"[^"]*"', save_string, line)
        line = re.sub(r"'[^']*'", save_string, line)
        
        # Ищем объявления переменных (тип имя загрузили значение)
        var_pattern = r'(слово|цифра|дробное|логика)\s+([а-яА-Яa-zA-Z_][а-яА-Яa-zA-Z0-9_]*)\s+загрузили\s+(.+)'
        var_match = re.match(var_pattern, line)
        if var_match:
            var_type = var_match.group(1)
            var_name = var_match.group(2)
            var_value = var_match.group(3)
            self.variables.add(var_name)
            return f"{var_name} = {var_value}"
        
        # Ищем простое присваивание (переменная загрузили значение)
        assign_pattern = r'([а-яА-Яa-zA-Z_][а-яА-Яa-zA-Z0-9_]*)\s+загрузили\s+(.+)'
        assign_match = re.match(assign_pattern, line)
        if assign_match:
            var_name = assign_match.group(1)
            var_value = assign_match.group(2)
            self.variables.add(var_name)
            return f"{var_name} = {var_value}"
        
        # СПЕЦИАЛЬНАЯ ОБРАБОТКА: засрать
        # засрать переменная -> переменная = input()
        input_pattern = r'засрать\s+([а-яА-Яa-zA-Z_][а-яА-Яa-zA-Z0-9_]*)'
        input_match = re.search(input_pattern, line)
        if input_match:
            var_name = input_match.group(1)
            self.variables.add(var_name)
            line = re.sub(input_pattern, f'{var_name} = input()', line)
        
        # высер что-то -> print(что-то)
        line = re.sub(r'высер\s+(.+)', r'print(\1)', line)
        
        # Замена алиасов
        for old, new in self.aliases.items():
            line = line.replace(old, new)
        
        # Замена команд (целые слова)
        for gov_word, py_word in sorted(self.commands.items(), key=lambda x: len(x[0]), reverse=True):
            pattern = r'\b' + re.escape(gov_word) + r'\b'
            line = re.sub(pattern, py_word, line)
        
        # Возвращаем строки
        for key, value in strings.items():
            line = line.replace(key, value)
        
        return line


class GovnovozInterpreter:
    """Интерпретатор для запуска файлов"""
    
    def __init__(self):
        self.compiler = GovnovozCompiler()
        self.error_handler = GovnoErrorHandler()
    
    def run_file(self, filename: str, args: List[str] = None):
        if not os.path.exists(filename):
            print(self.error_handler.format_error('file_not_found', f"Файл {filename} не найден!"))
            return 1
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                source = f.read()
            
            success, result = self.compiler.compile(source, filename)
            
            if not success:
                print(result)
                return 1
            
            exec_globals = {
                '__name__': '__main__',
                '__file__': filename,
                'sys': sys,
                'math': __import__('math'),
            }
            
            if args:
                sys.argv = [filename] + args
            
            exec(result, exec_globals)
            return 0
            
        except Exception as e:
            print(self.error_handler.format_error('generic', str(e)))
            return 1


class GovnovozInstaller:
    """Установщик в систему"""
    
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
        self.govno_home = self.home / ".govnovoz"
        self.bin_dir = self.govno_home / "bin"
        self.lib_dir = self.govno_home / "lib"
        self.templates_dir = self.govno_home / "templates"
    
    def install(self):
        print(f"\n🚛 Установка GOVNOVOZ v{VERSION}\n")
        
        # Создаем структуру
        self.govno_home.mkdir(exist_ok=True)
        self.bin_dir.mkdir(exist_ok=True)
        self.lib_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Копируем компилятор
        lib_file = self.lib_dir / "govnovoz_core.py"
        with open(__file__, 'r', encoding='utf-8') as src:
            with open(lib_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        # Создаем исполняемый файл
        executable = self.bin_dir / "govnovoz"
        with open(executable, 'w') as f:
            f.write("""#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path.home() / '.govnovoz' / 'lib'))
from govnovoz_core import main
if __name__ == '__main__':
    sys.exit(main())
""")
        executable.chmod(0o755)
        
        # Шаблоны
        templates = {
            "hello.govno": '''== Привет мир ==
погнали
    высер "Введите имя:"
    засрать имя
    высер "Привет, " + имя + "!"
закончили''',
            
            "calc.govno": '''== Калькулятор ==
погнали
    высер "Введите число:"
    засрать x
    высер "Квадрат: " + (x * x)
закончили''',
            
            "ifelse.govno": '''== Условия ==
погнали
    высер "Сколько лет?"
    засрать возраст
    если возраст больше 17:
        высер "Взрослый"
    тогда:
        высер "Мелкий"
закончили''',
        }
        
        for name, content in templates.items():
            with open(self.templates_dir / name, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Добавляем в PATH
        self.add_to_path()
        
        print(f"✅ Установлено в {self.govno_home}")
        print("✅ Команда: govnovoz")
        print("✅ Поддерживаются: .govno, .navoz")
        print("\nПримеры в ~/.govnovoz/templates/")
    
    def add_to_path(self):
        shell = os.environ.get('SHELL', '')
        rc_file = None
        
        if 'zsh' in shell:
            rc_file = Path.home() / '.zshrc'
        elif 'bash' in shell:
            rc_file = Path.home() / '.bashrc'
        
        if rc_file and rc_file.exists():
            with open(rc_file, 'a') as f:
                f.write(f'\nexport PATH="$PATH:{self.bin_dir}"\n')
            print(f"✅ Добавлено в {rc_file}")
            print("   Выполните: source " + str(rc_file))
    
    def uninstall(self):
        if self.govno_home.exists():
            import shutil
            shutil.rmtree(self.govno_home)
            print("🗑️ Говно удалено!")


def create_example():
    """Создание примера"""
    example = '''#!/usr/bin/env govnovoz
== Пример программы ==
погнали
    высер "Как тебя зовут?"
    засрать имя
    высер "Привет, " + имя + "!"
    
    высер "Сколько тебе лет?"
    засрать возраст
    если возраст больше 17:
        высер "Ты взрослый!"
    тогда:
        высер "Ты ещё мелкий!"
закончили
'''
    with open("example.govno", "w", encoding='utf-8') as f:
        f.write(example)
    os.chmod("example.govno", 0o755)
    print("✅ Создан example.govno")
    print("   Запусти: govnovoz example.govno")


def main():
    parser = argparse.ArgumentParser(description="GOVNOVOZ — говняный язык программирования")
    parser.add_argument('file', nargs='?', help='.govno или .navoz файл')
    parser.add_argument('--install', action='store_true', help='Установить в систему')
    parser.add_argument('--uninstall', action='store_true', help='Удалить из системы')
    parser.add_argument('--example', action='store_true', help='Создать пример')
    parser.add_argument('--version', '-v', action='version', version=f'Govnovoz {VERSION}')
    
    args = parser.parse_args()
    
    if args.install:
        GovnovozInstaller().install()
    elif args.uninstall:
        GovnovozInstaller().uninstall()
    elif args.example:
        create_example()
    elif args.file:
        sys.exit(GovnovozInterpreter().run_file(args.file))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()