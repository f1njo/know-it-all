import tkinter as tk
from tkinter import font, ttk

THEMES = {
    False: {'bg': '#F2F2F7', 'surface': '#FFFFFF', 'text': '#1C1C1E', 'muted': '#73737C',
            'accent': '#007AFF', 'border': '#E5E5EA', 'success': '#21834A', 'error': '#C53B35',
            'selected': '#E2EDFF', 'success_bg': '#E5F5EB', 'error_bg': '#FDECEC',
            'disabled': '#E8E8ED', 'on_accent': '#FFFFFF'},
    True: {'bg': '#000000', 'surface': '#1C1C1E', 'text': '#F5F5F7', 'muted': '#A0A0AA',
           'accent': '#0A84FF', 'border': '#38383A', 'success': '#66D58A', 'error': '#FF817B',
           'selected': '#163454', 'success_bg': '#183D28', 'error_bg': '#4A2226',
           'disabled': '#333336', 'on_accent': '#FFFFFF'},
}
COLORS = THEMES[False].copy()
FONT = 'Helvetica Neue'


def rounded_rectangle(canvas, x1, y1, x2, y2, radius, **kwargs):
    radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
    points = (x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
              x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
              x1, y2, x1, y2-radius, x1, y1+radius, x1, y1)
    return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)


class Card(tk.Frame):
    def __init__(self, parent, padding=22, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), **kwargs)
        self.padding = padding
        self.canvas = tk.Canvas(self, bg=self.cget('bg'), highlightthickness=0, height=1)
        self.canvas.pack(fill='both', expand=True)
        self.body = tk.Frame(self.canvas, bg=COLORS['surface'])
        self.window = self.canvas.create_window(padding, padding, anchor='nw', window=self.body)
        self.background = None
        self.canvas.bind('<Configure>', self.resize)
        self.body.bind('<Configure>', self.fit_height)

    def fit_height(self, event):
        height = event.height + 2 * self.padding
        if int(float(self.canvas.cget('height'))) != height:
            self.canvas.configure(height=height)

    def resize(self, event):
        if self.background is not None:
            self.canvas.delete(self.background)
        self.background = rounded_rectangle(self.canvas, 1, 1, event.width-1, event.height-1, 24,
                                            fill=COLORS['surface'], outline=COLORS['border'], width=1)
        self.canvas.tag_lower(self.background)
        self.canvas.itemconfigure(self.window, width=max(1, event.width-2*self.padding))


class Button(tk.Canvas):
    def __init__(self, parent, text, command, color=None, foreground=None,
                 height=48, size=13, sound=None, **kwargs):
        super().__init__(parent, height=height, width=100, bg=parent.cget('bg'),
                         highlightthickness=0, takefocus=True, cursor='hand2', **kwargs)
        self.text = text
        self.command = command
        self.color = COLORS['surface'] if color is None else color
        self.foreground = COLORS['text'] if foreground is None else foreground
        self.state = 'normal'
        self.sound = sound
        self.hovered = False
        self.focused = False
        self.font = font.Font(family=FONT, size=size, weight='bold')
        self.bind('<Configure>', self.paint)
        self.bind('<Enter>', self.enter)
        self.bind('<Leave>', self.leave)
        self.bind('<ButtonRelease-1>', self.click)
        self.bind('<Return>', self.activate)
        self.bind('<space>', self.activate)
        self.bind('<FocusIn>', self.focus_in)
        self.bind('<FocusOut>', self.focus_out)

    def configure(self, cnf=None, **kwargs):
        if isinstance(cnf, dict):
            kwargs.update(cnf)
        changed = False
        for name in ('text', 'command', 'color', 'foreground', 'state', 'sound'):
            if name in kwargs:
                setattr(self, name, kwargs.pop(name))
                if name == 'state':
                    kwargs['takefocus'] = self.state != 'disabled'
                    kwargs['cursor'] = 'arrow' if self.state == 'disabled' else 'hand2'
                changed = True
        result = super().configure(**kwargs) if kwargs else None
        if changed:
            self.paint()
        return result

    config = configure

    def cget(self, key):
        if key in ('text', 'state'):
            return getattr(self, key)
        return super().cget(key)

    def paint(self, event=None):
        self.delete('all')
        width, height = self.winfo_width(), self.winfo_height()
        if width < 5 or height < 5:
            return
        color = COLORS['disabled'] if self.state == 'disabled' and self.color == COLORS['accent'] else self.color
        if self.hovered and self.state != 'disabled':
            rgb = self.winfo_rgb(color)
            color = '#%02x%02x%02x' % tuple(max(0, int(c / 257 * .94)) for c in rgb)
        outline = COLORS['accent'] if self.focused and self.state != 'disabled' else color
        rounded_rectangle(self, 2, 2, width-2, height-2, 14, fill=color, outline=outline, width=2)
        fg = (self.foreground if self.color in (COLORS['success_bg'], COLORS['error_bg']) else COLORS['muted']) if self.state == 'disabled' else self.foreground
        self.create_text(width/2, height/2, text=self.text, fill=fg, font=self.font,
                         width=max(40, width-32), justify='center')

    def invoke(self):
        if self.state != 'disabled':
            if self.sound:
                self.sound()
            if self.command:
                return self.command()

    def click(self, event):
        if 0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height():
            self.focus_set()
            self.invoke()

    def activate(self, event):
        self.invoke()
        return 'break'

    def enter(self, event):
        self.hovered = True
        self.paint()

    def leave(self, event):
        self.hovered = False
        self.paint()

    def focus_in(self, event):
        self.focused = True
        self.paint()

    def focus_out(self, event):
        self.focused = False
        self.paint()


class Progress(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, height=6, bg=parent.cget('bg'), highlightthickness=0)
        self.value, self.maximum = 0, 1
        self.bind('<Configure>', self.paint)

    def configure(self, cnf=None, **kwargs):
        self.value = kwargs.pop('value', self.value)
        self.maximum = kwargs.pop('maximum', self.maximum)
        if kwargs:
            super().configure(**kwargs)
        self.paint()

    def paint(self, event=None):
        self.delete('all')
        width = self.winfo_width()
        rounded_rectangle(self, 0, 0, width, 6, 3, fill=COLORS['border'], outline='')
        filled = width * min(1, max(0, self.value / max(1, self.maximum)))
        if filled >= 6:
            rounded_rectangle(self, 0, 0, filled, 6, 3, fill=COLORS['accent'], outline='')


class Toggle(tk.Canvas):
    def __init__(self, parent, variable, command):
        super().__init__(parent, width=48, height=30, bg=parent.cget('bg'),
                         highlightthickness=0, takefocus=True, cursor='hand2')
        self.variable = variable
        self.command = command
        self.bind('<Configure>', self.paint)
        self.bind('<ButtonRelease-1>', self.activate)
        self.bind('<space>', self.activate)
        self.bind('<Return>', self.activate)
        self.bind('<FocusIn>', self.paint)
        self.bind('<FocusOut>', self.paint)

    def activate(self, event=None):
        self.variable.set(not self.variable.get())
        self.command()
        self.paint()
        return 'break'

    def paint(self, event=None):
        self.delete('all')
        active = self.variable.get()
        outline = COLORS['accent'] if self.focus_get() is self else ''
        rounded_rectangle(self, 2, 2, 46, 28, 13, fill='#34C759' if active else COLORS['border'],
                          outline=outline, width=2)
        x = 33 if active else 15
        self.create_oval(x-10, 5, x+10, 25, fill='#FFFFFF', outline='')


def apply_theme(root, dark):
    old = COLORS.copy()
    COLORS.update(THEMES[bool(dark)])
    mapping = {value: COLORS[key] for key, value in old.items() if key != 'on_accent'}
    mapping[old['surface']] = COLORS['surface']

    def recolor(widget):
        updates = {}
        for key in ('background', 'foreground', 'insertbackground', 'highlightbackground',
                    'highlightcolor', 'selectbackground', 'selectforeground', 'disabledbackground', 'disabledforeground'):
            if key in widget.keys():
                value = str(widget.cget(key))
                if value in mapping:
                    updates[key] = mapping[value]
        if updates:
            widget.configure(**updates)
        if isinstance(widget, Button):
            foreground = COLORS['on_accent'] if widget.color == old['accent'] else mapping.get(widget.foreground, widget.foreground)
            widget.configure(color=mapping.get(widget.color, widget.color), foreground=foreground)
        elif isinstance(widget, (Toggle, Progress)):
            widget.paint()
        elif isinstance(widget, tk.Canvas):
            for item in widget.find_all():
                for key in ('fill', 'outline'):
                    try:
                        value = widget.itemcget(item, key)
                    except tk.TclError:
                        continue
                    if value in mapping:
                        widget.itemconfigure(item, **{key: mapping[value]})
        if isinstance(widget, tk.Text):
            for tag in widget.tag_names():
                value = widget.tag_cget(tag, 'foreground')
                if value in mapping:
                    widget.tag_configure(tag, foreground=mapping[value])
        for child in widget.winfo_children():
            recolor(child)

    recolor(root)
    style = ttk.Style(root)
    style.configure('TCheckbutton', background=COLORS['bg'], foreground=COLORS['text'])
