import asyncio
import json
from datetime import datetime
import platform
import threading
from bybit_data import get_bybit_data
from okx_data import get_okx_data
import tkinter as tk
from tkinter import ttk

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Глобальные переменные для данных
current_data = {
    'bybit': {'price': 0, 'funding': 0, 'time_to_payment': 'N/A'},
    'okx': {'price': 0, 'funding': 0, 'time_to_payment': 'N/A'},
    'spreads': {'price': 0, 'funding': 0},
    'timestamp': 'N/A'
}

AVAILABLE_PAIRS = {
    'BTCUSDT': 'BTC/USDT',
    'ETHUSDT': 'ETH/USDT',
    'BNBUSDT': 'BNB/USDT',
    'SOLUSDT': 'SOL/USDT',
    'XRPUSDT': 'XRP/USDT',
    'ADAUSDT': 'ADA/USDT',
    'DOGEUSDT': 'DOGE/USDT',
    'DOTUSDT': 'DOT/USDT',
    'MATICUSDT': 'MATIC/USDT',
    'LTCUSDT': 'LTC/USDT'
}

selected_pair = 'BTCUSDT'
update_task = None

def calculate_spread(bybit_data, okx_data):
    """Вычисление спрэдов между Bybit и OKX"""
    if (isinstance(bybit_data['price'], (int, float)) and
            isinstance(okx_data['price'], (int, float))):
        max_price = max(bybit_data['price'], okx_data['price'])
        min_price = min(bybit_data['price'], okx_data['price'])
        price_spread = (max_price / min_price - 1) * 100

        funding_spread = (bybit_data['funding'] - okx_data['funding']
                          if max_price == bybit_data['price']
                          else okx_data['funding'] - bybit_data['funding'])

        return {
            'price': round(price_spread, 4),
            'funding': round(funding_spread, 6)
        }
    return {
        'price': 0,
        'funding': 0
    }

async def update_data():
    """Фоновая задача обновления данных"""
    global current_data, selected_pair
    okx_symbol = f"{selected_pair[:-4]}-USDT-SWAP"
    print(f"Обновление данных для Bybit: {selected_pair}, OKX: {okx_symbol}")  # Отладочное сообщение

    while True:
        try:
            bybit_data, okx_data = await asyncio.gather(
                get_bybit_data(selected_pair),
                get_okx_data(okx_symbol),
                return_exceptions=True
            )

            if not isinstance(bybit_data, Exception) and bybit_data:
                current_data['bybit'] = bybit_data
            if not isinstance(okx_data, Exception) and okx_data:
                current_data['okx'] = okx_data

            current_data['spreads'] = calculate_spread(current_data['bybit'], current_data['okx'])
            current_data['timestamp'] = datetime.now().strftime('%H:%M:%S')
            root.after(0, update_ui)

        except Exception as e:
            print(f"Ошибка обновления: {e}")

        await asyncio.sleep(1)

def update_ui():
    """Обновление интерфейса с новыми данными"""
    # Блок 1: Монетная пара и время обновления
    pair_label.config(text=f"{selected_pair[:-4]}/USDT")
    timestamp_label.config(text=f"Обновлено: {current_data['timestamp']}")

    # Блок 2: Данные Bybit
    bybit_price_label.config(text=f"Bybit:\nЦена: {current_data['bybit']['price']:.4f}")
    bybit_funding_label.config(text=f"Фандинг: {current_data['bybit']['funding']:.6f}%", fg=get_color(current_data['bybit']['funding']))
    bybit_time_label.config(text=f"До выплаты: {current_data['bybit']['time_to_payment']}")

    # Блок 3: Данные OKX
    okx_price_label.config(text=f"OKX:\nЦена: {current_data['okx']['price']:.4f}")
    okx_funding_label.config(text=f"Фандинг: {current_data['okx']['funding']:.6f}%", fg=get_color(current_data['okx']['funding']))
    okx_time_label.config(text=f"До выплаты: {current_data['okx']['time_to_payment']}")

    # Блок 4: Спреды
    spreads_price_label.config(text=f"Курсовой спред: {current_data['spreads']['price']:.4f}%", fg=get_color(current_data['spreads']['price']))
    spreads_funding_label.config(text=f"Спред фандинга: {current_data['spreads']['funding']:.6f}%", fg=get_color(current_data['spreads']['funding']))

def get_color(value):
    """Определение цвета для значений"""
    return "green" if value >= 0 else "red"

def on_pair_selected(event):
    global selected_pair, update_task
    selected_pair = pair_var.get()
    print(f"Выбрана новая пара: {selected_pair}")  # Отладочное сообщение

    # Остановка предыдущей задачи обновления
    if update_task is not None:
        update_task.cancel()

    # Запуск новой задачи обновления
    update_task = asyncio.run_coroutine_threadsafe(update_data(), loop)

def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Создание основного окна
root = tk.Tk()
root.title("Crypto Data Monitor")
root.geometry("400x600")  # Увеличиваем высоту окна
root.configure(bg="black")  # Черный фон

# Настройка шрифта
font_style = ("Courier New", 8, "bold")  # Уменьшенный шрифт
dropdown_font = ("Courier New", 8, "bold")  # Уменьшенный шрифт для списка

# Создание контейнера для выпадающего списка
dropdown_frame = ttk.Frame(root, width=140)  # Уменьшена ширина на 30%
dropdown_frame.pack(padx=10, pady=10, anchor="w")

# Создание виджетов
pair_var = tk.StringVar(value=selected_pair)
pair_dropdown = ttk.Combobox(dropdown_frame, textvariable=pair_var, values=list(AVAILABLE_PAIRS.keys()), font=dropdown_font, justify="center", width=15)  # Увеличена ширина кнопки
pair_dropdown.bind("<<ComboboxSelected>>", on_pair_selected)
pair_dropdown.pack(fill=tk.X, padx=10, pady=10)

pair_label = tk.Label(root, text=f"{selected_pair[:-4]}/USDT", font=font_style, anchor="w", bg="black", fg="white")
timestamp_label = tk.Label(root, text="Обновлено: N/A", font=font_style, anchor="w", bg="black", fg="white")

bybit_price_label = tk.Label(root, text="Bybit:\nЦена: N/A", font=font_style, anchor="w", justify="left", bg="black", fg="white")
bybit_funding_label = tk.Label(root, text="Фандинг: N/A", font=font_style, anchor="w", justify="left", bg="black", fg="white")
bybit_time_label = tk.Label(root, text="До выплаты: N/A", font=font_style, anchor="w", justify="left", bg="black", fg="white")

okx_price_label = tk.Label(root, text="OKX:\nЦена: N/A", font=font_style, anchor="w", justify="left", bg="black", fg="white")
okx_funding_label = tk.Label(root, text="Фандинг: N/A", font=font_style, anchor="w", justify="left", bg="black", fg="white")
okx_time_label = tk.Label(root, text="До выплаты: N/A", font=font_style, anchor="w", justify="left", bg="black", fg="white")

spreads_price_label = tk.Label(root, text="Курсовой спред: N/A", font=font_style, anchor="w", justify="left", bg="black", fg="white")
spreads_funding_label = tk.Label(root, text="Спред фандинга: N/A", font=font_style, anchor="w", justify="left", bg="black", fg="white")

# Размещение виджетов
pair_label.pack(fill=tk.X, padx=10, pady=5)
timestamp_label.pack(fill=tk.X, padx=10, pady=5)

tk.Label(root, text="", bg="black").pack()  # Пустая строка

bybit_price_label.pack(fill=tk.X, padx=10, pady=1)
bybit_funding_label.pack(fill=tk.X, padx=10, pady=1)
bybit_time_label.pack(fill=tk.X, padx=10, pady=1)

tk.Label(root, text="", bg="black").pack()  # Пустая строка

okx_price_label.pack(fill=tk.X, padx=10, pady=1)
okx_funding_label.pack(fill=tk.X, padx=10, pady=1)
okx_time_label.pack(fill=tk.X, padx=10, pady=1)

tk.Label(root, text="", bg="black").pack()  # Пустая строка

spreads_price_label.pack(fill=tk.X, padx=10, pady=1)
spreads_funding_label.pack(fill=tk.X, padx=10, pady=1)

# Запуск асинхронного цикла в отдельном потоке
loop = asyncio.new_event_loop()
thread = threading.Thread(target=start_asyncio_loop, args=(loop,), daemon=True)
thread.start()

# Запуск фоновой задачи обновления данных
update_task = asyncio.run_coroutine_threadsafe(update_data(), loop)

# Запуск основного цикла приложения
root.mainloop()
