import tkinter as tk
import random
import math

class MathStarGame:
    def __init__(self, root):
        self.root = root
        self.root.title("⭐ Математический звездопад")
        self.root.geometry("600x680")
        self.root.configure(bg="#1e1e2f")
        self.root.resizable(False, False)

        # Состояние игры
        self.score = 0
        self.streak = 0
        self.max_limit = 10
        self.mode = "mix"  # 'plus', 'minus', 'mix'
        self.current_answer = None
        self.particles = []
        self.is_waiting = False

        self.setup_ui()
        self.next_problem()
        self.animate()

    def setup_ui(self):
        # Панель статистики (Очки и Серия)
        stats_frame = tk.Frame(self.root, bg="#1e1e2f")
        stats_frame.pack(fill="x", padx=25, pady=(15, 5))

        self.score_label = tk.Label(
            stats_frame, text="⭐ Очки: 0", font=("Arial", 16, "bold"),
            fg="#ffd700", bg="#1e1e2f"
        )
        self.score_label.pack(side="left")

        self.streak_label = tk.Label(
            stats_frame, text="🔥 Серия: 0", font=("Arial", 16, "bold"),
            fg="#ff5722", bg="#1e1e2f"
        )
        self.streak_label.pack(side="right")

        # Панель настроек (Сложность и Операция)
        controls_frame = tk.Frame(self.root, bg="#2d2d44", bd=0)
        controls_frame.pack(fill="x", padx=20, pady=10)

        # Выбор сложности
        tk.Label(controls_frame, text="Предел:", font=("Arial", 10, "bold"), fg="#a0a0c0", bg="#2d2d44").pack(side="left", padx=(10, 2))
        for limit in [10, 20, 50]:
            btn = tk.Button(
                controls_frame, text=f"До {limit}", font=("Arial", 9, "bold"),
                bg="#3d3d5c", fg="white", activebackground="#4e4e75", activeforeground="white",
                bd=0, padx=6, pady=3, cursor="hand2",
                command=lambda l=limit: self.set_limit(l)
            )
            btn.pack(side="left", padx=2, pady=6)

        # Выбор режима
        tk.Label(controls_frame, text="Режим:", font=("Arial", 10, "bold"), fg="#a0a0c0", bg="#2d2d44").pack(side="left", padx=(15, 2))
        modes = [("+", "plus"), ("-", "minus"), ("+/-", "mix")]
        for text, m in modes:
            btn = tk.Button(
                controls_frame, text=text, font=("Arial", 9, "bold"),
                bg="#3d3d5c", fg="white", activebackground="#4e4e75", activeforeground="white",
                bd=0, padx=8, pady=3, cursor="hand2",
                command=lambda mode=m: self.set_mode(mode)
            )
            btn.pack(side="left", padx=2, pady=6)

        # Главный холст для математического примера и салюта
        self.canvas = tk.Canvas(self.root, width=560, height=250, bg="#252538", highlightthickness=0)
        self.canvas.pack(padx=20, pady=10)

        # Фоновые звезды
        self.bg_stars = []
        for _ in range(30):
            x = random.randint(10, 550)
            y = random.randint(10, 240)
            size = random.randint(1, 3)
            star_id = self.canvas.create_oval(x, y, x + size, y + size, fill="#555577", outline="")
            self.bg_stars.append(star_id)

        # Текст примера
        self.problem_text = self.canvas.create_text(
            280, 100, text="", font=("Arial", 48, "bold"), fill="#ffffff"
        )

        # Обратная связь (подсказки/поздравления)
        self.feedback_text = self.canvas.create_text(
            280, 185, text="Выбери правильный ответ!", font=("Arial", 15, "bold"), fill="#8a8ab5"
        )

        # Сетка из 4 больших кнопок ответов
        self.buttons_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.buttons_frame.pack(padx=20, pady=10)

        self.ans_buttons = []
        self.btn_colors = ["#4caf50", "#2196f3", "#ff9800", "#9c27b0"]

        for i in range(4):
            row = i // 2
            col = i % 2
            btn = tk.Button(
                self.buttons_frame, text="", font=("Arial", 22, "bold"),
                bg=self.btn_colors[i], fg="white", activebackground="#ffffff",
                width=10, height=2, bd=0, cursor="hand2",
                command=lambda idx=i: self.check_answer(idx)
            )
            btn.grid(row=row, column=col, padx=10, pady=10)
            self.ans_buttons.append(btn)

    def set_limit(self, limit):
        self.max_limit = limit
        self.next_problem()

    def set_mode(self, mode):
        self.mode = mode
        self.next_problem()

    def next_problem(self):
        self.is_waiting = False
        op = self.mode
        if op == "mix":
            op = random.choice(["plus", "minus"])

        if op == "plus":
            a = random.randint(1, self.max_limit - 1)
            b = random.randint(1, self.max_limit - a)
            self.current_answer = a + b
            problem_str = f"{a} + {b} = ?"
        else:
            a = random.randint(2, self.max_limit)
            b = random.randint(1, a)
            self.current_answer = a - b
            problem_str = f"{a} - {b} = ?"

        self.canvas.itemconfig(self.problem_text, text=problem_str)

        # Генерация вариантов ответа
        choices = {self.current_answer}
        while len(choices) < 4:
            offset = random.choice([-3, -2, -1, 1, 2, 3, 4, -4])
            wrong = self.current_answer + offset
            if wrong >= 0 and wrong != self.current_answer:
                choices.add(wrong)

        choices_list = list(choices)
        random.shuffle(choices_list)

        for i, btn in enumerate(self.ans_buttons):
            btn.config(
                text=str(choices_list[i]),
                state="normal",
                bg=self.btn_colors[i],
                fg="white"
            )

    def check_answer(self, btn_idx):
        if self.is_waiting:
            return

        chosen = int(self.ans_buttons[btn_idx]["text"])

        if chosen == self.current_answer:
            self.score += 10 + self.streak * 2
            self.streak += 1
            self.canvas.itemconfig(self.feedback_text, text="✨ Отлично! Правильно! ✨", fill="#00e676")
            self.ans_buttons[btn_idx].config(bg="#00e676")
            self.spawn_fireworks()
        else:
            self.streak = 0
            self.canvas.itemconfig(
                self.feedback_text, 
                text=f"Упс! Правильный ответ: {self.current_answer}", 
                fill="#ff5252"
            )
            self.ans_buttons[btn_idx].config(bg="#ff5252")

        self.score_label.config(text=f"⭐ Очки: {self.score}")
        self.streak_label.config(text=f"🔥 Серия: {self.streak}")

        self.is_waiting = True
        self.root.after(1200, self.next_problem)

    def spawn_fireworks(self):
        """Создает эффект векторного взрыва звездочек при победе"""
        colors = ["#ffd700", "#ff4081", "#00e676", "#00e5ff", "#ff9100"]
        for _ in range(40):
            x = 280
            y = 100
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 10)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            color = random.choice(colors)
            radius = random.randint(3, 7)
            particle = {
                'id': self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline=""),
                'dx': dx,
                'dy': dy,
                'life': random.randint(15, 30)
            }
            self.particles.append(particle)

    def animate(self):
        """Анимационный цикл для частиц и фона"""
        new_particles = []
        for p in self.particles:
            self.canvas.move(p['id'], p['dx'], p['dy'])
            p['life'] -= 1
            if p['life'] > 0:
                new_particles.append(p)
            else:
                self.canvas.delete(p['id'])
        self.particles = new_particles

        # Мерцание звезд на фоне
        if random.random() < 0.2:
            star = random.choice(self.bg_stars)
            colors = ["#ffffff", "#aaaaee", "#555577"]
            self.canvas.itemconfig(star, fill=random.choice(colors))

        self.root.after(30, self.animate)

if __name__ == "__main__":
    root = tk.Tk()
    app = MathStarGame(root)
    root.mainloop()
