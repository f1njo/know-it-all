import math
import random
import tkinter as tk
from tkinter import ttk

from audio import Audio
from questions import SUBJECTS, DIFFICULTIES, Session, make_test
import ui
from ui import FONT, Button, Card, Progress, Toggle

SUBJECT_DETAILS = {
    'Математика': ('＋', '#007AFF', 'Примеры и задачи'),
    'География': ('◎', '#248754', 'Планета и страны'),
    'Английский': ('Aa', '#AF52DE', 'Слова и предложения'),
    'Химия': ('⚗', '#D47A16', 'Вещества и материалы'),
    'Информатика': ('⌘', '#5856D6', 'Компьютеры и алгоритмы'),
}


class KnowItAllGame:
    def __init__(self, root):
        self.root = root
        root.title('Всезнайка · Know-It-All')
        root.geometry('1000x780')
        root.minsize(920, 720)
        root.configure(bg=ui.COLORS['bg'])
        self.audio = Audio()
        self.dark_theme = tk.BooleanVar(value=False)
        self.subject = tk.StringVar(value=SUBJECTS[0])
        self.difficulty = tk.StringVar(value=DIFFICULTIES[0])
        self.input_var = tk.StringVar()
        self.session = None
        self.last_result = None
        self.particles = []
        self.animation_id = None
        self.closed = False
        self.quiz_subject = self.quiz_difficulty = ''
        self.settings_window = None
        self.setup_ui()
        root.bind('<Return>', self.on_enter)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.show_home()

    def label(self, parent, text='', size=13, color=None, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=ui.COLORS['text'] if color is None else color,
                        font=(FONT, size, 'bold' if bold else 'normal'), **kwargs)

    def button(self, parent, text, command, primary=False, **kwargs):
        kwargs.setdefault('sound', self.audio.click)
        return Button(parent, text, command, color=ui.COLORS['accent'] if primary else ui.COLORS['bg'],
                      foreground=ui.COLORS['on_accent'] if primary else ui.COLORS['text'], **kwargs)

    def setup_ui(self):
        header = tk.Frame(self.root, bg=ui.COLORS['bg'])
        header.pack(fill='x', padx=28, pady=(18, 14))
        titles = tk.Frame(header, bg=ui.COLORS['bg'])
        titles.pack(side='left')
        self.label(titles, 'Всезнайка', 27, bold=True).pack(anchor='w')
        self.button(header, 'Звук', self.show_settings, height=40).pack(side='right', ipadx=10)
        theme_controls = tk.Frame(header, bg=ui.COLORS['bg'])
        theme_controls.pack(side='right', padx=18)
        self.label(theme_controls, 'Тёмная тема', 11, ui.COLORS['muted']).pack(side='left', padx=(0, 8))
        self.theme_toggle = Toggle(theme_controls, self.dark_theme, self.toggle_theme)
        self.theme_toggle.pack(side='left')
        content = tk.Frame(self.root, bg=ui.COLORS['bg'])
        content.pack(fill='both', expand=True, padx=24, pady=(0, 20))
        sidebar = tk.Frame(content, bg=ui.COLORS['bg'], width=204)
        sidebar.pack(side='left', fill='y', padx=(0, 18))
        sidebar.pack_propagate(False)
        self.label(sidebar, 'ПРЕДМЕТЫ', 10, ui.COLORS['muted'], bold=True).pack(anchor='w', padx=8, pady=(10, 14))
        self.subject_buttons = {}
        for subject in SUBJECTS:
            symbol, color, _ = SUBJECT_DETAILS[subject]
            button = Button(sidebar, f'{symbol}   {subject}', lambda value=subject: self.select_subject(value),
                            height=56, sound=self.audio.click)
            button.pack(fill='x', pady=4)
            self.subject_buttons[subject] = button
        self.menu_button = self.button(sidebar, 'Предметы', self.go_home, height=44)
        self.menu_button.pack(side='bottom', fill='x', pady=8)

        card = Card(content, padding=18)
        card.pack(side='left', fill='both', expand=True)
        body = card.body
        self.lesson_title = self.label(body, '', 11, ui.COLORS['muted'], bold=True)
        self.lesson_title.pack(anchor='w', pady=(0, 12))
        levels = tk.Frame(body, bg=ui.COLORS['bg'])
        levels.pack(fill='x', pady=(0, 14))
        self.level_buttons = {}
        for i, level in enumerate(DIFFICULTIES):
            button = Button(levels, level, lambda value=level: self.select_level(value),
                            color=ui.COLORS['bg'], size=12, height=38, sound=self.audio.click)
            button.grid(row=0, column=i, sticky='ew', padx=3, pady=3)
            levels.columnconfigure(i, weight=1, uniform='level')
            self.level_buttons[level] = button
        stats = tk.Frame(body, bg=ui.COLORS['surface'])
        stats.pack(fill='x', pady=(0, 10))
        self.progress = self.label(stats, '', 11, ui.COLORS['muted'])
        self.progress.pack(side='left')
        self.stats = self.label(stats, '', 11, ui.COLORS['accent'], bold=True)
        self.stats.pack(side='right')
        self.bar = Progress(body)
        self.bar.pack(fill='x', pady=(0, 12))
        self.canvas = tk.Canvas(body, height=138, bg=ui.COLORS['surface'], highlightthickness=0)
        self.canvas.pack(fill='x')
        self.problem_text = self.canvas.create_text(300, 68, text='', width=540,
                            font=(FONT, 22, 'bold'), fill=ui.COLORS['text'], justify='center')
        self.canvas.bind('<Configure>', self.resize_canvas)

        self.answer_area = tk.Frame(body, bg=ui.COLORS['surface'], height=138)
        self.answer_area.pack(fill='x', pady=(8, 4))
        self.answer_area.pack_propagate(False)
        self.choice_frame = tk.Frame(self.answer_area, bg=ui.COLORS['surface'])
        self.all_answer_buttons = []
        for i in range(4):
            button = self.button(self.choice_frame, '', lambda index=i: self.submit_choice(index), height=62, size=12)
            button.grid(row=i//2, column=i%2, sticky='nsew', padx=4, pady=4)
            self.all_answer_buttons.append(button)
        for column in (0, 1):
            self.choice_frame.columnconfigure(column, weight=1, uniform='answer')
        self.input_frame = tk.Frame(self.answer_area, bg=ui.COLORS['surface'])
        self.input_frame.columnconfigure(0, weight=1)
        self.entry = tk.Entry(self.input_frame, textvariable=self.input_var, font=(FONT, 22),
                              bg=ui.COLORS['bg'], fg=ui.COLORS['text'], disabledbackground=ui.COLORS['bg'],
                              disabledforeground=ui.COLORS['text'], insertbackground=ui.COLORS['accent'], justify='center', relief='flat',
                              highlightthickness=2, highlightbackground=ui.COLORS['border'], highlightcolor=ui.COLORS['accent'])
        self.entry.grid(row=0, column=0, sticky='ew', pady=(10, 10), ipady=10)
        self.submit_button = self.button(self.input_frame, 'Проверить ответ', self.submit_input, primary=True)
        self.submit_button.grid(row=1, column=0, sticky='ew')
        self.home_frame = tk.Frame(self.answer_area, bg=ui.COLORS['surface'])
        self.start_button = self.button(self.home_frame, 'Начать тест', self.start_test, primary=True,
                                       sound=lambda: self.audio.click('start'))
        self.start_button.pack(fill='x', padx=30)
        self.result_frame = tk.Frame(self.answer_area, bg=ui.COLORS['surface'])
        self.retry_button = self.button(self.result_frame, 'Ещё один тест', self.start_test, primary=True)
        self.retry_button.pack(fill='x', pady=(6, 8))
        self.review_button = self.button(self.result_frame, 'Разбор ответов', self.show_review)
        self.review_button.pack(fill='x')
        self.answer_buttons = []
        self.feedback = self.label(body, '', 12, ui.COLORS['muted'], wraplength=550, justify='center', height=4)
        self.feedback.pack(fill='x', pady=(8, 6))
        self.next_button = self.button(body, 'Продолжить', self.next_question, primary=True)
        self.next_button.pack(fill='x', pady=(0, 8))

    def show_area(self, frame):
        for area in (self.choice_frame, self.input_frame, self.home_frame, self.result_frame):
            area.pack_forget()
        frame.pack(fill='both', expand=True)

    def select_subject(self, subject):
        if self.session is not None:
            return
        self.subject.set(subject)
        self.show_home()

    def select_level(self, level):
        if self.session is not None:
            return
        self.difficulty.set(level)
        self.update_selection()

    def update_selection(self):
        for name, button in self.subject_buttons.items():
            selected = name == self.subject.get()
            button.configure(color=ui.COLORS['selected'] if selected else ui.COLORS['bg'],
                             foreground=SUBJECT_DETAILS[name][1] if selected else ui.COLORS['muted'],
                             state='disabled' if self.session else 'normal')
        for level, button in self.level_buttons.items():
            button.configure(color=ui.COLORS['surface'] if level == self.difficulty.get() else ui.COLORS['bg'],
                             foreground=ui.COLORS['text'] if level == self.difficulty.get() else ui.COLORS['muted'],
                             state='disabled' if self.session else 'normal')

    def resize_canvas(self, event):
        width = max(220, event.width - 24)
        self.canvas.coords(self.problem_text, event.width / 2, 68)
        self.canvas.itemconfigure(self.problem_text, width=width)
        self.feedback.configure(wraplength=width)

    def stop_animation(self):
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        self.canvas.delete('particle')
        self.particles.clear()

    def show_home(self):
        self.stop_animation()
        self.session = None
        self.last_result = None
        self.update_selection()
        subject = self.subject.get()
        _, color, title = SUBJECT_DETAILS[subject]
        self.lesson_title.configure(text=subject.upper(), fg=color)
        self.canvas.itemconfigure(self.problem_text, text=title, fill=ui.COLORS['text'], font=(FONT, 25, 'bold'))
        self.progress.configure(text='')
        self.stats.configure(text='')
        self.bar.configure(value=0, maximum=1)
        self.show_area(self.home_frame)
        self.feedback.configure(text='', fg=ui.COLORS['muted'])
        self.feedback.pack_forget()
        self.answer_area.configure(height=60)
        self.next_button.pack_forget()
        self.menu_button.pack_forget()

    def start_test(self):
        self.stop_animation()
        self.quiz_subject, self.quiz_difficulty = self.subject.get(), self.difficulty.get()
        self.session = Session(make_test(self.quiz_subject, self.quiz_difficulty))
        self.last_result = None
        self.update_selection()
        self.menu_button.configure(state='normal')
        self.menu_button.pack(side='bottom', fill='x', pady=8)
        self.bar.configure(maximum=len(self.session.questions), value=0)
        self.show_question()

    def go_home(self):
        self.show_home()

    def show_question(self):
        self.stop_animation()
        session, question = self.session, self.session.current
        self.lesson_title.configure(text=self.quiz_subject.upper())
        self.canvas.itemconfigure(self.problem_text, text=question.prompt, fill=ui.COLORS['text'], font=(FONT, 21, 'bold'))
        self.progress.configure(text=f'Задание {session.index + 1} из {len(session.questions)}')
        self.update_stats()
        self.answer_area.configure(height=138)
        self.feedback.pack(fill='x', pady=(8, 6))
        self.next_button.configure(state='disabled', text='Дальше')
        self.next_button.pack(fill='x', pady=(0, 8))
        self.feedback.configure(text='', fg=ui.COLORS['muted'])
        self.answer_buttons = []
        if question.typed:
            self.input_var.set('')
            self.entry.configure(state='normal')
            self.submit_button.configure(state='normal')
            self.show_area(self.input_frame)
            self.entry.focus_set()
        else:
            self.answer_buttons = self.all_answer_buttons
            for button, option in zip(self.answer_buttons, question.options):
                button.configure(text=option, color=ui.COLORS['bg'], foreground=ui.COLORS['text'], state='normal')
            self.show_area(self.choice_frame)

    def update_stats(self):
        self.stats.configure(text=f'{self.session.score} очков  ·  Серия {self.session.streak}')

    def submit_choice(self, index):
        if self.session and not self.session.current.typed:
            self.submit(self.session.current.options[index])

    def submit_input(self):
        if not self.input_var.get().strip():
            self.feedback.configure(text='Сначала впиши ответ.', fg=ui.COLORS['error'])
            return
        self.submit(self.input_var.get())

    def submit(self, answer):
        if self.session is None:
            return
        right = self.session.submit(answer)
        if right is None:
            return
        question = self.session.current
        for button, option in zip(self.answer_buttons, question.options):
            color = ui.COLORS['success_bg'] if option == question.answer else ui.COLORS['bg']
            if option == answer and not right:
                color = ui.COLORS['error_bg']
            button.configure(state='disabled', color=color)
        self.entry.configure(state='disabled')
        self.submit_button.configure(state='disabled')
        prefix = 'Правильно. Так держать!' if right else f'Правильный ответ: {question.answer}'
        self.feedback.configure(text=f'{prefix}\n{question.explanation}', fg=ui.COLORS['success'] if right else ui.COLORS['error'])
        self.update_stats()
        self.bar.configure(value=self.session.index + 1)
        self.next_button.configure(state='normal', text='Результат' if self.session.index+1 == len(self.session.questions) else 'Дальше')
        self.next_button.focus_set()
        if right:
            self.spawn_fireworks()

    def on_enter(self, event=None):
        if self.session:
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
        self.stop_animation()
        session = self.session
        self.last_result, self.session = session, None
        self.update_selection()
        total = len(session.questions)
        self.canvas.itemconfigure(self.problem_text, text=f'{session.correct} из {total}\nправильных ответов', fill=ui.COLORS['text'])
        self.progress.configure(text='Тест завершён')
        self.stats.configure(text=f'{session.score} очков')
        self.show_area(self.result_frame)
        self.feedback.configure(text=f'Лучшая серия: {session.best_streak}', fg=ui.COLORS['success'])
        self.next_button.pack_forget()

    def show_review(self, session=None):
        session = session or self.last_result
        if session is None:
            return
        window = tk.Toplevel(self.root)
        window.title('Всезнайка · Разбор ответов')
        window.geometry('720x600')
        window.configure(bg=ui.COLORS['bg'])
        self.label(window, 'Разбор ответов', 24, bold=True).pack(anchor='w', padx=24, pady=20)
        frame = tk.Frame(window, bg=ui.COLORS['surface'])
        frame.pack(fill='both', expand=True, padx=24, pady=(0, 24))
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side='right', fill='y')
        text = tk.Text(frame, wrap='word', bg=ui.COLORS['surface'], fg=ui.COLORS['text'], font=(FONT, 13), relief='flat',
                       padx=20, pady=20, yscrollcommand=scrollbar.set)
        text.pack(fill='both', expand=True)
        scrollbar.configure(command=text.yview)
        text.tag_configure('title', font=(FONT, 14, 'bold'), spacing1=12)
        text.tag_configure('right', foreground=ui.COLORS['success'])
        text.tag_configure('wrong', foreground=ui.COLORS['error'])
        text.tag_configure('explanation', foreground=ui.COLORS['muted'], spacing3=18)
        for i, (question, answer, right) in enumerate(session.history, 1):
            text.insert('end', f'{i}. {question.prompt}\n', 'title')
            text.insert('end', f'{"Верно" if right else "Попробуй запомнить"} · Твой ответ: {answer}\n', 'right' if right else 'wrong')
            text.insert('end', f'Ответ: {question.answer}\n{question.explanation}\n', 'explanation')
        text.configure(state='disabled')

    def toggle_theme(self):
        self.audio.click()
        ui.apply_theme(self.root, self.dark_theme.get())
        self.update_selection()

    def show_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        window = tk.Toplevel(self.root)
        self.settings_window = window
        window.title('Звук')
        window.geometry('360x260')
        window.resizable(False, False)
        window.configure(bg=ui.COLORS['bg'])
        window.transient(self.root)
        self.label(window, 'Звук', 23, bold=True).pack(anchor='w', padx=24, pady=(20, 12))
        if not self.audio.available:
            self.label(window, 'Звук недоступен.\nИгра продолжает работать.', 13, ui.COLORS['muted']).pack(padx=24, pady=20)
            return
        music = tk.BooleanVar(value=not self.audio.music_muted)
        clicks = tk.BooleanVar(value=not self.audio.sfx_muted)
        for label, variable, command in (
            ('Фоновая музыка', music, lambda: self.audio.set_music_muted(not music.get())),
            ('Звуки кнопок', clicks, lambda: setattr(self.audio, 'sfx_muted', not clicks.get()))):
            ttk.Checkbutton(window, text=label, variable=variable, command=command).pack(anchor='w', padx=24, pady=6)
        self.label(window, 'Громкость музыки', 11, ui.COLORS['muted']).pack(anchor='w', padx=24, pady=(12, 0))
        window.volume = tk.DoubleVar(value=self.audio.volume)
        ttk.Scale(window, from_=0, to=1, variable=window.volume, command=self.audio.set_volume).pack(fill='x', padx=24, pady=10)

    def spawn_fireworks(self):
        width = self.canvas.winfo_width()
        for _ in range(20):
            angle, speed = random.uniform(0, math.tau), random.uniform(1, 4)
            x, y = width/2, 68
            particle = self.canvas.create_oval(x-2, y-2, x+2, y+2, tags='particle',
                        fill=random.choice((ui.COLORS['accent'], '#34C759', '#AF52DE', '#FF9F0A')), outline='')
            self.particles.append([particle, math.cos(angle)*speed, math.sin(angle)*speed, 20])
        if self.animation_id is None:
            self.animate()

    def animate(self):
        self.animation_id = None
        if self.closed:
            return
        alive = []
        for particle in self.particles:
            self.canvas.move(particle[0], particle[1], particle[2])
            particle[3] -= 1
            if particle[3] > 0:
                alive.append(particle)
            else:
                self.canvas.delete(particle[0])
        self.particles = alive
        if alive:
            self.animation_id = self.root.after(30, self.animate)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.stop_animation()
        self.audio.close()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    KnowItAllGame(root)
    root.mainloop()
