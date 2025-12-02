#!/usr/bin/env python3
"""
Утилита для загрузки тайлов карт для офлайн-использования
Позволяет скачать тайлы для выбранной области и уровней зума
"""

import os
import sys
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import math


class TileDownloader:
    """Класс для загрузки тайлов карт"""

    # Источники тайлов
    TILE_SOURCES = {
        'terrain': 'https://tile.opentopomap.org/{z}/{x}/{y}.png',
        'satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        'osm': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    }

    def __init__(self, output_dir='tiles'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VoteToVid Offline Tile Downloader/1.0'
        })

    def lat_lon_to_tile(self, lat, lon, zoom):
        """Конвертирует координаты широты/долготы в номера тайлов"""
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (x, y)

    def download_tile(self, source_type, z, x, y, delay=0.1):
        """Загружает один тайл"""

        # Создаем путь для сохранения
        tile_dir = self.output_dir / source_type / str(z) / str(x)
        tile_dir.mkdir(parents=True, exist_ok=True)

        # Определяем расширение файла
        ext = '.jpg' if source_type == 'satellite' else '.png'
        tile_path = tile_dir / f"{y}{ext}"

        # Если тайл уже существует, пропускаем
        if tile_path.exists():
            return True, f"Пропущен (уже существует): {source_type}/{z}/{x}/{y}"

        # Получаем URL тайла
        url = self.TILE_SOURCES[source_type].format(z=z, x=x, y=y)

        try:
            # Задержка для соблюдения политики использования
            time.sleep(delay)

            # Загружаем тайл
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Сохраняем
            with open(tile_path, 'wb') as f:
                f.write(response.content)

            return True, f"Загружен: {source_type}/{z}/{x}/{y}"

        except requests.RequestException as e:
            return False, f"Ошибка при загрузке {source_type}/{z}/{x}/{y}: {e}"

    def download_area(self, lat_min, lon_min, lat_max, lon_max,
                      zoom_min, zoom_max, source_type='terrain',
                      max_workers=4, delay=0.1):
        """
        Загружает тайлы для указанной области

        Args:
            lat_min, lon_min: Минимальные координаты (юго-западный угол)
            lat_max, lon_max: Максимальные координаты (северо-восточный угол)
            zoom_min, zoom_max: Диапазон уровней зума
            source_type: Тип тайлов ('terrain', 'satellite', 'osm')
            max_workers: Количество параллельных потоков загрузки
            delay: Задержка между запросами (секунды)
        """

        print(f"\n{'=' * 60}")
        print(f"Начинается загрузка тайлов: {source_type}")
        print(f"{'=' * 60}")
        print(f"Область: ({lat_min}, {lon_min}) - ({lat_max}, {lon_max})")
        print(f"Уровни зума: {zoom_min} - {zoom_max}")
        print(f"Параллельных потоков: {max_workers}")
        print(f"Задержка между запросами: {delay}s")
        print(f"{'=' * 60}\n")

        # Подсчитываем общее количество тайлов
        total_tiles = 0
        tasks = []

        for zoom in range(zoom_min, zoom_max + 1):
            x_min, y_max = self.lat_lon_to_tile(lat_min, lon_min, zoom)
            x_max, y_min = self.lat_lon_to_tile(lat_max, lon_max, zoom)

            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    tasks.append((source_type, zoom, x, y, delay))
                    total_tiles += 1

        print(f"📊 Всего тайлов для загрузки: {total_tiles}\n")

        if total_tiles > 1000:
            print(f"⚠️  ВНИМАНИЕ: Это большое количество тайлов!")
            response = input("Продолжить? (yes/no): ")
            if response.lower() not in ['yes', 'y', 'да', 'д']:
                print("Загрузка отменена.")
                return

        # Загружаем тайлы параллельно
        downloaded = 0
        failed = 0
        skipped = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.download_tile, *task) for task in tasks]

            for future in as_completed(futures):
                success, message = future.result()

                if success:
                    if "Пропущен" in message:
                        skipped += 1
                    else:
                        downloaded += 1
                else:
                    failed += 1
                    print(f"❌ {message}")

                # Прогресс
                progress = downloaded + failed + skipped
                if progress % 10 == 0 or progress == total_tiles:
                    print(f"Прогресс: {progress}/{total_tiles} "
                          f"(загружено: {downloaded}, пропущено: {skipped}, ошибок: {failed})")

        print(f"\n{'=' * 60}")
        print(f"✓ Загрузка завершена!")
        print(f"  Загружено: {downloaded}")
        print(f"  Пропущено: {skipped}")
        print(f"  Ошибок: {failed}")
        print(f"{'=' * 60}\n")


def main():
    """Главная функция"""

    print("\n" + "=" * 60)
    print("🗺️  VoteToVid - Загрузчик тайлов карт")
    print("=" * 60 + "\n")

    downloader = TileDownloader()

    # Примеры популярных областей
    print("Выберите область для загрузки:")
    print("1. Горный Алтай (небольшая область)")
    print("2. Горный Алтай (расширенная область)")
    print("3. Крым")
    print("4. Байкал")
    print("5. Своя область (ввести координаты)")
    print("0. Выход")

    choice = input("\nВыбор (0-5): ").strip()

    areas = {
        '1': {
            'name': 'Горный Алтай (малая)',
            'bounds': (50.0, 86.0, 51.0, 87.5),
            'zoom': (8, 12)
        },
        '2': {
            'name': 'Горный Алтай (большая)',
            'bounds': (49.5, 85.0, 51.5, 88.5),
            'zoom': (7, 11)
        },
        '3': {
            'name': 'Крым',
            'bounds': (44.4, 33.5, 45.5, 36.5),
            'zoom': (8, 12)
        },
        '4': {
            'name': 'Байкал',
            'bounds': (51.5, 103.5, 53.5, 107.5),
            'zoom': (8, 11)
        }
    }

    if choice == '0':
        print("Выход.")
        return

    elif choice in areas:
        area = areas[choice]
        lat_min, lon_min, lat_max, lon_max = area['bounds']
        zoom_min, zoom_max = area['zoom']
        area_name = area['name']

    elif choice == '5':
        print("\nВведите координаты области:")
        try:
            lat_min = float(input("Минимальная широта: "))
            lon_min = float(input("Минимальная долгота: "))
            lat_max = float(input("Максимальная широта: "))
            lon_max = float(input("Максимальная долгота: "))
            zoom_min = int(input("Минимальный зум (обычно 7-10): "))
            zoom_max = int(input("Максимальный зум (обычно 11-14): "))
            area_name = "Своя область"
        except ValueError:
            print("❌ Ошибка ввода координат!")
            return
    else:
        print("❌ Неверный выбор!")
        return

    # Выбор типа карты
    print(f"\nОбласть: {area_name}")
    print("\nВыберите тип карты:")
    print("1. Рельеф (terrain)")
    print("2. Спутник (satellite)")
    print("3. OpenStreetMap")
    print("4. Всё вместе")

    map_choice = input("\nВыбор (1-4): ").strip()

    source_types = {
        '1': ['terrain'],
        '2': ['satellite'],
        '3': ['osm'],
        '4': ['terrain', 'satellite', 'osm']
    }

    if map_choice not in source_types:
        print("❌ Неверный выбор!")
        return

    sources = source_types[map_choice]

    # Загружаем
    for source in sources:
        downloader.download_area(
            lat_min, lon_min, lat_max, lon_max,
            zoom_min, zoom_max,
            source_type=source,
            max_workers=3,  # Не перегружаем серверы
            delay=0.5  # Задержка для соблюдения правил
        )

    print("\n✓ Все тайлы загружены!")
    print("Теперь вы можете запустить сервер командой: python server.py\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Загрузка прервана пользователем")
        sys.exit(0)