#!/usr/bin/env python3
"""
GOVNOVOZ v6.4 — Графический установщик
"Красивое говно с кнопочками"
"""

import sys
import os
import shutil
import subprocess
import platform
from pathlib import Path
import threading

# Проверка наличия PyQt6
try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
except ImportError:
    print("❌ PyQt6 не установлен! Установите: pip install PyQt6")
    print("   или используйте терминальный установщик: python3 installer.py --install")
    sys.exit(1)

# Конфигурация
VERSION = "6.4"
GOVNO_EXTENSIONS = ['.govno', '.navoz']
GOVNO_HOME = Path.home() / ".govnovoz"
BIN_DIR = GOVNO_HOME / "bin"
LIB_DIR = GOVNO_HOME / "lib"
TEMPLATES_DIR = GOVNO_HOME / "templates"


class InstallWorker(QThread):
    """Поток для установки (чтобы GUI не зависал)"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, install_path, use_sudo, install_templates, add_to_path):
        super().__init__()
        self.install_path = Path(install_path)
        self.use_sudo = use_sudo
        self.install_templates = install_templates
        self.add_to_path = add_to_path
    
    def run(self):
        try:
            # Шаг 1: Создание структуры
            self.progress.emit(10, "📁 Создаём структуру папок...")
            bin_dir = self.install_path / "bin"
            lib_dir = self.install_path / "lib"
            templates_dir = self.install_path / "templates"
            
            bin_dir.mkdir(parents=True, exist_ok=True)
            lib_dir.mkdir(parents=True, exist_ok=True)
            templates_dir.mkdir(parents=True, exist_ok=True)
            
            # Шаг 2: Копирование компилятора
            self.progress.emit(30, "📦 Устанавливаем компилятор...")
            lib_file = lib_dir / "govnovoz_core.py"
            with open(__file__, 'r', encoding='utf-8') as src:
                with open(lib_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            # Шаг 3: Создание исполняемого файла
            self.progress.emit(50, "🔧 Создаём команду govnovoz...")
            executable = bin_dir / "govnovoz"
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
            
            # Шаг 4: Создание шаблонов
            if self.install_templates:
                self.progress.emit(70, "📝 Создаём примеры программ...")
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
                    with open(templates_dir / name, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            # Шаг 5: Добавление в PATH
            if self.add_to_path:
                self.progress.emit(90, "🔄 Добавляем в PATH...")
                self.add_to_path_file()
            
            # Шаг 6: Ссылка в /usr/local/bin
            if self.use_sudo and platform.system() in ["Linux", "Darwin"]:
                self.progress.emit(95, "🔗 Создаём ссылку в /usr/local/bin...")
                try:
                    cmd = f"echo 'password' | sudo -S ln -sf {bin_dir}/govnovoz /usr/local/bin/govnovoz"
                    # На самом деле надо будет запросить пароль через GUI
                    subprocess.run(["sudo", "ln", "-sf", str(bin_dir/"govnovoz"), "/usr/local/bin/govnovoz"], 
                                 capture_output=True)
                except:
                    pass
            
            self.progress.emit(100, "✅ Установка завершена!")
            self.finished.emit(True, f"Govnovoz установлен в {self.install_path}")
            
        except Exception as e:
            self.finished.emit(False, f"Ошибка: {e}")
    
    def add_to_path_file(self):
        """Добавление в .bashrc/.zshrc"""
        shell = os.environ.get('SHELL', '')
        rc_file = None
        
        if 'zsh' in shell:
            rc_file = Path.home() / '.zshrc'
        elif 'bash' in shell:
            rc_file = Path.home() / '.bashrc'
        
        if rc_file and rc_file.exists():
            with open(rc_file, 'a') as f:
                f.write(f'\n# Добавлено Govnovoz\nexport PATH="$PATH:{BIN_DIR}"\n')


class GovnovozGUI(QMainWindow):
    """Главное окно установщика"""
    
    def __init__(self):
        super().__init__()
        self.system = platform.system()
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle(f"🚛 GOVNOVOZ v{VERSION} — Установщик")
        self.setFixedSize(700, 600)
        self.center_window()
        
        # Устанавливаем иконку
        self.setWindowIcon(self.create_icon())
        
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        
        # Главный layout
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # ===== ХЕДЕР =====
        header = self.create_header()
        layout.addWidget(header)
        
        # ===== СТЕК ЭКРАНОВ =====
        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)
        
        # Создаём экраны
        self.welcome_screen = self.create_welcome_screen()
        self.install_screen = self.create_install_screen()
        self.progress_screen = self.create_progress_screen()
        self.complete_screen = self.create_complete_screen()
        
        self.stacked.addWidget(self.welcome_screen)
        self.stacked.addWidget(self.install_screen)
        self.stacked.addWidget(self.progress_screen)
        self.stacked.addWidget(self.complete_screen)
        
        # ===== НИЖНЯЯ ПАНЕЛЬ =====
        bottom = self.create_bottom_bar()
        layout.addWidget(bottom)
        
        # Применяем стили
        self.apply_styles()
        
        # Показываем первый экран
        self.stacked.setCurrentIndex(0)
        
        # Проверяем существующую установку
        self.check_existing()
    
    def create_icon(self):
        """Создание иконки приложения"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Рисуем говно
        painter.setBrush(QColor('#8B4513'))
        painter.setPen(QPen(QColor('#5D3A1A'), 2))
        
        path = QPainterPath()
        path.moveTo(32, 10)
        path.cubicTo(45, 15, 50, 30, 45, 45)
        path.cubicTo(40, 55, 25, 55, 15, 45)
        path.cubicTo(10, 35, 15, 20, 32, 10)
        painter.drawPath(path)
        
        # Глазки
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(25, 25, 8, 8)
        painter.drawEllipse(35, 25, 8, 8)
        painter.setBrush(Qt.GlobalColor.black)
        painter.drawEllipse(27, 27, 4, 4)
        painter.drawEllipse(37, 27, 4, 4)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_header(self):
        """Создание шапки"""
        header = QWidget()
        header.setFixedHeight(100)
        
        layout = QHBoxLayout(header)
        
        # Анимированная иконка
        self.poop_label = QLabel("💩")
        self.poop_label.setFont(QFont("Segoe UI", 48))
        layout.addWidget(self.poop_label)
        
        # Текст
        text = QWidget()
        text_layout = QVBoxLayout(text)
        
        title = QLabel("GOVNOVOZ")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #FF8C42;")
        
        subtitle = QLabel(f"v{VERSION} — {' / '.join(GOVNO_EXTENSIONS)}")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #B0B0B0;")
        
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        text_layout.addStretch()
        
        layout.addWidget(text)
        layout.addStretch()
        
        # Таймер анимации
        self.poop_timer = QTimer()
        self.poop_timer.timeout.connect(self.animate_poop)
        self.poop_timer.start(2000)
        
        return header
    
    def create_welcome_screen(self):
        """Экран приветствия"""
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setSpacing(30)
        
        # Приветствие
        welcome = QLabel(
            "🚛 ДОБРО ПОЖАЛОВАТЬ В МИР ГОВНА!\n\n"
            "Govnovoz — это язык программирования,\n"
            "где каждая команда пахнет навозом.\n\n"
            f"Поддерживаются расширения: {', '.join(GOVNO_EXTENSIONS)}"
        )
        welcome.setFont(QFont("Segoe UI", 14))
        welcome.setWordWrap(True)
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome)
        
        # Информация о системе
        info = QLabel(
            f"Система: {self.system}\n"
            f"Домашняя папка: {Path.home()}\n"
            f"Python: {sys.version.split()[0]}"
        )
        info.setFont(QFont("Segoe UI", 11))
        info.setStyleSheet("""
            background-color: #1A1A1A;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 20px;
        """)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        # Предупреждение
        warning = QLabel(
            "⚠️ ВНИМАНИЕ: Язык создан для кайфа,\n"
            "не используйте в продакшене!"
        )
        warning.setStyleSheet("color: #FF8C42; font-weight: bold;")
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning)
        
        layout.addStretch()
        return screen
    
    def create_install_screen(self):
        """Экран настроек установки"""
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("⚙️ НАСТРОЙКИ УСТАНОВКИ")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #FF8C42;")
        layout.addWidget(title)
        
        # Группа пути
        path_group = QGroupBox("📁 Путь установки")
        path_group.setStyleSheet("""
            QGroupBox {
                color: #FF8C42;
                border: 1px solid #333;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        path_layout = QHBoxLayout(path_group)
        
        self.path_edit = QLineEdit(str(GOVNO_HOME))
        self.path_edit.setReadOnly(True)
        self.path_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1A1A1A;
                color: white;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 8px;
            }
        """)
        
        browse_btn = QPushButton("📂 Обзор")
        browse_btn.clicked.connect(self.browse_path)
        browse_btn.setStyleSheet(self.get_button_style())
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        
        layout.addWidget(path_group)
        
        # Группа опций
        options_group = QGroupBox("⚡ Дополнительные опции")
        options_group.setStyleSheet(path_group.styleSheet())
        
        options_layout = QVBoxLayout(options_group)
        
        self.sudo_check = QCheckBox("🔐 Использовать sudo для /usr/local/bin")
        self.sudo_check.setChecked(True)
        options_layout.addWidget(self.sudo_check)
        
        self.templates_check = QCheckBox("📝 Установить примеры программ")
        self.templates_check.setChecked(True)
        options_layout.addWidget(self.templates_check)
        
        self.path_check = QCheckBox("🔄 Добавить в PATH (через .bashrc)")
        self.path_check.setChecked(True)
        options_layout.addWidget(self.path_check)
        
        layout.addWidget(options_group)
        
        # Информация
        info = QLabel(
            "После установки команда 'govnovoz' будет доступна\n"
            "из любой папки. Файлы .govno и .navoz можно запускать\n"
            "напрямую или через компилятор."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; padding: 10px;")
        layout.addWidget(info)
        
        layout.addStretch()
        return screen
    
    def create_progress_screen(self):
        """Экран прогресса установки"""
        screen = QWidget()
        layout = QVBoxLayout(screen)
        
        # Заголовок
        title = QLabel("🔄 УСТАНОВКА...")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #FF8C42;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #1A1A1A;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #FF8C42;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Лог
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(250)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1A1A1A;
                color: #B0B0B0;
                border: 1px solid #333;
                border-radius: 10px;
                font-family: monospace;
                padding: 15px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Анимация
        self.anim_label = QLabel("💩")
        self.anim_label.setFont(QFont("Segoe UI", 48))
        self.anim_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.anim_label)
        
        # Таймер анимации прогресса
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.animate_progress)
        
        layout.addStretch()
        return screen
    
    def create_complete_screen(self):
        """Экран завершения"""
        screen = QWidget()
        layout = QVBoxLayout(screen)
        
        # Успех
        success = QLabel("✅")
        success.setFont(QFont("Segoe UI", 72))
        success.setAlignment(Qt.AlignmentFlag.AlignCenter)
        success.setStyleSheet("color: #4CAF50;")
        layout.addWidget(success)
        
        # Текст
        complete = QLabel("УСТАНОВКА ЗАВЕРШЕНА!")
        complete.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        complete.setAlignment(Qt.AlignmentFlag.AlignCenter)
        complete.setStyleSheet("color: #FF8C42;")
        layout.addWidget(complete)
        
        # Информация
        info = QLabel(
            f"📁 Говно установлено: {GOVNO_HOME}\n"
            "🚛 Команда: govnovoz\n"
            f"📝 Поддерживаются: {', '.join(GOVNO_EXTENSIONS)}\n"
            "💡 Попробуйте: govnovoz --example"
        )
        info.setFont(QFont("Segoe UI", 12))
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("background-color: #1A1A1A; padding: 20px; border-radius: 10px;")
        layout.addWidget(info)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        example_btn = QPushButton("📝 Создать пример")
        example_btn.clicked.connect(self.create_example)
        example_btn.setStyleSheet(self.get_button_style())
        
        repl_btn = QPushButton("🎮 Запустить REPL")
        repl_btn.clicked.connect(self.run_repl)
        repl_btn.setStyleSheet(self.get_button_style())
        
        btn_layout.addWidget(example_btn)
        btn_layout.addWidget(repl_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return screen
    
    def create_bottom_bar(self):
        """Нижняя панель с кнопками"""
        bar = QWidget()
        bar.setFixedHeight(50)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.back_btn = QPushButton("◀ Назад")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setStyleSheet(self.get_button_style())
        
        self.next_btn = QPushButton("Далее ▶")
        self.next_btn.clicked.connect(self.go_next)
        self.next_btn.setStyleSheet(self.get_button_style() + """
            QPushButton {
                background-color: #FF8C42;
                color: black;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFA55C;
            }
        """)
        
        self.cancel_btn = QPushButton("✕ Отмена")
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setStyleSheet(self.get_button_style())
        
        layout.addWidget(self.back_btn)
        layout.addStretch()
        layout.addWidget(self.cancel_btn)
        layout.addWidget(self.next_btn)
        
        return bar
    
    def get_button_style(self):
        """Стиль кнопок"""
        return """
            QPushButton {
                background-color: #2A2A2A;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3A3A3A;
                border-color: #FF8C42;
            }
            QPushButton:pressed {
                background-color: #1A1A1A;
            }
            QPushButton:disabled {
                background-color: #1A1A1A;
                color: #666;
                border-color: #333;
            }
        """
    
    def apply_styles(self):
        """Общие стили"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0A0A0A;
            }
            QLabel {
                color: white;
            }
            QCheckBox {
                color: #B0B0B0;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #1A1A1A;
            }
            QCheckBox::indicator:checked {
                background-color: #FF8C42;
                border-color: #FF8C42;
            }
        """)
    
    def center_window(self):
        """Центрирование окна"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def check_existing(self):
        """Проверка существующей установки"""
        if GOVNO_HOME.exists():
            reply = QMessageBox.question(
                self,
                "Говно уже есть!",
                "Govnovoz уже установлен в системе.\n"
                "Хотите переустановить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                self.stacked.setCurrentIndex(3)
                self.installation_complete = True
                self.next_btn.setText("Завершить")
    
    def browse_path(self):
        """Выбор пути установки"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для установки",
            str(Path.home())
        )
        if path:
            self.path_edit.setText(path)
    
    def go_back(self):
        """Переход назад"""
        current = self.stacked.currentIndex()
        if current > 0:
            self.stacked.setCurrentIndex(current - 1)
        self.back_btn.setEnabled(current > 1)
        if current == 1:
            self.next_btn.setText("Далее ▶")
    
    def go_next(self):
        """Переход вперёд"""
        current = self.stacked.currentIndex()
        
        if current == 0:
            self.stacked.setCurrentIndex(1)
            self.back_btn.setEnabled(True)
            
        elif current == 1:
            self.start_installation()
            
        elif current == 2:
            # Установка уже идёт
            pass
            
        elif current == 3:
            self.close()
    
    def start_installation(self):
        """Начало установки"""
        self.stacked.setCurrentIndex(2)
        self.back_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # Очищаем лог
        self.log_text.clear()
        
        # Запускаем установку в отдельном потоке
        self.worker = InstallWorker(
            self.path_edit.text(),
            self.sudo_check.isChecked(),
            self.templates_check.isChecked(),
            self.path_check.isChecked()
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.installation_finished)
        self.worker.start()
        
        # Запускаем анимацию
        self.progress_timer.start(100)
    
    def update_progress(self, value, message):
        """Обновление прогресса"""
        self.progress_bar.setValue(value)
        self.log_text.append(message)
        # Прокрутка вниз
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def animate_poop(self):
        """Анимация говна в шапке"""
        current = self.poop_label.text()
        if current == "💩":
            self.poop_label.setText("🚛")
        elif current == "🚛":
            self.poop_label.setText("💩")
    
    def animate_progress(self):
        """Анимация во время установки"""
        frames = ["💩", "🚛", "🌾", "💩", "📦"]
        current = self.anim_label.text()
        idx = (frames.index(current) + 1) % len(frames) if current in frames else 0
        self.anim_label.setText(frames[idx])
    
    def installation_finished(self, success, message):
        """Завершение установки"""
        self.progress_timer.stop()
        self.anim_label.setText("✅" if success else "❌")
        
        if success:
            self.log_text.append("\n✅ Установка успешно завершена!")
            self.stacked.setCurrentIndex(3)
            self.next_btn.setText("Завершить")
        else:
            self.log_text.append(f"\n❌ {message}")
            self.next_btn.setText("Закрыть")
        
        self.back_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
    
    def create_example(self):
        """Создание примера программы"""
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
        filename = "example.govno"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(example)
            os.chmod(filename, 0o755)
            QMessageBox.information(
                self,
                "Готово!",
                f"Файл {filename} создан!\n\n"
                f"Запустите: govnovoz {filename}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать файл: {e}")
    
    def run_repl(self):
        """Запуск REPL"""
        self.hide()
        try:
            subprocess.run(["govnovoz", "--repl"])
        except:
            subprocess.run(["python3", str(LIB_DIR / "govnovoz_core.py"), "--repl"])
        finally:
            self.show()
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.stacked.currentIndex() == 2 and hasattr(self, 'worker') and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Прервать установку?",
                "Установка ещё не завершена.\n"
                "Точно хотите прервать?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        event.accept()


def main():
    """Главная функция"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Устанавливаем шрифт
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Создаём и показываем окно
    window = GovnovozGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()