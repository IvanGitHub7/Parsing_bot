import tkinter as tk
from tkinter import ttk
import asyncio
import threading
from data_handler import DataHandler

class CryptoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Arbitrage Scanner")
        self.root.geometry("450x650")

        self.handler = DataHandler()
        self.current_sort = 'price'

        # Инициализируем labels заранее
        self.labels = {}

        self.setup_ui()
        self.start_background_tasks()

    def setup_ui(self):
        """Инициализация UI компонентов"""
        self.show_welcome_screen()

    def show_welcome_screen(self):
        """Экран приветствия"""
        self.clear_frame()

        frame = ttk.Frame(self.root)
        frame.pack(expand=True, padx=20, pady=50)

        ttk.Label(
            frame,
            text="Добро пожаловать в Арбитражный Сканер",
            font=('Helvetica', 14, 'bold')
        ).pack(pady=20)

        ttk.Label(
            frame,
            text="Выберите приоритет для сортировки пар:",
            font=('Helvetica', 10)
        ).pack(pady=10)

        self.sort_var = tk.StringVar(value='price')

        ttk.Radiobutton(
            frame,
            text="По курсовому спреду (≥0.1%)",
            variable=self.sort_var,
            value='price'
        ).pack(anchor='w', pady=5)

        ttk.Radiobutton(
            frame,
            text="По спреду фандинга (≥0.05%)",
            variable=self.sort_var,
            value='funding'
        ).pack(anchor='w', pady=5)

        ttk.Button(
            frame,
            text="Продолжить",
            command=self.show_main_screen
        ).pack(pady=20)

    def show_main_screen(self):
        """Основной экран с данными"""
        self.clear_frame()
        self.current_sort = self.sort_var.get()

        # Выпадающий список пар
        self.pair_var = tk.StringVar()
        self.pair_combobox = ttk.Combobox(
            self.root,
            textvariable=self.pair_var,
            state='readonly',
            font=('Helvetica', 12)
        )
        self.pair_combobox.pack(fill='x', padx=20, pady=10)
        self.pair_combobox.bind('<<ComboboxSelected>>', self.on_pair_selected)

        # Инициализация labels для данных
        self.init_data_labels()

        # Кнопка возврата
        ttk.Button(
            self.root,
            text='Изменить приоритет сортировки',
            command=self.show_welcome_screen
        ).pack(pady=10)

        # Загружаем пары
        self.load_pairs()

    def init_data_labels(self):
        """Инициализация меток для отображения данных"""
        self.data_frame = ttk.Frame(self.root)
        self.data_frame.pack(fill='both', expand=True, padx=20, pady=5)

        # Создаем и размещаем все метки
        self.labels = {
            'timestamp': ttk.Label(self.data_frame, text="Обновлено: N/A"),
            'bybit': ttk.Label(self.data_frame, text="Bybit:", font=('Helvetica', 11, 'bold')),
            'bybit_price': ttk.Label(self.data_frame, text="Цена: N/A"),
            'bybit_funding': ttk.Label(self.data_frame, text="Фандинг: N/A"),
            'bybit_time': ttk.Label(self.data_frame, text="До выплаты: N/A"),
            'okx': ttk.Label(self.data_frame, text="OKX:", font=('Helvetica', 11, 'bold')),
            'okx_price': ttk.Label(self.data_frame, text="Цена: N/A"),
            'okx_funding': ttk.Label(self.data_frame, text="Фандинг: N/A"),
            'okx_time': ttk.Label(self.data_frame, text="До выплаты: N/A"),
            'price_spread': ttk.Label(self.data_frame, text="Спред цены: N/A", font=('Helvetica', 11)),
            'funding_spread': ttk.Label(self.data_frame, text="Спред фандинга: N/A", font=('Helvetica', 11))
        }

        # Размещаем метки в grid
        rows = [
            ('timestamp', 0),
            ('', 1),  # Разделитель
            ('bybit', 2),
            ('bybit_price', 3),
            ('bybit_funding', 4),
            ('bybit_time', 5),
            ('', 6),  # Разделитель
            ('okx', 7),
            ('okx_price', 8),
            ('okx_funding', 9),
            ('okx_time', 10),
            ('', 11),  # Разделитель
            ('price_spread', 12),
            ('funding_spread', 13)
        ]

        for key, row in rows:
            if key == '':
                ttk.Separator(self.data_frame).grid(row=row, column=0, sticky='ew', pady=5)
            else:
                self.labels[key].grid(row=row, column=0, sticky='w', pady=2)

    def load_pairs(self):
        """Загрузка списка пар из БД"""
        def load():
            async def async_load():
                pairs = await self.handler.get_sorted_pairs(self.current_sort)
                self.root.after(0, self.update_pair_combobox, pairs)

            asyncio.run_coroutine_threadsafe(async_load(), self.loop)

        threading.Thread(target=load, daemon=True).start()

    def update_pair_combobox(self, pairs):
        """Обновление выпадающего списка пар"""
        if not pairs:
            pairs = ['BTCUSDT']

        self.pair_combobox['values'] = pairs
        self.pair_var.set(pairs[0])
        self.handler.set_pair(pairs[0])

    def on_pair_selected(self, event):
        """Обработчик выбора пары"""
        self.handler.set_pair(self.pair_var.get())

    def update_ui(self):
        """Обновление данных в интерфейсе"""
        if not hasattr(self, 'labels'):
            return

        data = self.handler.get_data()

        self.labels['timestamp'].config(text=f"Обновлено: {data['timestamp']}")

        # Bybit данные
        bybit = data['bybit']
        self.labels['bybit_price'].config(text=f"Цена: {bybit['price']:.4f}")
        self.labels['bybit_funding'].config(
            text=f"Фандинг: {bybit['funding']:.6f}%",
            foreground='green' if bybit['funding'] >= 0 else 'red'
        )
        self.labels['bybit_time'].config(text=f"До выплаты: {bybit['time_to_payment']}")

        # OKX данные
        okx = data['okx']
        self.labels['okx_price'].config(text=f"Цена: {okx['price']:.4f}")
        self.labels['okx_funding'].config(
            text=f"Фандинг: {okx['funding']:.6f}%",
            foreground='green' if okx['funding'] >= 0 else 'red'
        )
        self.labels['okx_time'].config(text=f"До выплаты: {okx['time_to_payment']}")

        # Спреды
        spreads = data['spreads']
        self.labels['price_spread'].config(
            text=f"Спред цены: {spreads['price']:.4f}%",
            foreground='green' if spreads['price'] >= 0 else 'red'
        )
        self.labels['funding_spread'].config(
            text=f"Спред фандинга: {spreads['funding']:.6f}%",
            foreground='green' if spreads['funding'] >= 0 else 'red'
        )

        self.root.after(1000, self.update_ui)

    def start_background_tasks(self):
        """Запуск фоновых задач"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.handler.set_callback(self.update_ui)

        def run_loop():
            self.loop.run_forever()

        threading.Thread(target=run_loop, daemon=True).start()
        self.handler.start(self.loop)

        # Запускаем обновление UI только после инициализации labels
        if hasattr(self, 'labels'):
            self.update_ui()

    def clear_frame(self):
        """Очистка фрейма"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def on_close(self):
        """Обработчик закрытия окна"""
        self.handler.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
