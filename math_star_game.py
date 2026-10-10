"""Know-It-All: five school subjects in a star-themed Tkinter quiz."""
import math
import pygame
import random
import tkinter as tk
from tkinter import ttk

from questions import SUBJECTS, DIFFICULTIES, Session, make_test

BG = '#1e1e2f'
PANEL = '#252538'
TEXT = '#f4f4ff'
MUTED = '#b8b8d4'
GOLD = '#ffd76a'


class MathStarGame:
    def __init__(self, root):
        self.root = root
        root.title('⭐ Know-It-All — Всезнайка')
        root.geometry('820x780')
        root.minsize(760, 720)
        root.configure(bg=BG)

        # Инициализация звукового движка pygame
        pygame.mixer.init()
        try:
            pygame.mixer.music.load('media/music/Relaxing music.mp3')  # Путь к вашему файлу
            pygame.mixer.music.set_volume(0.5)            # Начальная громкость (от 0.0 до 1.0)
            pygame.mixer.music.play(-1)                   # -1 означает бесконечный цикл
        except Exception as e:
            print(f"Музыкальный файл не найден или не загружен: {e}")

        # --- Загрузка звуков кликов (SFX) ---
        self.sfx_muted = False
        try:
            self.std_click_sound = pygame.mixer.Sound('media/music/Standart btn.mp3')
        except Exception as e:
            self.std_click_sound = None
            print(f"Звук standart_btn не найден: {e}")
            
        try:
            self.start_click_sound = pygame.mixer.Sound('media/music/Game start btn.mp3')
        except Exception as e:
            self.start_click_sound = None
            print(f"Звук start_btn не найден: {e}")
        
        self.subject = tk.StringVar(value=SUBJECTS[0])
        self.difficulty = tk.StringVar(value=DIFFICULTIES[0])
        self.session = None
        self.particles = []
        self.animation_id = None
        self.closed = False
        self.quiz_subject = self.quiz_difficulty = ''
        self.setup_ui()
        root.bind('<Return>', self.on_enter)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.show_home()
        self.animate()

        # Инициализация звукового движка pygame
        pygame.mixer.init()
        try:
            pygame.mixer.music.load('media/music/Relaxing music.mp3')  # Путь к вашему файлу
            pygame.mixer.music.set_volume(0.5)            # Начальная громкость (от 0.0 до 1.0)
            pygame.mixer.music.play(-1)                   # -1 означает бесконечный цикл
        except Exception as e:
            print(f"Музыкальный файл не найден или не загружен: {e}")

        # --- Загрузка звуков кликов (SFX) ---
        self.sfx_muted = False
        try:
            self.std_click_sound = pygame.mixer.Sound('media/music/Standart btn.mp3')
        except Exception as e:
            self.std_click_sound = None
            print(f"Звук standart_btn не найден: {e}")
            
        try:
            self.start_click_sound = pygame.mixer.Sound('media/music/Game start btn.mp3')
        except Exception as e:
            self.start_click_sound = None
            print(f"Звук start_btn не найден: {e}")

    def show_volume_slider(self, event=None):
        # Показываем ползунок ПЕРЕД кнопкой кликов, чтобы она оставалась доступной справа
        if not self.volume_slider.winfo_ismapped():
            self.volume_slider.pack(side='left', before=self.sfx_btn, padx=(6, 6))

    def hide_volume_slider(self, event=None):
        # Скрываем ползунок, только если курсор действительно ушел со всех элементов управления звуком
        x, y = self.root.winfo_pointerxy()
        widget_under_mouse = self.root.winfo_containing(x, y)
        if widget_under_mouse not in (self.volume_slider, self.sound_btn, self.sfx_btn):
            self.volume_slider.pack_forget()

    def toggle_sound(self):
        self.sound_muted = not self.sound_muted
        if self.sound_muted:
            self.sound_btn.configure(text='🔇', fg=MUTED)
            pygame.mixer.music.pause()  # Ставим музыку на паузу
        else:
            self.sound_btn.configure(text='🔊', fg=GOLD)
            pygame.mixer.music.unpause()  # Возобновляем музыку

    def toggle_sfx(self):
        self.sfx_muted = not self.sfx_muted
        if self.sfx_muted:
            self.sfx_btn.configure(fg=MUTED)
        else:
            self.sfx_btn.configure(fg=GOLD)

    def on_volume_changed(self, value):
        vol = float(value)
        if self.sound_muted and vol > 0:
            # Если двигаем ползунок при выключенном звуке — автоматически включаем звук обратно
            self.sound_muted = False
            self.sound_btn.configure(text='🔊', fg=GOLD)
            pygame.mixer.music.unpause()
        pygame.mixer.music.set_volume(vol)  # Меняем громкость в реальном времени

    def label(self, parent, text='', size=14, color=TEXT, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=color,
                        font=('Arial', size), **kwargs)

    def button(self, parent, text, command, color='#3d3d5c', sound=None, **kwargs):
        def lighten_hex(hex_str, factor=1.25):
            hex_str = hex_str.lstrip('#')
            try:
                rgb = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
                new_rgb = tuple(min(255, int(c * factor)) for c in rgb)
                return f'#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}'
            except Exception:
                return hex_str

        hover_color = lighten_hex(color, 1.25)

        # Выбираем звук: если передан персональный, берем его, иначе стандартный
        active_sound = sound if sound is not None else getattr(self, 'std_click_sound', None)

        def on_click_wrapper():
            if not getattr(self, 'sfx_muted', False) and active_sound:
                active_sound.play()
            if command:
                command()

        btn = tk.Button(parent, text=text, command=on_click_wrapper, font=('Arial', 13, 'bold'),
                         bg=color, fg=TEXT, activebackground=color, activeforeground=TEXT,
                         padx=14, pady=9, relief='flat', cursor='hand2', **kwargs)

        def on_enter(event):
            if btn['state'] != 'disabled':
                btn.configure(bg=hover_color)

        def on_leave(event):
            if btn['state'] != 'disabled':
                btn.configure(bg=color)

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn

    def setup_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill='x', padx=24, pady=(16, 8))
        self.label(header, '⭐ Всезнайка', 24, GOLD).pack(side='left')

        # --- Настройка красивого стиля для ползунка ---
        style = ttk.Style()
        style.theme_use('clam')  # 'clam' позволяет менять цвета элементов

        # Настройка стиля для прогресс-бара
        style.configure('Custom.Horizontal.TProgressbar',
                        troughcolor='#3d3d5c',  # Цвет фоновой дорожки (тёмный)
                        background=GOLD,        # Цвет заполненной шкалы (золотой)
                        bordercolor='#3d3d5c',
                        lightcolor=GOLD,
                        darkcolor=GOLD)

        style.configure('Custom.Horizontal.TScale',
                        background=BG,          # Фоновый цвет вокруг ползунка
                        troughcolor='#3d3d5c',  # Цвет дорожки (желоба)
                        slidercolor=GOLD,       # Цвет самого ползунка (бегунка)
                        bordercolor='#3d3d5c',
                        lightcolor=GOLD,
                        darkcolor=GOLD)

        # Настройка красивого стиля для выпадающих списков (Combobox)
        style.configure('Custom.TCombobox',
                        fieldbackground='#3d3d5c',  # Цвет фона поля ввода
                        background='#3d3d5c',      # Цвет кнопки со стрелочкой
                        foreground=TEXT,           # Цвет текста («Математика», «Лёгкий»)
                        arrowcolor=GOLD,           # Цвет стрелочки (делаем золотым под стиль игры)
                        bordercolor='#3d3d5c',
                        lightcolor='#3d3d5c',
                        darkcolor='#3d3d5c')

        # Настройка внешнего вида самого выпадающего списка (всплывающего окна)
        self.root.option_add('*TCombobox*Listbox.background', '#252538')      # Тёмный фон списка (под цвет PANEL)
        self.root.option_add('*TCombobox*Listbox.foreground', TEXT)          # Цвет текста элементов
        self.root.option_add('*TCombobox*Listbox.selectBackground', '#555580') # Цвет подсветки при наведении/выборе
        self.root.option_add('*TCombobox*Listbox.selectForeground', TEXT)      # Цвет текста выбранного элемента
        self.root.option_add('*TCombobox*Listbox.font', ('Arial', 12))         # Шрифт элементов списка
        self.root.option_add('*TCombobox*Listbox.relief', 'flat')            # Убираем лишние рамки
        self.root.option_add('*TCombobox*Listbox.highlightthickness', 0)
        
        # Настройка цветов при выборе элементов и наведении
        style.map('Custom.TCombobox',
                  fieldbackground=[('readonly', '#3d3d5c')],
                  selectbackground=[('readonly', '#555580')],
                  selectforeground=[('readonly', TEXT)],
                  background=[('readonly', '#3d3d5c')])

        # --- Блок управления звуком ---
        self.sound_muted = False
        self.volume_var = tk.DoubleVar(value=0.5) # Громкость от 0 до 1
        
        sound_frame = tk.Frame(header, bg=BG)
        sound_frame.pack(side='right', padx=10)
        
        # Кнопка звука (иконка)
        self.sound_btn = tk.Button(sound_frame, text='🔊', font=('Arial', 12),
                                   bg=PANEL, fg=TEXT, relief='flat',
                                   activebackground=PANEL, activeforeground=TEXT,
                                   cursor='hand2', command=self.toggle_sound, width=3)
        self.sound_btn.pack(side='left')

    # Кнопка включения/выключения звуков кликов (SFX)
        self.sfx_btn = tk.Button(sound_frame, text='🖱️', font=('Arial', 12),
                                  bg=PANEL, fg=TEXT, relief='flat',
                                  activebackground=PANEL, activeforeground=TEXT,
                                  cursor='hand2', command=self.toggle_sfx, width=3)
        self.sfx_btn.pack(side='left', padx=(4, 0))
        
        # Ползунок громкости (создаем, но пока не упаковываем, чтобы скрыт)
        self.volume_slider = ttk.Scale(sound_frame, from_=0, to=1, orient='horizontal',
                                       variable=self.volume_var, length=90, 
                                       style='Custom.Horizontal.TScale',
                                       command=self.on_volume_changed)
        
        # События наведения мыши для показа/скрытия ползунка
        sound_frame.bind('<Enter>', self.show_volume_slider)
        sound_frame.bind('<Leave>', self.hide_volume_slider)
        self.sound_btn.bind('<Enter>', self.show_volume_slider)

        # Подпись в шапке
        self.label(header, 'Учись, пробуй, открывай!', 12, MUTED).pack(side='right')

        controls = tk.Frame(self.root, bg=PANEL)
        controls.pack(fill='x', padx=24, pady=8)
        self.label(controls, 'Предмет:', 12).grid(row=0, column=0, padx=10, pady=12)
        self.subject_box = ttk.Combobox(controls, textvariable=self.subject, values=SUBJECTS,
                                       state='readonly', width=17, font=('Arial', 12), 
                                       style='Custom.TCombobox')
        self.subject_box.grid(row=0, column=1, padx=4)
        self.label(controls, 'Сложность:', 12).grid(row=0, column=2, padx=10)
        self.level_box = ttk.Combobox(controls, textvariable=self.difficulty, values=DIFFICULTIES,
                                     state='readonly', width=12, font=('Arial', 12), 
                                     style='Custom.TCombobox')
        self.level_box.grid(row=0, column=3, padx=4)
        self.start_button = self.button(controls, 'Начать', self.start_test, sound=self.start_click_sound)
        self.start_button.grid(row=0, column=4, padx=12)
        controls.columnconfigure(4, weight=1)

        stats = tk.Frame(self.root, bg=BG)
        stats.pack(fill='x', padx=24, pady=6)
        self.progress = self.label(stats, '', 12, MUTED)
        self.progress.pack(side='left')
        self.stats = self.label(stats, '', 12, GOLD)
        self.stats.pack(side='right')
        self.bar = ttk.Progressbar(self.root, maximum=1, style='Custom.Horizontal.TProgressbar')
        self.bar.pack(fill='x', padx=24, pady=(0, 8))

        self.canvas = tk.Canvas(self.root, height=220, bg=PANEL, highlightthickness=0)
        self.canvas.pack(fill='x', padx=24)
        self.canvas.bind('<Configure>', self.resize_canvas)
        for _ in range(35):
            x, y = random.randint(5, 730), random.randint(5, 215)
            self.canvas.create_oval(x, y, x + 2, y + 2, fill='#555577', outline='')
        self.problem_text = self.canvas.create_text(380, 108, text='', width=690,
                                                   font=('Arial', 23, 'bold'), fill=TEXT,
                                                   justify='center')
        self.answer_area = tk.Frame(self.root, bg=BG)
        self.answer_area.pack(fill='x', padx=24, pady=14)
        self.feedback = self.label(self.root, '', 14, MUTED, wraplength=710, justify='center')
        self.feedback.pack(fill='x', padx=24, pady=6)
        self.next_button = self.button(self.root, 'Дальше →', self.next_question)
        self.next_button.pack(pady=(6, 12))
        self.hint = self.label(self.root, 'Выбери предмет и сложность, затем нажми «Начать».', 11, MUTED)
        self.hint.pack(side='bottom', pady=10)
        self.input_var = tk.StringVar()
        self.answer_buttons = []
        self.entry = self.submit_button = None

    def resize_canvas(self, event):
        self.canvas.coords(self.problem_text, event.width / 2, 108)
        self.canvas.itemconfigure(self.problem_text, width=max(200, event.width - 48))

    def clear_answers(self):
        for widget in self.answer_area.winfo_children():
            widget.destroy()
        self.answer_buttons = []
        self.entry = self.submit_button = None

    def show_home(self):
        self.canvas.itemconfigure(self.problem_text, text='Пять предметов. Три уровня.\nМного маленьких открытий!')
        self.feedback.configure(text='Математика • География • Английский\nХимия • Информатика')
        self.next_button.configure(state='disabled')
        self.progress.configure(text='Готов к новому тесту?')
        self.stats.configure(text='⭐ Очки: 0')

    def start_test(self):
        self.quiz_subject = self.subject.get()
        self.quiz_difficulty = self.difficulty.get()
        self.session = Session(make_test(self.quiz_subject, self.quiz_difficulty))
        self.subject_box.configure(state='disabled')
        self.level_box.configure(state='disabled')
        self.start_button.configure(text='В меню', command=self.go_home)
        self.bar.configure(maximum=len(self.session.questions), value=0)
        self.show_question()

    def go_home(self):
        self.session = None
        self.clear_answers()
        self.subject_box.configure(state='readonly')
        self.level_box.configure(state='readonly')
        self.start_button.configure(text='Начать', command=self.start_test)
        self.bar.configure(value=0)
        self.hint.configure(text='Выбери предмет и сложность, затем нажми «Начать».')
        self.show_home()

    def show_question(self):
        self.clear_answers()
        s, q = self.session, self.session.current
        self.canvas.itemconfigure(self.problem_text, text=q.prompt)
        self.progress.configure(text=f'{self.quiz_subject} · {self.quiz_difficulty} · {s.index + 1}/{len(s.questions)}')
        self.update_stats()
        self.feedback.configure(text='Впиши ответ.' if q.typed else 'Выбери один правильный ответ.', fg=MUTED)
        self.next_button.configure(state='disabled', text='Дальше →')
        if q.typed:
            self.input_var.set('')
            self.entry = tk.Entry(self.answer_area, textvariable=self.input_var, font=('Arial', 22),
                                  justify='center', bg=PANEL, fg=TEXT, insertbackground=TEXT, width=24)
            self.entry.pack(pady=10, ipady=8)
            self.submit_button = self.button(self.answer_area, 'Проверить', self.submit_input)
            self.submit_button.pack()
            self.entry.focus_set()
            self.hint.configure(text='Для английского ответа используй английскую раскладку. Enter — проверить.')
        else:
            colors = ('#285d42', '#294c79', '#795529', '#603d79')
            for i, option in enumerate(q.options):
                btn = self.button(self.answer_area, option, lambda value=option: self.submit(value),
                                  colors[i], wraplength=310, height=2)
                btn.grid(row=i // 2, column=i % 2, sticky='nsew', padx=6, pady=6)
                self.answer_buttons.append(btn)
            for col in (0, 1):
                self.answer_area.columnconfigure(col, weight=1, uniform='answers')
            self.hint.configure(text='После ответа прочитай объяснение и нажми «Дальше».')

    def update_stats(self):
        s = self.session
        self.stats.configure(text=f'⭐ {s.score} очков   🔥 Серия: {s.streak}')

    def submit_input(self):
        if not self.input_var.get().strip():
            self.feedback.configure(text='Сначала впиши ответ, затем нажми «Проверить».', fg=GOLD)
            return
        self.submit(self.input_var.get())

    def submit(self, answer):
        if self.session is None:
            return
        right = self.session.submit(answer)
        if right is None:
            return
        q = self.session.current
        for button in self.answer_buttons:
            button.configure(state='disabled')
        if self.entry is not None:
            self.entry.configure(state='disabled')
            self.submit_button.configure(state='disabled')
        prefix = '✨ Верно!' if right else f'Попробуй запомнить: правильный ответ — {q.answer}.'
        self.feedback.configure(text=f'{prefix}\n{q.explanation}', fg='#8de8ac' if right else '#ffb0b0')
        self.update_stats()
        self.bar.configure(value=self.session.index + 1)
        self.next_button.configure(state='normal', text='Результат →' if self.session.index + 1 == len(self.session.questions) else 'Дальше →')
        self.next_button.focus_set()
        if right:
            self.spawn_fireworks()

    def on_enter(self, event=None):
        if not self.session:
            return
        if self.session.answered:
            self.next_question()
        elif self.session.current.typed:
            self.submit_input()

    def next_question(self):
        if self.session is None or not self.session.answered:
            return
        if self.session.advance():
            self.show_question()
        else:
            self.show_result()

    def show_result(self):
        s = self.session
        self.clear_answers()
        total = len(s.questions)
        self.canvas.itemconfigure(self.problem_text, text=f'Тест завершён!\nПравильно: {s.correct} из {total}\n⭐ {s.score} очков')
        self.feedback.configure(text=f'Лучшая серия: {s.best_streak}. ' +
                                ('Отличная работа!' if s.correct == total else 'Ошибки помогают учиться. Попробуй ещё раз!'), fg=GOLD)
        self.progress.configure(text=f'{self.quiz_subject} · {self.quiz_difficulty} · Итоги')
        self.next_button.configure(state='disabled')
        self.button(self.answer_area, 'Ещё один тест', self.start_test).pack(side='left', padx=6)
        self.button(self.answer_area, 'Разбор ответов', lambda: self.show_review(s)).pack(side='left', padx=6)
        self.button(self.answer_area, 'Выбрать предмет', self.go_home).pack(side='right', padx=6)
        self.hint.configure(text='В разборе можно посмотреть каждый ответ и его объяснение.')
        # Finished quiz no longer accepts Return or submits.
        self.session = None

    def show_review(self, session):
        win = tk.Toplevel(self.root)
        win.title('Всезнайка — разбор ответов')
        win.geometry('700x560')
        frame = tk.Frame(win)
        frame.pack(fill='both', expand=True)
        scroll = ttk.Scrollbar(frame)
        scroll.pack(side='right', fill='y')
        text = tk.Text(frame, wrap='word', bg=PANEL, fg=TEXT, font=('Arial', 14),
                       padx=20, pady=20, yscrollcommand=scroll.set)
        text.pack(fill='both', expand=True)
        scroll.configure(command=text.yview)
        for i, (q, answer, right) in enumerate(session.history, 1):
            text.insert('end', f'{i}. {q.prompt}\n{"✓ Верно" if right else "✗ Ошибка"} · Твой ответ: {answer}\n'
                        f'Правильный ответ: {q.answer}\n{q.explanation}\n\n')
        text.configure(state='disabled')

    def spawn_fireworks(self):
        width = self.canvas.winfo_width()
        for _ in range(35):
            angle, speed = random.uniform(0, math.tau), random.uniform(2, 7)
            x, y = width / 2, 110
            particle = self.canvas.create_oval(x-3, y-3, x+3, y+3,
                        fill=random.choice((GOLD, '#ff80ab', '#8de8ac', '#80deff')), outline='')
            self.particles.append([particle, math.cos(angle)*speed, math.sin(angle)*speed, 24])

    def animate(self):
        if self.closed:
            return
        alive = []
        for p in self.particles:
            self.canvas.move(p[0], p[1], p[2])
            p[3] -= 1
            if p[3] > 0:
                alive.append(p)
            else:
                self.canvas.delete(p[0])
        self.particles = alive
        self.animation_id = self.root.after(30, self.animate)

    def close(self):
        self.closed = {}
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
        pygame.mixer.quit()  # Корректно завершаем работу звуковой системы при закрытии игры
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    MathStarGame(root)
    root.mainloop()
