#!/usr/bin/env python3
"""
VoteToVid локальный сервер
Запускает веб-сервер для офлайн-просмотра карты красивых видов
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Настройки
PORT = 8000
DIRECTORY = Path(__file__).parent


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Кастомный обработчик HTTP-запросов с поддержкой CORS
    и правильной обработкой путей к тайлам
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        # Добавляем CORS заголовки для работы с локальными ресурсами
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # Логирование запросов
        print(f"GET запрос: {self.path}")

        # Если запрашиваются тайлы, но они не существуют, возвращаем пустое изображение
        if '/tiles/' in self.path:
            tile_path = DIRECTORY / self.path.lstrip('/')
            if not tile_path.exists():
                # Возвращаем прозрачное изображение 1x1 пиксель
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                # Прозрачный PNG 1x1
                empty_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
                self.wfile.write(empty_png)
                return

        # Обработка обычных запросов
        super().do_GET()

    def log_message(self, format, *args):
        # Красивый лог
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")


def create_directories():
    """Создаем необходимые директории для тайлов"""
    tiles_dir = DIRECTORY / 'tiles'
    for subdir in ['terrain', 'satellite', 'views', 'slopes']:
        (tiles_dir / subdir).mkdir(parents=True, exist_ok=True)
    print(f"✓ Созданы директории для тайлов в {tiles_dir}")


def print_info():
    """Выводим информацию о сервере"""
    print("\n" + "=" * 60)
    print("🗺️  VoteToVid - Локальный сервер карты красивых видов")
    print("=" * 60)
    print(f"\n📁 Рабочая директория: {DIRECTORY}")
    print(f"🌐 Сервер запущен на порту: {PORT}")
    print(f"\n🔗 Откройте в браузере:")
    print(f"   → http://localhost:{PORT}")
    print(f"   → http://127.0.0.1:{PORT}")
    print("\n💡 Особенности офлайн-режима:")
    print("   • Leaflet библиотека загружается из CDN (нужен интернет при первом запуске)")
    print("   • Тайлы карт хранятся локально в папке 'tiles/'")
    print("   • Для полного офлайн-режима загрузите тайлы заранее")
    print("\n📦 Структура тайлов:")
    print("   tiles/terrain/{z}/{x}/{y}.png   - тайлы рельефа")
    print("   tiles/satellite/{z}/{x}/{y}.jpg - спутниковые снимки")
    print("   tiles/views/{z}/{x}/{y}.png     - слой красоты видов")
    print("   tiles/slopes/{z}/{x}/{y}.png    - слой уклонов")
    print("\n⚠️  Для загрузки тайлов используйте утилиту tile_downloader.py")
    print("   (см. README.md для инструкций)")
    print("\n⌨️  Нажмите Ctrl+C для остановки сервера")
    print("=" * 60 + "\n")


def main():
    """Главная функция запуска сервера"""

    # Переходим в рабочую директорию
    os.chdir(DIRECTORY)

    # Создаем директории
    create_directories()

    # Выводим информацию
    print_info()

    # Запускаем сервер
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✓ Сервер успешно запущен!\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⚠️  Сервер остановлен пользователем")
        sys.exit(0)
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"\n❌ ОШИБКА: Порт {PORT} уже используется!")
            print(f"   Попробуйте изменить PORT в скрипте или закрыть программу, использующую порт {PORT}")
        else:
            print(f"\n❌ ОШИБКА: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()