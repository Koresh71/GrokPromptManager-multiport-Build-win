import sys, os, platform
IS_WINDOWS = platform.system() == 'Windows'

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

def set_icon_safe(app_obj, icon_path):
    try:
        if IS_WINDOWS:
            app_obj.iconbitmap(resource_path(icon_path))
    except Exception: pass
# --- РАЗДЕЛ 1: ИМПОРТЫ И ПЛАТФОРМОЗАВИСИМЫЕ НАСТРОЙКИ --- #
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import json, os, sys, hashlib, uuid, webbrowser, base64, glob, re, shutil, math, platform, time
import threading, urllib.request, urllib.parse, subprocess

# УМНАЯ ДИАГНОСТИКА ВИДЕО (OPENCV + PYGAME-CE ДЛЯ ЗВУКА)
try:
    import cv2
    from PIL import Image, ImageTk
    import pygame
    HAS_VIDEO = True
    VIDEO_ERROR = ""
except ImportError as e:
    HAS_VIDEO = False
    VIDEO_ERROR = str(e)

# Кроссплатформенный импорт библиотек Windows
if sys.platform == "win32":
    import ctypes
    import winreg
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
        myappid = 'ikdesigns.grokpromptmanager.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except: pass

# --- РАЗДЕЛ 2: СИСТЕМНЫЕ ФУНКЦИИ --- #
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# --- РАЗДЕЛ 3: ТЕХНИЧЕСКИЕ ДАННЫЕ И ЦВЕТОВАЯ СХЕМА --- #
ENCODED_SALT = "R1JPSy1QUk8tS09STklMT1YtVjE="
SECRET_SALT = base64.b64decode(ENCODED_SALT).decode('utf-8')

# Настройки сервера IK Designs
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxCoqjx-fV5a_dLUwTqyK_Jvt8wN9YxznUNZw1gUxGQhvZwOiNnQp6WAgvCS6YYXVN-/exec"
PRODUCT_ID = "GROK"
LICENSE_FILE_NAME = "grok_license.ikd"

BG_MAIN = "#0a0b10"      
BG_PANEL = "#11131a"     
BG_SIDEBAR = "#151821"   
ACCENT_GREEN = "#10b981" 
ACCENT_CYAN = "#00d1ff"  
ACCENT_GOLD = "#ffb800"  
TEXT_WHITE = "#ffffff"
TEXT_MUTED = "#8b949e"
BORDER_GLOW = "#1e293b"
DANGER = "#ef4444"
SUCCESS = "#84cc16"      

# --- РАЗДЕЛ 4: КАСТОМНЫЕ ВИДЖЕТЫ --- #

class IKDVideoPlayer(tk.Canvas):
    def __init__(self, master, video_path, on_finish):
        super().__init__(master, bg="#000000", highlightthickness=0)
        self.video_path = video_path
        self.audio_path = video_path.replace('.mp4', '.mp3')
        self.on_finish = on_finish
        self.playing = False
        self.cap = None
        self.photo = None
        self._canvas_w = 100
        self._canvas_h = 100
        self.has_audio = False
        
        if os.path.exists(self.audio_path):
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(self.audio_path)
                self.has_audio = True
            except: pass

        self.bind("<Configure>", self._on_resize)

    def play(self):
        import cv2
        import time
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            if self.on_finish: self.on_finish()
            return
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0: self.fps = 30
        self.playing = True
        
        if self.has_audio:
            try:
                import pygame
                pygame.mixer.music.play()
            except: pass
            
        self.start_time = time.time()
        self.frame_count = 0
        self._update_frame()

    def _on_resize(self, event):
        self._canvas_w = event.width
        self._canvas_h = event.height

    def _update_frame(self):
        if not self.playing: return
        import cv2
        import time
        from PIL import Image, ImageTk
        
        elapsed = time.time() - self.start_time
        expected_frame = int(elapsed * self.fps)
        
        if self.frame_count > expected_frame:
            delay = int(((self.frame_count / self.fps) - elapsed) * 1000)
            self.after(max(1, delay), self._update_frame)
            return
            
        frames_to_advance = expected_frame - self.frame_count
        ret = True
        
        for _ in range(frames_to_advance - 1):
            ret = self.cap.grab()
            self.frame_count += 1
            if not ret: break
            
        if ret:
            ret, frame = self.cap.read()
            self.frame_count += 1

        if not ret:
            self.stop()
            if self.on_finish: self.on_finish()
            return

        if self._canvas_w > 10 and self._canvas_h > 10:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self._canvas_w, self._canvas_h), interpolation=cv2.INTER_LINEAR)
            img = Image.fromarray(frame)
            self.photo = ImageTk.PhotoImage(image=img)
            self.delete("all")
            self.create_image(0, 0, image=self.photo, anchor="nw")

        self.after(1, self._update_frame)

    def stop(self):
        self.playing = False
        if self.cap:
            self.cap.release()
        if self.has_audio:
            try:
                import pygame
                pygame.mixer.music.stop()
            except: pass

class GlowButton(tk.Canvas):
    def __init__(self, master, text, color, command=None, width=200, height=50, font_size=12, zoom=1.0, is_tab=False, **kwargs):
        self.zoom = zoom
        self.h = int(height * zoom)
        self.req_w = int(width * zoom)
        self.is_tab = is_tab
        super().__init__(master, width=self.req_w, height=self.h+int(24*zoom), bg=master['bg'], highlightthickness=0, cursor="hand2", **kwargs)
        self.command = command
        self.color = color
        self.text = text
        self.font_size = int(font_size * zoom)
        self.hover = False
        self.current_width = self.req_w
        self.is_active = False
        self.pulse_val = 2
        self.pulse_dir = 1
        self.hover_step = 0
        self.hover_dir = 1
        self.tick = 0
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", self._on_resize)
        self._pulse_loop()

    def set_active(self, state):
        self.is_active = state
        self.render()

    def set_text(self, new_text):
        self.text = new_text
        self.render()

    def _on_resize(self, event):
        if event.width > 10:
            self.current_width = event.width
            self.render()
            
    def _pulse_loop(self):
        if not self.winfo_exists(): return
        self.tick += 1
        needs_render = False
        if self.is_active and not self.hover:
            if self.tick % 12 == 0: 
                self.pulse_val += self.pulse_dir
                if self.pulse_val >= 8: self.pulse_dir = -1
                elif self.pulse_val <= 0: self.pulse_dir = 1
                needs_render = True
        if self.hover:
            self.hover_step += self.hover_dir
            if self.hover_step >= 20: self.hover_dir = -1
            elif self.hover_step <= 0: self.hover_dir = 1
            needs_render = True
        if needs_render: self.render()
        self.after(40, self._pulse_loop)

    def _mix_colors(self, c1, c2, ratio):
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 * (1 - ratio) + r2 * ratio)
        g = int(g1 * (1 - ratio) + g2 * ratio)
        b = int(b1 * (1 - ratio) + b2 * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"

    def render(self):
        self.delete("all")
        z = self.zoom
        off = int(12 * z)
        w = self.current_width - off*2
        if w < 10: w = 10
        is_hover = self.hover
        is_active = self.is_active
        render_color = self.color
        if not is_active and is_hover:
            render_color = ACCENT_CYAN if self.is_tab else self.color
        intensity = 8 if is_hover else 3
        if intensity > 3:
            for i in range(intensity, 0, -1):
                self.draw_rounded_rect(off-i, off-i, w+off+i, self.h+off+i, radius=int(12*z), outline=render_color, width=1)
        else:
            self.draw_rounded_rect(off-3, off-3, w+off+3, self.h+off+3, radius=int(11*z), outline=render_color, width=1)
        
        if is_hover:
            ratio = 0.5 + (self.hover_step / 20.0) * 0.5 
            fill_c = self._mix_colors(BG_PANEL, render_color, ratio)
            text_c = BG_MAIN 
        elif is_active:
            ratio = 0.1 + (self.pulse_val / 8.0) * 0.3
            fill_c = self._mix_colors(BG_PANEL, render_color, ratio)
            text_c = render_color
        else:
            fill_c = BG_PANEL if not self.is_tab else BG_SIDEBAR
            text_c = TEXT_WHITE

        self.draw_rounded_rect(off, off, w+off, self.h+off, radius=int(8*z), fill=fill_c, outline=render_color, width=2)
        self.create_text(w/2 + off, self.h/2 + off, text=self.text, fill=text_c, font=("Segoe UI Bold", self.font_size))

    def draw_rounded_rect(self, x1, y1, x2, y2, radius=15, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def _on_click(self, e):
        if self.command: self.command()
    def _on_enter(self, e):
        self.hover = True; self.render()
    def _on_leave(self, e):
        self.hover = False; self.hover_step = 0; self.render()

class FutureArtCanvas(tk.Canvas):
    def __init__(self, master, zoom=1.0, **kwargs):
        super().__init__(master, bg=BG_PANEL, highlightthickness=0, **kwargs)
        self.zoom = zoom
        self.bind("<Configure>", self._on_resize)
        self.image_ref = None 
        self.angle_offset = 0
        self._animate_art()

    def _animate_art(self):
        if not self.winfo_exists(): return
        self.angle_offset += 0.015
        self.render()
        self.after(40, self._animate_art)

    def _on_resize(self, event):
        self.render()

    def render(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10: return
        cx, cy, z = w / 2, h / 2, self.zoom
        has_image, img_y_bottom = False, 0
        try:
            img_path = resource_path("art.png")
            if os.path.exists(img_path):
                if not self.image_ref:
                    img = tk.PhotoImage(file=img_path)
                    if z <= 0.75: img = img.zoom(3).subsample(4)
                    self.image_ref = img
                self.create_image(cx, int(20 * z), image=self.image_ref, anchor="n")
                has_image, img_y_bottom = True, int(20 * z) + self.image_ref.height()
        except: pass
            
        if has_image:
            remaining_h = h - img_y_bottom
            if remaining_h > int(100 * z):
                cy = img_y_bottom + (remaining_h / 2) + int(10 * z)
                scale_mod = 0.95 
            else:
                scale_mod = 0.75; cy = h - int(90 * z)
        else: scale_mod = 1.1 

        max_radius = int(120 * z * scale_mod)
        if max_radius > (w / 2) - 10: scale_mod = scale_mod * ((w / 2 - 10) / max_radius)

        r1, r2, r3 = int(120 * z * scale_mod), int(95 * z * scale_mod), int(65 * z * scale_mod)
        self.create_oval(cx-r1, cy-r1, cx+r1, cy+r1, outline=BORDER_GLOW, width=int(2*z), dash=(int(10*z), int(10*z)))
        self.create_oval(cx-r2, cy-r2, cx+r2, cy+r2, outline=ACCENT_CYAN, width=int(1*z))
        
        points = []
        for i in range(6):
            angle = i * (math.pi / 3) + self.angle_offset
            points.append(cx + math.cos(angle) * r3); points.append(cy + math.sin(angle) * r3)
        
        for i in range(6, 0, -1): self.create_polygon(points, outline=ACCENT_GREEN, fill="", width=1)
        self.create_polygon(points, outline=ACCENT_GREEN, fill=BG_MAIN, width=max(1, int(2*z)))
        
        pulse = math.sin(self.angle_offset * 3) * 5 * z * scale_mod
        r4 = int(15 * z * scale_mod) + pulse
        self.create_oval(cx-r4, cy-r4, cx+r4, cy+r4, fill=ACCENT_GOLD, outline=ACCENT_GOLD)
        
        for i in range(6):
            angle = i * (math.pi / 3) + self.angle_offset
            x1, y1 = cx + math.cos(angle) * r4, cy + math.sin(angle) * r4
            x2, y2 = cx + math.cos(angle) * r3, cy + math.sin(angle) * r3
            self.create_line(x1, y1, x2, y2, fill=ACCENT_GOLD, width=max(1, int(2*z)))
            
        self.create_text(cx, cy+r1+int(35*z*scale_mod), text="GROK AI ENGINE :: ACTIVE", fill=ACCENT_CYAN, font=("Consolas", int(12*z*scale_mod), "bold"))

# --- ФУНКЦИЯ ДЛЯ СКРЫТОГО СБОРА ТЕЛЕМЕТРИИ --- #
def get_telemetry():
    """Собирает ОС, IP, Город и Имя пользователя"""
    try:
        os_info = f"{platform.system()} {platform.release()}"
    except:
        os_info = "Unknown"
        
    try:
        username = os.getlogin()
    except:
        username = "Unknown"
        
    ip, loc = "Unknown", "Unknown"
    try:
        req = urllib.request.Request("http://ip-api.com/json/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
            ip = data.get('query', 'Unknown')
            loc = f"{data.get('country', '')}, {data.get('city', '')}".strip(', ')
    except:
        pass
    return os_info, ip, loc, username

# --- РАЗДЕЛ 5: СТАТИЧЕСКИЕ ТЕКСТОВЫЕ ДАННЫЕ И ЛОКАЛИЗАЦИЯ --- #
INFO_RU = """Как генерировать вирусные ролики в Grok Imagine
Работа с Grok строится на правиле «Бей сразу».
У тебя есть всего несколько секунд, поэтому медленные раскадровки здесь не работают. Следуй этим правилам, чтобы получить максимальный результат:

Шаг 1. Формула идеального старта («Start with...»)
Grok лучше всего работает, когда четко понимает, как выглядит первый кадр. Наши промты всегда начинаются с описания стартовой композиции (например: Start with an extreme macro close-up of a...). Нейросеть сначала «рисует» эту картинку у себя в «голове», а затем приводит ее в движение. Не меняй это начало!

Шаг 2. Правило 6 секунд (The 6-Second Rule)
Помни, что Grok официально генерирует очень короткие видео. Всё действие в промте должно умещаться в этот лимит.

Совет режиссера: Пиши агрессивные глаголы. Не «машина едет», а «машина яростно срывается с места, выбрасывая грязь в линзу» (aggressively spins out, kicking up a massive cloud of mud).

Шаг 3. Задавай движение камеры
В отличие от других сетей, Grok любит динамичную, иногда грязную съемку. Вставляй в промты фразы вроде:
Aggressive camera shake (Агрессивная тряска камеры — для взрывов).
Fast-tracking shot (Быстрое следование).
Subjective POV (Вид от первого лица).

Шаг 4. Не бойся абсурда (Embrace the Weird)
Grok создавался как нейросеть без жестких творческих ограничений (в разумных пределах). Если ты хочешь сгенерировать 50-метрового хомяка, крутящего колесо обозрения в центре Нью-Йорка — просто попроси его об этом. Чем безумнее сочетание несочетаемого, тем круче результат.

Шаг 5. Как использовать нашу базу
Скопируй нужный промт на английском (от слова Start и до конца). Вставь в строку генерации Grok. Если нужно адаптировать идею, просто замени существительные. Например, в промте про «кота-бухгалтера» поменяй grumpy, fat tabby cat на cute golden retriever — и получишь собаку-бухгалтера, сохранив всю остальную идеальную физику сцены."""

INFO_EN = """How to Generate Viral Videos in Grok Imagine
Working with Grok is based on the "Hit Hard" rule.
You only have a few seconds, so slow storyboards don't work here. Follow these rules to get maximum results:

Step 1. The Perfect Start Formula ("Start with...")
Grok works best when it clearly understands what the first frame looks like. Our prompts always begin with a description of the starting composition (e.g., Start with an extreme macro close-up of a...). The AI first "paints" this image in its "mind" and then sets it in motion. Do not change this opening!

Step 2. The 6-Second Rule
Remember that Grok generates very short videos. All action in the prompt must fit within this limit.

Director's Tip: Use aggressive verbs. Instead of "a car is driving," use "a car aggressively spins out, kicking up a massive cloud of mud into the lens".

Step 3. Set the Camera Movement
Unlike other networks, Grok loves dynamic, sometimes gritty cinematography. Insert phrases into your prompts like:
Aggressive camera shake (For explosions).
Fast-tracking shot (Fast tracking).
Subjective POV (First-person view).

Step 4. Embrace the Weird
Grok was created as an AI without rigid creative boundaries (within reasonable limits). If you want to generate a 50-meter hamster spinning a Ferris wheel in the center of New York — just ask for it. The crazier the combination of the mismatched, the better the result.

Step 5. How to Use Our Database
Copy the required prompt in English (from the word Start to the end). Paste it into the Grok generation line. If you need to adapt the idea, simply replace the nouns. For example, in the prompt about the "accountant cat," change "grumpy, fat tabby cat" to "cute golden retriever" — and you'll get an accountant dog while preserving all the other perfect physics of the scene."""

HELP_RU = """📝 ДОБРО ПОЖАЛОВАТЬ В GROK PROMPT MANAGER!

Этот инструмент создан для удобного хранения, редактирования и быстрого использования ваших лучших текстовых запросов (промптов) для нейросети Grok Imagine.

🔍 ПОИСК И НАВИГАЦИЯ
• Используйте выпадающий список в левом меню для фильтрации промптов по категориям.
• Нажмите на название эффекта в списке, чтобы загрузить его в главное окно.
• В левой панели отображаются только названия, чтобы вы могли быстро ориентироваться в базе.

🚀 ИСПОЛЬЗОВАНИЕ БАЗЫ
• В главном окне вы увидите подробное описание и сам промпт (на английском, оптимизированном для Grok).
• Нажмите светящуюся кнопку «КОПИРОВАТЬ ПРОМПТ» — текст автоматически скопируется в буфер обмена компьютера.
• Перейдите в Grok Imagine и вставьте текст (Ctrl+V) для генерации.

⚙️ УПРАВЛЕНИЕ БАЗОЙ (АДМИНКА)
• Перейдите во вкладку «Управление», чтобы добавить свои собственные наработки или отредактировать существующие.
• Чтобы создать новую категорию, нажмите кнопку «+» рядом с выбором категорий.
• Если вы хотите удалить ненужную категорию, выберите её и нажмите «-». Внимание: при этом удалятся и все промпты из этой категории!
• Чтобы создать новый промпт, нажмите «ДОБАВИТЬ НОВЫЙ ПРОМПТ», заполните все поля и нажмите «СОХРАНИТЬ».
• Для изменения существующего промпта просто выберите его в списке, внесите правки и сохраните. Программа умная: она предложит вам выбор — перезаписать старый или сохранить как новый.

💾 ФАЙЛЫ И ДАННЫЕ
• Программа автоматически сканирует свою папку на наличие файлов с расширением *.ikd (например, user_grok_prompts.ikd).
• Все ваши данные надежно зашифрованы и хранятся локально. Вы можете переносить этот файл на другие устройства для синхронизации вашей личной базы."""

HELP_EN = """📝 WELCOME TO GROK PROMPT MANAGER!

This tool is designed to conveniently store, edit, and quickly use your best text queries (prompts) for the Grok Imagine AI.

🔍 SEARCH AND NAVIGATION
• Use the drop-down list in the left menu to filter prompts by categories.
• Click on the effect name in the list to load it into the main window.
• The left panel displays only titles so you can quickly navigate the database.

🚀 USING THE DATABASE
• In the main window, you will see a detailed description and the prompt itself (in English, optimized for Grok).
• Click the glowing "COPY PROMPT" button — the text will automatically be copied to your computer's clipboard.
• Go to Grok Imagine and paste the text (Ctrl+V) to generate.

⚙️ DATABASE MANAGEMENT (ADMIN)
• Go to the "Management" tab to add your own developments or edit existing ones.
• To create a new category, click the "+" button next to the category selection.
• If you want to delete an unnecessary category, select it and click "-". Warning: this will also delete all prompts from this category!
• To create a new prompt, click "ADD NEW PROMPT", fill in all the fields, and click "SAVE".
• To change an existing prompt, simply select it in the list, make edits, and save. The program is smart: it will offer you a choice — overwrite the old one or save it as a new one.

💾 FILES AND DATA
• The program automatically scans its folder for files with the *.ikd extension (e.g., user_grok_prompts.ikd).
• All your data is securely encrypted and stored locally. You can transfer this file to other devices to synchronize your personal database."""

LANG_DATA = {
    "RU": {
        "title": "Grok Prompt Manager", "tab_main": "💻 База Промптов", 
        "tab_admin": "⚙ Управление", 
        "tab_trans": "🌍 Переводчик", 
        "tab_video": "🎬 Генерация", 
        "tab_info": "📖 Информация", "tab_help": "📝 Инструкция", 
        "nav": "🧭 НАВИГАЦИЯ", "all_cats": "Все категории",
        "copy_btn": "🚀 КОПИРОВАТЬ ПРОМПТ", "save_btn": "💾 СОХРАНИТЬ", "del_btn": "🗑 УДАЛИТЬ",
        "add_new": "➕ ДОБАВИТЬ НОВЫЙ ПРОМТ", "cat_label": "1. КАТЕГОРИЯ:", "name_label": "2. НАЗВАНИЕ ЭФФЕКТА:",
        "desc_label": "3. ОПИСАНИЕ:", "prompt_label": "4. ПРОМПТ:", "main_cat_head": "Категория:",
        "main_desc_head": "ОПИСАНИЕ:", "main_prompt_head": "ПРОМПТ:", "lang_btn": "Language: EN", "zoom_btn": "🔍 МАСШТАБ",
        "about_btn": "ℹ О программе", 
        "about_msg": "🧠 Grok Prompt Manager\n\nВерсия: V 1.0\nЛицензия: АКТИВИРОВАНА ✅\nID: {hwid}\nРазработчик: IK Designs\n\nПрограмма предназначена для управления и быстрой генерации промптов для нейросети Grok Imagine. Все права защищены.",
        "confirm_del": "Подтверждение", "ask_del": "Вы уверены, что хотите удалить этот элемент?",
        "copy_ok": "Промпт скопирован!",
        "video_title": "ГЕНЕРАТОР ВИДЕО (SYNTX.AI)",
        "video_desc": "Syntx.ai — это универсальная ИИ-платформа «всё-в-одно», которая объединяет в себе сразу несколько передовых нейросетей.\nОна позволяет не только генерировать крутые видеоролики и изображения по вашим промптам, но и работать с текстом, аудио, сценариями и музыкой в едином интерфейсе.\n\nНажмите на кнопку ниже, чтобы открыть платформу и применить ваши скопированные промпты на практике!",
        "video_btn": "🌐 ОТКРЫТЬ SYNTX", 
        "promo_btn": "🎁 ПРОМОКОД",
        "promo_msg": "Промокод SYNTX-IKDESIGNS успешно скопирован в буфер обмена!\nИспользуйте его при регистрации на Syntx.ai для получения бонусов."
    },
    "EN": {
        "title": "Grok Prompt Manager", "tab_main": "💻 Prompt Database", 
        "tab_admin": "⚙ Manage",
        "tab_trans": "🌍 Translator", 
        "tab_video": "🎬 Generate", 
        "tab_info": "📖 Information", "tab_help": "📝 Instruction", 
        "nav": "🧭 NAVIGATION", "all_cats": "All Categories",
        "copy_btn": "🚀 COPY PROMPT", "save_btn": "💾 SAVE CHANGES", "del_btn": "🗑 DELETE",
        "add_new": "➕ ADD NEW PROMPT", "cat_label": "1. CATEGORY:", "name_label": "2. EFFECT NAME:",
        "desc_label": "3. DESCRIPTION:", "prompt_label": "4. PROMPT:", "main_cat_head": "Category:",
        "main_desc_head": "DESCRIPTION:", "main_prompt_head": "PROMPT:", "lang_btn": "Язык: RU", "zoom_btn": "🔍 ZOOM",
        "about_btn": "ℹ About", 
        "about_msg": "🧠 Grok Prompt Manager\n\nVersion: V 1.0\nLicense: ACTIVATED ✅\nID: {hwid}\nDeveloper: IK Designs\n\nThe program is designed for managing and quickly generating prompts for the Grok Imagine AI. All rights reserved.",
        "confirm_del": "Confirmation", "ask_del": "Are you sure you want to delete this item?",
        "copy_ok": "Copied!",
        "video_title": "VIDEO GENERATOR (SYNTX.AI)",
        "video_desc": "Syntx.ai is a universal all-in-one AI platform that combines multiple cutting-edge neural networks.\nIt allows you not only to generate awesome videos and images from your prompts, but also to work with text, audio, scripts, and music in a single interface.\n\nClick the button below to open the platform and put your copied prompts into practice!",
        "video_btn": "🌐 OPEN SYNTX",
        "promo_btn": "🎁 PROMO CODE",
        "promo_msg": "Promo code SYNTX-IKDESIGNS successfully copied to clipboard!\nUse it when registering on Syntx.ai to receive bonuses."
    }
}

# --- РАЗДЕЛ 6: ОСНОВНОЙ КЛАСС ПРИЛОЖЕНИЯ --- #
class GrokPromptManager:
    def __init__(self, root):
        self.root = root
        self.current_lang = "RU"
        self.zoom_scale = 1.0
        self.root.configure(bg=BG_MAIN)
        
        self.base_dir = get_base_dir()
        self.lic_file = self.get_license_path()
        self.user_data_file = os.path.join(self.base_dir, "user_grok_prompts.ikd")
        
        self.icon_main = resource_path("logo.ico")
        self.icon_ikd = resource_path("ikd_logo.ico")
        self.icon_mac = resource_path("logo.icns")
        
        self.hwid = hashlib.md5(str(uuid.getnode()).encode()).hexdigest()[:12].upper()
        self.prompts, self.categories_data = [], {}
        self.cur_adm_idx = None
        self.style = ttk.Style()
        
        self.set_window_icon()
        self.center_window(1300, 850)
        
        if sys.platform == "win32":
            self.register_ikd_association()

        if not self.check_license():
            self.show_language_selector()
        else:
            self.show_main_interface()
            self.check_periodic_license()

    def save_sync_data(self, pin):
        try:
            sync_file = self.lic_file.replace(LICENSE_FILE_NAME, "sync.ikd")
            data = {"pin": pin, "time": time.time()}
            with open(sync_file, "wb") as f:
                f.write(base64.b64encode(self.xor_cipher(json.dumps(data).encode('utf-8'))))
        except: pass

    def check_periodic_license(self):
        sync_file = self.lic_file.replace(LICENSE_FILE_NAME, "sync.ikd")
        if not os.path.exists(sync_file): return
        try:
            with open(sync_file, "rb") as f:
                data = json.loads(self.xor_cipher(base64.b64decode(f.read())).decode('utf-8'))
            last_time = data.get("time", 0)
            saved_pin = data.get("pin", "")
            if time.time() - last_time > 1209600:
                threading.Thread(target=self.bg_verify, args=(saved_pin,), daemon=True).start()
        except: pass

    def bg_verify(self, pin):
        try:
            params = urllib.parse.urlencode({'hwid': self.hwid, 'pin': pin, 'product': PRODUCT_ID}).encode()
            req = urllib.request.Request(GOOGLE_SCRIPT_URL, data=params, method='POST')
            with urllib.request.urlopen(req, timeout=10) as r:
                res = json.loads(r.read().decode('utf-8'))
                if res.get("success"):
                    self.save_sync_data(pin) 
                else:
                    if os.path.exists(self.lic_file): os.remove(self.lic_file)
                    sync_file = self.lic_file.replace(LICENSE_FILE_NAME, "sync.ikd")
                    if os.path.exists(sync_file): os.remove(sync_file)
                    os._exit(0) 
        except: pass 

    def get_license_path(self):
        if getattr(sys, 'frozen', False):
            appdata = os.environ.get('APPDATA')
            path = os.path.join(appdata, "IK Designs", "Grok Prompt Manager")
            os.makedirs(path, exist_ok=True)
            return os.path.join(path, LICENSE_FILE_NAME)
        else:
            return os.path.join(self.base_dir, LICENSE_FILE_NAME)

    def set_window_icon(self):
        try:
            if sys.platform == "win32" and os.path.exists(self.icon_main):
                set_icon_safe(self.root, "logo.ico")
            elif sys.platform == "darwin" and os.path.exists(self.icon_mac):
                img = tk.Image("photo", file=self.icon_mac)
                self.root.tk.call('wm', 'iconphoto', self.root._w, img)
        except: pass

    def register_ikd_association(self):
        if sys.platform != "win32": return
        try:
            prog_id = "IKDesigns.IKDFile"
            desired_name = "Файл данных IK Designs"
            
            appdata_path = os.environ.get('APPDATA')
            ikd_dir = os.path.join(appdata_path, "IK Designs")
            os.makedirs(ikd_dir, exist_ok=True)
            target_icon_path = os.path.join(ikd_dir, "ikd_file_icon.ico")
            
            if not os.path.exists(target_icon_path) and os.path.exists(self.icon_ikd):
                shutil.copy2(self.icon_ikd, target_icon_path)

            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}") as key:
                    current_val, _ = winreg.QueryValueEx(key, "")
                    if current_val == desired_name: return
            except: pass

            exe_path = f'"{sys.executable}"'
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.ikd") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, prog_id)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, desired_name)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}\DefaultIcon") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{target_icon_path}"')
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}\shell\open\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'{exe_path} "%1"')
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        except: pass

    def center_window(self, w, h):
        width, height = int(w * self.zoom_scale), int(h * self.zoom_scale)
        if not hasattr(self, 'window_centered'):
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            x, y = (sw // 2) - (width // 2), (sh // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            self.window_centered = True
        else:
            self.root.geometry(f"{width}x{height}")

    def apply_base_style(self):
        s = self.zoom_scale
        f_main = int(16 * s)
        self.style.theme_use('default')
        self.style.layout('TNotebook.Tab', [])
        self.style.configure('TNotebook', background=BG_MAIN, borderwidth=0)
        self.style.configure('TNotebook.Tab', padding=[20, 10], font=("Segoe UI Bold", 11))
        self.style.configure('TCombobox', font=('Segoe UI', f_main))

    def apply_zoom(self, scale):
        self.zoom_scale = scale
        try: current_tab = self.nb.index(self.nb.select())
        except: current_tab = 0
        self.show_main_interface(tab_index=current_tab)

    def check_license(self):
        if not os.path.exists(self.lic_file): return False
        try:
            with open(self.lic_file, "r") as f:
                saved_key = f.read().strip()
                hash_res = hashlib.sha256((self.hwid + SECRET_SALT).encode()).hexdigest().upper()
                expected = f"{hash_res[0:6]}-{hash_res[6:12]}-{hash_res[12:18]}"
                return saved_key == expected
        except: return False

    def xor_cipher(self, data):
        key = SECRET_SALT
        return bytes([b ^ ord(key[i % len(key)]) for i, b in enumerate(data)])

    def encrypt_data(self, data):
        return base64.b64encode(self.xor_cipher(json.dumps(data, ensure_ascii=False).encode('utf-8')))

    def decrypt_data(self, encrypted):
        try: return json.loads(self.xor_cipher(base64.b64decode(encrypted)).decode('utf-8'))
        except: return []

    def get_cat_display(self, cat_ru):
        val = self.categories_data.get(cat_ru, cat_ru)
        return self.get_loc_text(val) if self.current_lang == "EN" else self.get_loc_text(cat_ru)

    def get_loc_text(self, text):
        if not text or not isinstance(text, str): return ""
        text = text.strip()
        cleaned = re.sub(r'^\d+[\.\)\-]\s*', '', text)
        if cleaned: text = cleaned
        start_idx = text.rfind('(')
        if start_idx != -1 and text.endswith(')'):
            p1, p2 = text[:start_idx].strip(), text[start_idx+1:-1].strip()
            if bool(re.search('[а-яА-ЯёЁ]', p2)) and not bool(re.search('[а-яА-ЯёЁ]', p1)): ru, en = p2, p1
            else: ru, en = p1, p2
            return en if self.current_lang == "EN" else ru
        return text

    def init_database(self):
        for json_file in glob.glob(os.path.join(self.base_dir, "*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f: data = json.load(f)
                counter = 1
                while os.path.exists(os.path.join(self.base_dir, f"{counter}_user_grok_prompts.ikd")): counter += 1
                new_ikd_path = os.path.join(self.base_dir, f"{counter}_user_grok_prompts.ikd")
                with open(new_ikd_path, 'wb') as f: f.write(self.encrypt_data(data))
                os.remove(json_file)
            except: pass

        self.prompts, self.categories_data = [], {}
        all_dat_files = [f for f in os.listdir(self.base_dir) if f.endswith(".ikd") and "grok_prompts" in f]
        for f_name in all_dat_files:
            file_path = os.path.join(self.base_dir, f_name)
            try:
                with open(file_path, 'rb') as f:
                    batch = self.decrypt_data(f.read())
                source_type = "user" if "user" in f_name else "system"
                for item in batch:
                    item["_source"] = source_type
                    self.prompts.append(item)
                    ru_cat = item.get("category", "Общее")
                    self.categories_data[ru_cat] = item.get("category_en", ru_cat)
            except: pass
        if not self.categories_data: self.categories_data["Общее"] = "General"

    def show_main_interface(self, tab_index=0):
        s = self.zoom_scale
        for w in self.root.winfo_children(): w.destroy()
        self.init_database()
        
        self.center_window(1300, 850)
        self.apply_base_style()
        l = LANG_DATA[self.current_lang]
        self.root.title(l["title"])

        header = tk.Frame(self.root, bg=BG_MAIN, pady=int(10*s)); header.pack(fill="x")
        tk.Label(header, text="🧠 Grok Prompt Manager", font=("Segoe UI Black", int(26*s)), bg=BG_MAIN, fg=ACCENT_GREEN).pack(side="left", padx=int(30*s))
        
        self.btn_about = GlowButton(header, text=l["about_btn"], color=ACCENT_CYAN, command=lambda: messagebox.showinfo(l["about_btn"], l["about_msg"].format(hwid=self.hwid)), width=160, height=35, font_size=10, zoom=s)
        self.btn_about.pack(side="right", padx=int(10*s))
        
        self.btn_lang = GlowButton(header, text=l["lang_btn"], color=ACCENT_GREEN, command=self.toggle_lang, width=160, height=35, font_size=10, zoom=s)
        self.btn_lang.pack(side="right", padx=int(5*s))
        
        zm = tk.Menubutton(header, text=l["zoom_btn"], bg=BG_PANEL, fg="white", font=("Segoe UI Bold", int(10*s)), relief="flat", padx=10)
        zm.menu = tk.Menu(zm, tearoff=0, bg=BG_PANEL, fg="white", font=("Segoe UI", 12))
        zm["menu"] = zm.menu
        for v in [1.0, 0.75, 0.5]: zm.menu.add_command(label=f"{int(v*100)}%", command=lambda val=v: self.apply_zoom(val))
        zm.pack(side="right", padx=int(5*s))

        nav_bar = tk.Frame(self.root, bg=BG_MAIN)
        nav_bar.pack(fill="x", padx=int(25*s), pady=int(5*s))
        
        tabs_info = [(0, l["tab_main"]), (1, l["tab_admin"]), (2, l["tab_trans"]), (3, l["tab_video"]), (4, l["tab_info"]), (5, l["tab_help"])]
        self.tab_buttons = []
        for idx, name in tabs_info:
            is_active = (idx == tab_index)
            btn_color = ACCENT_GOLD if is_active else BORDER_GLOW
            btn = GlowButton(nav_bar, text=name, color=btn_color, command=lambda i=idx: self.switch_tab(i), width=190, height=45, font_size=12, zoom=s, is_tab=True)
            btn.pack(side="left", padx=5)
            btn.set_active(is_active)
            self.tab_buttons.append(btn)

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=int(15*s), pady=int(10*s))
        t1, t2, t3, t4, t5, t6 = [tk.Frame(self.nb, bg=BG_MAIN) for _ in range(6)]
        self.nb.add(t1, text="1"); self.nb.add(t2, text="2"); self.nb.add(t3, text="3")
        self.nb.add(t4, text="4"); self.nb.add(t5, text="5"); self.nb.add(t6, text="6")
        
        off_p = int(12*s)

        # --- TAB 1: БАЗА ПРОМПТОВ ---
        left = tk.Frame(t1, bg=BG_SIDEBAR, width=int(300*s)); left.pack(side="left", fill="y", pady=int(10*s)); left.pack_propagate(False)
        tk.Label(left, text=l["nav"], font=("Segoe UI Bold", int(14*s)), bg=BG_PANEL, fg=TEXT_WHITE).pack(fill="x", pady=(0, int(10*s)), ipady=int(18*s))
        self.cat_var = tk.StringVar(value=l["all_cats"])
        self.main_cb = ttk.Combobox(left, textvariable=self.cat_var, state="readonly", font=("Segoe UI Bold", int(14*s)), justify="center")
        self.main_cb.pack(fill="x", padx=int(10*s), pady=(0, int(10*s)), ipady=int(12*s)); self.main_cb.bind("<<ComboboxSelected>>", lambda e: self.update_list())
        self.main_cb['values'] = [l["all_cats"]] + sorted([self.get_cat_display(c) for c in self.categories_data.keys()])

        lb_f1 = tk.Frame(left, bg=BG_SIDEBAR); lb_f1.pack(fill="both", expand=True)
        sb1 = tk.Scrollbar(lb_f1); sb1.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(lb_f1, bg=BG_SIDEBAR, fg=TEXT_WHITE, bd=0, font=("Segoe UI Bold", int(15*s)), selectbackground=ACCENT_GOLD, selectforeground="#000000", highlightthickness=0, yscrollcommand=sb1.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb1.config(command=self.listbox.yview); self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
        tk.Frame(t1, bg=BORDER_GLOW, width=int(2*s)).pack(side="left", fill="y", padx=int(10*s), pady=int(10*s))

        right = tk.Frame(t1, bg=BG_MAIN, padx=int(15*s)); right.pack(side="right", fill="both", expand=True, pady=int(10*s))
        
        self.btn_copy = GlowButton(right, text=l["copy_btn"], color=ACCENT_CYAN, command=self.copy_p, font_size=18, width=400, height=60, zoom=s) 
        self.btn_copy.pack(side="bottom", fill="x", pady=(int(10*s), 0))
        
        header_f = tk.Frame(right, bg=BG_MAIN)
        header_f.pack(fill="x", padx=off_p, pady=(0, int(10*s)))
        
        text_f = tk.Frame(header_f, bg=BG_MAIN)
        text_f.pack(side="left", fill="both", expand=True, anchor="n")
        
        self.lbl_p_n = tk.Label(text_f, text="", font=("Segoe UI Black", int(28*s)), bg=BG_MAIN, fg=ACCENT_GOLD, anchor="nw", wraplength=int(650*s))
        self.lbl_p_n.pack(fill="x", pady=(0, int(5*s)))
        
        self.lbl_main_cat = tk.Label(text_f, text="", font=("Segoe UI Bold", int(12*s)), bg=BG_MAIN, fg=ACCENT_CYAN, anchor="w")
        self.lbl_main_cat.pack(fill="x")
        
        self.lbl_logo = tk.Label(header_f, bg=BG_MAIN)
        self.lbl_logo.pack(side="right", anchor="n", padx=(int(10*s), 0), pady=(int(8*s), 0))
        
        try:
            logo_path = resource_path("logo.png")
            if os.path.exists(logo_path):
                img = tk.PhotoImage(file=logo_path)
                if s <= 0.75:
                    img = img.zoom(3).subsample(4)
                self.main_logo_img = img
                self.lbl_logo.config(image=self.main_logo_img)
        except: pass
        
        tk.Label(right, text=l["main_desc_head"], font=("Segoe UI Bold", int(10*s)), bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w", padx=off_p)
        self.txt_desc_main = tk.Text(right, bg=BG_PANEL, fg=TEXT_WHITE, font=("Segoe UI", int(14*s)), bd=0, wrap="word", height=4, state="disabled", highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_CYAN)
        self.txt_desc_main.pack(fill="x", padx=off_p, pady=(int(5*s), int(15*s)))
        
        tk.Label(right, text=l["main_prompt_head"], font=("Segoe UI Bold", int(10*s)), bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w", padx=off_p)
        self.txt_p_main = scrolledtext.ScrolledText(right, bg="#000000", fg=TEXT_WHITE, font=("Consolas", int(15*s)), bd=0, padx=int(15*s), pady=int(15*s), state="disabled", highlightthickness=2, highlightbackground=ACCENT_CYAN, highlightcolor=ACCENT_CYAN, height=18)
        self.txt_p_main.pack(fill="both", expand=True, padx=off_p)

        # --- TAB 2: УПРАВЛЕНИЕ (Админка) ---
        f2 = tk.Frame(t2, bg=BG_MAIN, padx=20, pady=10); f2.pack(fill="both", expand=True)
        la = tk.Frame(f2, bg=BG_SIDEBAR, width=int(300*s)); la.pack(side="left", fill="y"); la.pack_propagate(False)
        self.afv = tk.StringVar(value=l["all_cats"])
        self.afc = ttk.Combobox(la, textvariable=self.afv, state="readonly", font=("Segoe UI Bold", int(14*s)), justify="center")
        self.afc.pack(fill="x", padx=int(10*s), pady=int(15*s), ipady=int(12*s)); self.afc.bind("<<ComboboxSelected>>", lambda e: self.update_admin_list())
        self.afc['values'] = self.main_cb['values']

        lb_f2 = tk.Frame(la, bg=BG_SIDEBAR); lb_f2.pack(fill="both", expand=True)
        sb2 = tk.Scrollbar(lb_f2); sb2.pack(side="right", fill="y")
        self.alb = tk.Listbox(lb_f2, bg=BG_SIDEBAR, fg="white", bd=0, font=("Segoe UI Bold", int(15*s)), selectbackground=ACCENT_GOLD, selectforeground="#000000", highlightthickness=0, yscrollcommand=sb2.set)
        self.alb.pack(side="left", fill="both", expand=True)
        sb2.config(command=self.alb.yview); self.alb.bind("<<ListboxSelect>>", self.on_admin_select)
        
        tk.Frame(f2, bg=BORDER_GLOW, width=int(2*s)).pack(side="left", fill="y", padx=int(10*s))

        ra = tk.Frame(f2, bg=BG_MAIN, padx=int(10*s)); ra.pack(side="right", fill="both", expand=True)
        
        btn_container = tk.Frame(ra, bg=BG_MAIN)
        btn_container.pack(side="bottom", fill="x", pady=(int(10*s), 0))
        
        self.b_d = GlowButton(btn_container, text=l["del_btn"], color=DANGER, font_size=14, width=300, height=50, zoom=s, command=self.del_adm) 
        self.b_d.pack(side="left", fill="x", expand=True, padx=(0, int(10*s)))
        
        self.b_s = GlowButton(btn_container, text=l["save_btn"], color=SUCCESS, font_size=14, width=300, height=50, zoom=s, command=self.save_adm)
        self.b_s.pack(side="right", fill="x", expand=True, padx=(int(10*s), 0))
        
        tk.Label(ra, text=l["cat_label"], bg=BG_MAIN, fg=TEXT_WHITE, font=("Segoe UI Bold", int(14*s))).pack(anchor="w", padx=off_p)
        cl = tk.Frame(ra, bg=BG_MAIN); cl.pack(fill="x", pady=2, padx=off_p)
        self.ecc = ttk.Combobox(cl, state="readonly", font=("Segoe UI Bold", int(16*s))); self.ecc.pack(side="left", fill="x", expand=True, ipady=int(10*s))
        self.ecc['values'] = sorted([self.get_cat_display(c) for c in self.categories_data.keys()])
        
        self.b_add_c = GlowButton(cl, text="+", color=SUCCESS, width=50, height=40, font_size=18, zoom=s, command=self.add_cat)
        self.b_add_c.pack(side="left", padx=int(5*s))
        self.b_del_c = GlowButton(cl, text="-", color=DANGER, width=50, height=40, font_size=18, zoom=s, command=self.del_cat)
        self.b_del_c.pack(side="left")
        
        self.b_new = GlowButton(ra, text=l["add_new"], color=ACCENT_CYAN, font_size=13, width=350, height=40, zoom=s, command=self.clear_adm)
        self.b_new.pack(fill="x", pady=(int(8*s), int(10*s)))
        
        tk.Label(ra, text=l["name_label"], bg=BG_MAIN, fg=TEXT_WHITE, font=("Segoe UI Bold", int(14*s))).pack(anchor="w", padx=off_p)
        self.a_en = tk.Entry(ra, font=("Segoe UI Bold", int(15*s)), bg=BG_PANEL, fg="white", bd=0, insertbackground="white", highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_GOLD)
        self.a_en.pack(fill="x", pady=2, ipady=int(12*s), padx=off_p)
        
        tk.Label(ra, text=l["desc_label"], bg=BG_MAIN, fg=TEXT_WHITE, font=("Segoe UI Bold", int(14*s))).pack(anchor="w", padx=off_p)
        self.a_rd = tk.Text(ra, height=3, font=("Segoe UI Semibold", int(14*s)), bg=BG_PANEL, fg="white", bd=0, insertbackground="white", wrap="word", highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_GOLD)
        self.a_rd.pack(fill="x", pady=2, padx=off_p)
        
        tk.Label(ra, text=l["prompt_label"], bg=BG_MAIN, fg=TEXT_WHITE, font=("Segoe UI Bold", int(14*s))).pack(anchor="w", padx=off_p)
        self.a_tp = scrolledtext.ScrolledText(ra, height=20, font=("Consolas Bold", int(14*s)), bg="#000", fg=ACCENT_CYAN, bd=0, insertbackground="white", highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_CYAN)
        self.a_tp.pack(fill="both", expand=True, pady=2, padx=off_p)

        # --- TAB 3: ПЕРЕВОДЧИК ОНЛАЙН ---
        self.trans_langs_ru = {
            "Автоопределение": "auto", "Русский": "ru", "Английский": "en", 
            "Испанский": "es", "Немецкий": "de", "Французский": "fr", 
            "Китайский": "zh-CN", "Японский": "ja", "Итальянский": "it", 
            "Корейский": "ko", "Польский": "pl", "Турецкий": "tr", 
            "Арабский": "ar", "Хинди": "hi"
        }
        self.trans_langs_en = {
            "Auto Detect": "auto", "Russian": "ru", "English": "en", 
            "Spanish": "es", "German": "de", "French": "fr", 
            "Chinese": "zh-CN", "Japanese": "ja", "Italian": "it", 
            "Korean": "ko", "Polish": "pl", "Turkish": "tr", 
            "Arabic": "ar", "Hindi": "hi"
        }
        self.current_trans_langs = self.trans_langs_ru if self.current_lang == "RU" else self.trans_langs_en
        lang_names = list(self.current_trans_langs.keys())

        trans_container = tk.Frame(t3, bg=BG_MAIN)
        trans_container.pack(fill="both", expand=True, padx=int(15*s), pady=int(10*s))
        
        tk.Label(trans_container, text="🌍 ОНЛАЙН ПЕРЕВОДЧИК" if self.current_lang == "RU" else "🌍 ONLINE TRANSLATOR", font=("Segoe UI Black", int(20*s)), bg=BG_MAIN, fg=ACCENT_CYAN).pack(pady=(0, int(10*s)))
        
        btn_f_tr = tk.Frame(trans_container, bg=BG_MAIN)
        btn_f_tr.pack(side="bottom", pady=int(10*s))
        
        btn_swap = GlowButton(btn_f_tr, text="⇄", color=ACCENT_CYAN, command=self.swap_langs, font_size=20, width=80, height=50, zoom=s)
        btn_swap.pack(side="left", padx=int(10*s))
        
        btn_tr_main = GlowButton(btn_f_tr, text="ПЕРЕВЕСТИ / TRANSLATE", color=SUCCESS, command=self.do_translate, font_size=14, width=400, height=50, zoom=s)
        btn_tr_main.pack(side="left", padx=int(10*s))

        trans_content = tk.Frame(trans_container, bg=BG_MAIN)
        trans_content.pack(side="top", fill="both", expand=True)

        left_f = tk.Frame(trans_content, bg=BG_MAIN)
        left_f.place(relx=0.0, rely=0.0, relwidth=0.48, relheight=1.0)
        
        top_l = tk.Frame(left_f, bg=BG_MAIN)
        top_l.pack(fill="x", pady=(0, int(5*s)))
        
        self.cb_src = ttk.Combobox(top_l, values=lang_names, state="readonly", font=("Segoe UI Bold", int(12*s)))
        self.cb_src.set(lang_names[0]) 
        self.cb_src.pack(side="left")
        
        tk.Button(top_l, text="📋 ВСТАВИТЬ / PASTE", bg=BG_PANEL, fg=TEXT_WHITE, font=("Segoe UI Bold", int(10*s)), bd=0, cursor="hand2", command=self.paste_trans_src).pack(side="right")
        
        self.txt_trans_src = scrolledtext.ScrolledText(left_f, bg=BG_PANEL, fg=TEXT_WHITE, font=("Consolas", int(14*s)), bd=0, insertbackground="white", insertwidth=3, highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_CYAN)
        self.txt_trans_src.pack(fill="both", expand=True)

        right_f = tk.Frame(trans_content, bg=BG_MAIN)
        right_f.place(relx=0.52, rely=0.0, relwidth=0.48, relheight=1.0)
        
        top_r = tk.Frame(right_f, bg=BG_MAIN)
        top_r.pack(fill="x", pady=(0, int(5*s)))
        
        self.cb_tgt = ttk.Combobox(top_r, values=lang_names[1:], state="readonly", font=("Segoe UI Bold", int(12*s)))
        self.cb_tgt.set(lang_names[2]) 
        self.cb_tgt.pack(side="left")
        
        tk.Button(top_r, text="📋 КОПИРОВАТЬ / COPY", bg=BG_PANEL, fg=TEXT_WHITE, font=("Segoe UI Bold", int(10*s)), bd=0, cursor="hand2", command=self.copy_trans_tgt).pack(side="right")
        
        self.txt_trans_tgt = scrolledtext.ScrolledText(right_f, bg=BG_PANEL, fg=ACCENT_GREEN, font=("Consolas", int(14*s)), bd=0, insertbackground="white", highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_CYAN)
        self.txt_trans_tgt.pack(fill="both", expand=True)

        # --- TAB 4: ЛАУНЧПАД ГЕНЕРАЦИИ ВИДЕО ---
        video_container = tk.Frame(t4, bg=BG_MAIN)
        video_container.place(relx=0.5, rely=0.45, anchor="center") 
        
        tk.Label(video_container, text=l["video_title"], font=("Segoe UI Black", int(28*s)), bg=BG_MAIN, fg=ACCENT_CYAN).pack(pady=(0, int(15*s)))
        
        txt_desc = tk.Label(video_container, text=l["video_desc"], font=("Segoe UI Semibold", int(14*s)), bg=BG_MAIN, fg=TEXT_WHITE, justify="center", wraplength=int(800*s))
        txt_desc.pack(pady=(0, int(20*s)))
        
        btn_launch = GlowButton(video_container, text=l["video_btn"], color=SUCCESS, command=lambda: webbrowser.open("https://syntx.ai/"), font_size=16, width=400, height=60, zoom=s)
        btn_launch.pack(pady=int(10*s))
        
        btn_promo = GlowButton(video_container, text=l["promo_btn"], color=ACCENT_GOLD, command=self.copy_promo, font_size=13, width=300, height=45, zoom=s)
        btn_promo.pack(pady=int(10*s))

        # --- TAB 5: ИНФОРМАЦИЯ ---
        info_content = INFO_RU if self.current_lang == "RU" else INFO_EN
        clean_info = re.sub(r'\s*#\s*\d+$', '', info_content, flags=re.MULTILINE)
        st_info = scrolledtext.ScrolledText(t5, font=("Segoe UI Semibold", int(15*s)), bg=BG_PANEL, fg=TEXT_WHITE, bd=0, padx=int(45*s), pady=int(45*s), wrap="word", highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_CYAN)
        st_info.pack(fill="both", expand=True, padx=int(15*s), pady=int(15*s))
        st_info.insert("1.0", clean_info)
        st_info.config(state="disabled")

        # --- TAB 6: ИНСТРУКЦИЯ ---
        help_container = tk.Frame(t6, bg=BG_MAIN)
        help_container.pack(fill="both", expand=True, padx=int(15*s), pady=int(15*s))

        help_content = HELP_RU if self.current_lang == "RU" else HELP_EN
        clean_help = re.sub(r'\s*#\s*\d+$', '', help_content, flags=re.MULTILINE)
        
        art_frame = tk.Frame(help_container, bg=BG_PANEL, width=int(320*s), highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_CYAN)
        art_frame.pack(side="right", fill="y")
        art_frame.pack_propagate(False)

        art_canvas = FutureArtCanvas(art_frame, zoom=s)
        art_canvas.pack(fill="both", expand=True)

        st_help = scrolledtext.ScrolledText(help_container, font=("Segoe UI Semibold", int(14*s)), bg=BG_PANEL, fg=TEXT_WHITE, bd=0, padx=int(30*s), pady=int(30*s), wrap="word", highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_CYAN)
        st_help.pack(side="left", fill="both", expand=True, padx=(0, int(15*s)))
        st_help.insert("1.0", clean_help)
        st_help.config(state="disabled")
            
        self.nb.select(tab_index)
        self.update_list()

    def paste_trans_src(self):
        try:
            self.txt_trans_src.delete("1.0", tk.END)
            self.txt_trans_src.insert("1.0", self.root.clipboard_get())
        except: pass

    def copy_trans_tgt(self):
        txt = self.txt_trans_tgt.get("1.0", tk.END).strip()
        if txt and not txt.startswith("Перевод..."):
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            messagebox.showinfo("IKD", "Текст скопирован!" if self.current_lang == "RU" else "Copied!")

    def swap_langs(self):
        src = self.cb_src.get()
        tgt = self.cb_tgt.get()
        
        if src != "Автоопределение" and src != "Auto Detect":
            self.cb_src.set(tgt)
            self.cb_tgt.set(src)
            
        src_text = self.txt_trans_src.get("1.0", tk.END).strip()
        tgt_text = self.txt_trans_tgt.get("1.0", tk.END).strip()
        
        self.txt_trans_src.delete("1.0", tk.END)
        if tgt_text and not tgt_text.startswith("Перевод..."):
            self.txt_trans_src.insert("1.0", tgt_text)
            
        self.txt_trans_tgt.delete("1.0", tk.END)
        if src_text:
            self.txt_trans_tgt.insert("1.0", src_text)

    def do_translate(self):
        sl_name = self.cb_src.get()
        tl_name = self.cb_tgt.get()
        sl = self.current_trans_langs.get(sl_name, 'auto')
        tl = self.current_trans_langs.get(tl_name, 'en')
        
        src_txt = self.txt_trans_src.get("1.0", tk.END).strip()
        if not src_txt: return
        
        self.txt_trans_tgt.delete("1.0", tk.END)
        self.txt_trans_tgt.insert("1.0", "Перевод... Пожалуйста, подождите..." if self.current_lang == "RU" else "Translating... Please wait...")
        self.root.update()
        
        def fetch_translation():
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={tl}&dt=t&q={urllib.parse.quote(src_txt)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    res = ''.join([part[0] for part in data[0] if part[0]])
            except Exception as e:
                res = f"Ошибка сети / Network error: Проверьте подключение к интернету.\n({e})"
            
            # ИСПРАВЛЕНО: Безопасная передача текста без удаления переменных
            self.root.after(0, lambda text=res: (self.txt_trans_tgt.delete("1.0", tk.END), self.txt_trans_tgt.insert("1.0", text)))

        threading.Thread(target=fetch_translation, daemon=True).start()

    def copy_promo(self):
        self.root.clipboard_clear()
        self.root.clipboard_append("SYNTX-IKDESIGNS")
        messagebox.showinfo("IKD", LANG_DATA[self.current_lang]["promo_msg"])

    def switch_tab(self, idx):
        self.show_main_interface(tab_index=idx)

    def toggle_lang(self):
        self.current_lang = "EN" if self.current_lang == "RU" else "RU"
        self.show_main_interface()

    def update_list(self):
        self.listbox.delete(0, tk.END); self.cur_map = []
        sel, all_l = self.cat_var.get(), LANG_DATA[self.current_lang]["all_cats"]
        for i, p in enumerate(self.prompts):
            c_disp = self.get_cat_display(p.get('category', 'Общее'))
            if sel == all_l or c_disp == sel:
                self.listbox.insert(tk.END, f"  {self.get_loc_text(p['name'])}") 
                self.cur_map.append(i)

    def on_select(self, e):
        if not self.listbox.curselection(): return
        item = self.prompts[self.cur_map[self.listbox.curselection()[0]]]
        self.lbl_p_n.config(text=self.get_loc_text(item.get('name', ''))) 
        
        c_val = item.get('category', 'Общее')
        if self.current_lang == 'EN':
            d_cat = self.categories_data.get(c_val, c_val)
        else:
            d_cat = c_val
        self.lbl_main_cat.config(text=f"{LANG_DATA[self.current_lang]['main_cat_head']} {self.get_loc_text(d_cat)}")
        
        desc = item.get('desc_ru', '') if self.current_lang == "RU" else item.get('desc_en', item.get('desc_ru', ''))
        for w, t in [(self.txt_desc_main, self.get_loc_text(desc)), (self.txt_p_main, item.get('prompt', ''))]:
            w.config(state="normal"); w.delete("1.0", tk.END); w.insert("1.0", t); w.config(state="disabled")

    def copy_p(self):
        c = self.txt_p_main.get("1.0", tk.END).strip()
        if c:
            self.root.clipboard_clear(); self.root.clipboard_append(c)
            messagebox.showinfo("OK", LANG_DATA[self.current_lang]["copy_ok"])

    def update_admin_list(self):
        self.alb.delete(0, tk.END); self.adm_map = []
        sel, all_l = self.afv.get(), LANG_DATA[self.current_lang]["all_cats"]
        for i, p in enumerate(self.prompts):
            c_disp = self.get_cat_display(p.get('category', 'Общее'))
            if sel == all_l or c_disp == sel:
                self.alb.insert(tk.END, f"  {self.get_loc_text(p['name'])}")
                self.adm_map.append(i)

    def on_admin_select(self, e):
        if not self.alb.curselection(): return
        self.cur_adm_idx = self.adm_map[self.alb.curselection()[0]]
        it = self.prompts[self.cur_adm_idx]
        self.ecc.set(self.get_cat_display(it.get('category', 'Общее')))
        self.a_en.delete(0, tk.END); self.a_en.insert(0, self.get_loc_text(it['name']))
        self.a_tp.delete("1.0", tk.END); self.a_tp.insert("1.0", it['prompt'])
        
        desc_text = it.get('desc_en', it.get('desc_ru', '')) if self.current_lang == "EN" else it.get('desc_ru', '')
        self.a_rd.delete("1.0", tk.END); self.a_rd.insert("1.0", desc_text)

    def save_adm(self):
        cat_display = self.ecc.get()
        prompt_name = self.a_en.get().strip()
        
        if not cat_display or not prompt_name:
            messagebox.showwarning("Внимание", "Необходимо заполнить категорию и название эффекта.")
            return

        ru_cat = next((r for r, e in self.categories_data.items() if e == cat_display or r == cat_display), cat_display)
        
        desc_input = self.a_rd.get("1.0", tk.END).strip()
        new_item = {
            "name": prompt_name,
            "category": ru_cat,
            "category_en": self.categories_data.get(ru_cat, ru_cat),
            "prompt": self.a_tp.get("1.0", tk.END).strip()
        }
        
        if self.current_lang == "EN":
            new_item["desc_en"] = desc_input
            if self.cur_adm_idx is not None:
                new_item["desc_ru"] = self.prompts[self.cur_adm_idx].get("desc_ru", "")
        else:
            new_item["desc_ru"] = desc_input
            if self.cur_adm_idx is not None:
                new_item["desc_en"] = self.prompts[self.cur_adm_idx].get("desc_en", "")
        
        user_list = []
        if os.path.exists(self.user_data_file):
            try:
                with open(self.user_data_file, 'rb') as f:
                    user_list = self.decrypt_data(f.read())
            except Exception as e: pass

        existing_names = [self.get_loc_text(p.get('name')) for p in user_list]

        if self.cur_adm_idx is None:
            if prompt_name in existing_names:
                messagebox.showerror("Ошибка", f"Промпт с названием '{prompt_name}' уже существует!\nПожалуйста, измените название, чтобы не удалить старый промпт.")
                return
        else:
            old_name_raw = self.prompts[self.cur_adm_idx]['name']
            old_name = self.get_loc_text(old_name_raw)
            
            if old_name != prompt_name:
                if prompt_name in existing_names:
                    messagebox.showerror("Ошибка", f"Промпт с названием '{prompt_name}' уже существует!")
                    return
                
                ans = messagebox.askyesno("Сохранение", "Вы изменили название эффекта.\nСохранить как новый промпт?\n\n(Да - создать новый, Нет - переименовать старый)")
                if ans:
                    self.cur_adm_idx = None
                else:
                    user_list = [p for p in user_list if self.get_loc_text(p.get('name')) != old_name]
            else:
                user_list = [p for p in user_list if self.get_loc_text(p.get('name')) != old_name]

        user_list = [p for p in user_list if self.get_loc_text(p.get('name')) != prompt_name]
        user_list.append(new_item)
        
        try:
            with open(self.user_data_file, 'wb') as f:
                f.write(self.encrypt_data(user_list))
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{e}")
            return

        self.cur_adm_idx = None
        self.show_main_interface(tab_index=1)
    
    def del_adm(self):
        l = LANG_DATA[self.current_lang]
        if self.cur_adm_idx is None or not messagebox.askyesno(l["confirm_del"], l["ask_del"]): return
        n = self.prompts[self.cur_adm_idx]['name']
        all_dat_files = [f for f in os.listdir(self.base_dir) if f.endswith(".ikd") and "grok_prompts" in f]
        for f_name in all_dat_files:
            path = os.path.join(self.base_dir, f_name)
            try:
                with open(path, 'rb') as f: data = self.decrypt_data(f.read())
                new_data = [p for p in data if p.get('name') != n]
                if len(new_data) != len(data):
                    with open(path, 'wb') as f: f.write(self.encrypt_data(new_data))
            except: pass
        self.cur_adm_idx = None
        self.show_main_interface(tab_index=1)

    def add_cat(self):
        top = tk.Toplevel(self.root)
        top.title("Новая категория")
        top.geometry(f"{int(500*self.zoom_scale)}x{int(250*self.zoom_scale)}")
        top.configure(bg=BG_PANEL)
        top.transient(self.root)
        top.grab_set()

        sw, sh = self.root.winfo_width(), self.root.winfo_height()
        sx, sy = self.root.winfo_x(), self.root.winfo_y()
        top.geometry(f"+{sx + sw//2 - int(250*self.zoom_scale)}+{sy + sh//2 - int(125*self.zoom_scale)}")

        tk.Label(top, text="Введите название новой категории:", font=("Segoe UI Bold", int(14*self.zoom_scale)), bg=BG_PANEL, fg=TEXT_WHITE).pack(pady=int(20*self.zoom_scale))
        
        cat_var = tk.StringVar()
        entry = tk.Entry(top, textvariable=cat_var, font=("Segoe UI Bold", int(16*self.zoom_scale)), bg=BG_MAIN, fg=TEXT_WHITE, insertbackground="white", highlightthickness=2, highlightcolor=ACCENT_CYAN, highlightbackground=BORDER_GLOW)
        entry.pack(fill="x", padx=int(30*self.zoom_scale), ipady=int(8*self.zoom_scale))
        entry.focus_set()

        def save_new_cat(event=None):
            n = cat_var.get().strip()
            if n:
                if n not in self.categories_data:
                    self.categories_data[n] = n
                    new_vals = [LANG_DATA[self.current_lang]["all_cats"]] + sorted([self.get_cat_display(c) for c in self.categories_data.keys()])
                    self.main_cb['values'] = new_vals
                    self.afc['values'] = new_vals
                    self.ecc['values'] = sorted([self.get_cat_display(c) for c in self.categories_data.keys()])
                    self.ecc.set(self.get_cat_display(n))
                top.destroy()

        entry.bind("<Return>", save_new_cat)
        
        btn = GlowButton(top, text="СОХРАНИТЬ", color=SUCCESS, command=save_new_cat, width=250, height=45, font_size=13, zoom=self.zoom_scale)
        btn.pack(pady=int(25*self.zoom_scale))

    def del_cat(self):
        l = LANG_DATA[self.current_lang]; cd = self.ecc.get()
        if cd and messagebox.askyesno(l["confirm_del"], l["ask_del"]):
            rc = next((r for r, e in self.categories_data.items() if e == cd or r == cd), cd)
            all_dat = [f for f in os.listdir(self.base_dir) if f.endswith(".ikd") and "grok_prompts" in f]
            for f_name in all_dat:
                path = os.path.join(self.base_dir, f_name)
                try:
                    with open(path, 'rb') as f: data = self.decrypt_data(f.read())
                    new_d = [p for p in data if p.get('category') != rc]
                    if len(new_d) != len(data):
                        with open(path, 'wb') as f: f.write(self.encrypt_data(new_d))
                except: pass
            self.categories_data.pop(rc, None); self.show_main_interface(tab_index=1)

    def clear_adm(self):
        self.cur_adm_idx = None; self.a_en.delete(0, tk.END); self.a_tp.delete("1.0", tk.END); self.a_rd.delete("1.0", tk.END)

    def show_language_selector(self):
        for w in self.root.winfo_children(): w.destroy()
        self.center_window(1300, 850) 
        c = tk.Frame(self.root, bg=BG_MAIN); c.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(c, text="CHOOSE LANGUAGE / ВЫБЕРИТЕ ЯЗЫК", font=("Segoe UI Bold", 18), bg=BG_MAIN, fg=TEXT_WHITE).pack(pady=20)
        btn_f = tk.Frame(c, bg=BG_MAIN); btn_f.pack()
        
        GlowButton(btn_f, text="ENGLISH", color=ACCENT_CYAN, font_size=14, width=200, height=50, command=lambda: self.set_lang_and_auth("EN")).pack(side="left", padx=10)
        GlowButton(btn_f, text="РУССКИЙ", color=ACCENT_GREEN, font_size=14, width=200, height=50, command=lambda: self.set_lang_and_auth("RU")).pack(side="left", padx=10)

    def set_lang_and_auth(self, lang): self.current_lang = lang; self.show_auth_window()

    def show_auth_window(self):
        for widget in self.root.winfo_children(): widget.destroy()
        self.center_window(1300, 850) 
        
        txt = {
            "RU": {
                "head": "🧠 Grok Prompt Manager", "id": f"ID устройства: {self.hwid}", 
                "copy": "📋 Копировать ID", "act": "ПОДТВЕРДИТЬ АКТИВАЦИЮ", 
                "msg": "Идентификатор скопирован!", "err": "Ошибка: Ключ лицензии не прошел проверку", 
                "back": "↩ НАЗАД", "paste": "📋 ВСТАВИТЬ ИЗ БУФЕРА", 
                "entry_hint": "Введите ваш Код Активации или Ключ Лицензии"
            },
            "EN": {
                "head": "🧠 Grok Prompt Manager", "id": f"Device ID: {self.hwid}", 
                "copy": "📋 Copy ID", "act": "CONFIRM ACTIVATION", 
                "msg": "Device ID copied!", "err": "Error: Invalid License Key", 
                "back": "↩ BACK", "paste": "📋 PASTE FROM CLIPBOARD",
                "entry_hint": "Enter your Activation Code or License Key"
            }
        }[self.current_lang]

        c = tk.Frame(self.root, bg=BG_MAIN); c.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Button(c, text=txt["back"], bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI Bold", 10), bd=0, padx=10, pady=5, command=self.show_language_selector).pack(anchor="nw", pady=(0, 20))
        
        tk.Label(c, text=txt["head"], font=("Segoe UI Black", 42), bg=BG_MAIN, fg=ACCENT_GREEN).pack()
        
        idf = tk.Frame(c, bg=BG_MAIN, pady=15); idf.pack()
        tk.Label(idf, text=txt["id"], bg=BG_MAIN, fg=TEXT_MUTED, font=("Consolas", 14)).pack(side="left", padx=15)
        tk.Button(idf, text=txt["copy"], bg="#333", fg="white", font=("Segoe UI Bold", 10), command=lambda: (self.root.clipboard_clear(), self.root.clipboard_append(self.hwid), messagebox.showinfo("ОК", txt["msg"])), bd=0).pack(side="left")
        
        self.ki = tk.Entry(c, font=("Consolas", 20), justify="center", bg=BG_PANEL, fg="white", width=35, insertbackground="white", highlightthickness=2, highlightbackground=BORDER_GLOW, highlightcolor=ACCENT_CYAN)
        self.ki.pack(pady=10, ipady=12)
        
        tk.Label(c, text=txt["entry_hint"], font=("Segoe UI Italic", 10), bg=BG_MAIN, fg=TEXT_MUTED).pack()
        
        self.status_lbl = tk.Label(c, text="", font=("Segoe UI Bold", 11), bg=BG_MAIN, fg=ACCENT_CYAN)
        self.status_lbl.pack(pady=5)
        
        tk.Button(c, text=txt["paste"], bg="#475569", fg="white", font=("Segoe UI Bold", 10), command=lambda: (self.ki.delete(0, tk.END), self.ki.insert(0, self.root.clipboard_get())), bd=0).pack(pady=15)
        
        self.btn_act = GlowButton(c, text=txt["act"], color=ACCENT_GREEN, command=lambda: self.activate_now(self.ki.get().strip().upper(), txt["err"]), font_size=16, width=380, height=70, zoom=self.zoom_scale)
        self.btn_act.pack(pady=10, fill="x")

    def activate_now(self, user_key, error_msg):
        txt = {"RU": {"checking": "🔍 ПРОВЕРКА ЛИЦЕНЗИИ...", "wait": "Пожалуйста, подождите...", "act": "ПОДТВЕРДИТЬ АКТИВАЦИЮ"}, 
               "EN": {"checking": "🔍 CHECKING LICENSE...", "wait": "Please wait...", "act": "CONFIRM ACTIVATION"}}[self.current_lang]
        
        self.btn_act.set_text(txt["checking"])
        self.btn_act.set_active(True)
        self.status_lbl.config(text=txt["wait"], fg=ACCENT_GOLD)
        self.root.update()

        if user_key.startswith("GRK-"):
            threading.Thread(target=self.server_activation, args=(user_key,), daemon=True).start()
            return

        hash_res = hashlib.sha256((self.hwid + SECRET_SALT).encode()).hexdigest().upper()
        expected = f"{hash_res[0:6]}-{hash_res[6:12]}-{hash_res[12:18]}"
        
        if user_key == expected:
            with open(self.lic_file, "w") as f: f.write(user_key)
            self.root.after(500, self.show_success_and_proceed)
        else:
            self.btn_act.set_text(txt["act"])
            self.btn_act.set_active(False)
            self.status_lbl.config(text="")
            messagebox.showerror("Ошибка" if self.current_lang == "RU" else "Error", error_msg)

    # ИСПРАВЛЕНО: Безопасная обработка ошибок для избежания "тихого зависания"
    def server_activation(self, code):
        txt_act = "ПОДТВЕРДИТЬ АКТИВАЦИЮ" if self.current_lang == "RU" else "CONFIRM ACTIVATION"
        
        # Надежная функция для сброса интерфейса при ошибке сети
        def reset_ui_with_error(title, msg):
            messagebox.showerror(title, msg)
            self.btn_act.set_text(txt_act)
            self.btn_act.set_active(False)
            self.status_lbl.config(text="")

        try:
            os_info, ip, loc, username = get_telemetry()
            params = urllib.parse.urlencode({'hwid': self.hwid, 'pin': code, 'product': PRODUCT_ID, 'os': os_info, 'ip': ip, 'location': loc, 'username': username}).encode()
            req = urllib.request.Request(GOOGLE_SCRIPT_URL, data=params, method='POST')
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
            
            if res_data.get("success"):
                final_key = res_data.get("key")
                with open(self.lic_file, "w") as f: f.write(final_key)
                self.save_sync_data(code)
                self.root.after(0, self.show_success_and_proceed)
            else:
                msg = res_data.get("message", "Ошибка активации")
                title = "Сервер" if self.current_lang == "RU" else "Server"
                # Передаем строковые переменные безопасно
                self.root.after(0, lambda t=title, m=msg: reset_ui_with_error(t, f"Отказ: {m}"))
                
        except Exception as e:
            title = "Сеть" if self.current_lang == "RU" else "Network"
            # Ошибка превращается в строку до того, как переменная 'e' удалится из памяти!
            err_msg = str(e)
            self.root.after(0, lambda t=title, m=err_msg: reset_ui_with_error(t, f"Сбой связи: {m}"))

    def show_success_and_proceed(self):
        msg = "✅ ЛИЦЕНЗИЯ УСПЕШНО АКТИВИРОВАНА!" if self.current_lang == "RU" else "✅ LICENSE SUCCESSFULLY ACTIVATED!"
        self.status_lbl.config(text=msg, fg=ACCENT_GREEN)
        self.btn_act.set_text("OK!")
        self.root.update()
        messagebox.showinfo("IK DESIGNS", msg)
        self.proceed_to_app()

    def proceed_to_app(self):
        v_path = resource_path("intro.mp4")
        if os.path.exists(v_path):
            self.play_intro(v_path)
        else:
            self.show_main_interface()

    def play_intro(self, v_path):
        if not HAS_VIDEO:
            msg = (
                f"Внимание!\nВаша операционная система запустила этот скрипт через:\n{sys.executable}\n\n"
                f"В этом окружении Питона не установлены библиотеки для видео!\n"
                f"Хотите, чтобы программа прямо сейчас сама автоматически скачала и установила их?"
            )
            if messagebox.askyesno("Авто-настройка Питона", msg):
                self.root.withdraw()
                load_win = tk.Toplevel()
                load_win.title("IKD Auto Installer")
                load_win.geometry("450x150")
                load_win.configure(bg="#0a0b10")
                load_win.update_idletasks()
                x = (load_win.winfo_screenwidth() // 2) - (450 // 2)
                y = (load_win.winfo_screenheight() // 2) - (150 // 2)
                load_win.geometry(f"+{x}+{y}")
                load_win.overrideredirect(True)
                
                tk.Label(load_win, text="⏳ ПОЖАЛУЙСТА, ПОДОЖДИТЕ...\n\nИдет загрузка и установка (OpenCV + PyGame-CE)...\nЭто займет около 10-20 секунд.", font=("Segoe UI Bold", 12), bg="#0a0b10", fg="#00d1ff").pack(expand=True)
                load_win.update()

                try:
                    si = None
                    if sys.platform == "win32":
                        si = subprocess.STARTUPINFO()
                        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python", "pillow", "pygame-ce"], startupinfo=si)
                    
                    load_win.destroy()
                    messagebox.showinfo("ГОТОВО ✅", "Библиотеки для видео и звука успешно скачаны!\n\nПожалуйста, закройте это окно и запустите программу заново (видео заработает).")
                    sys.exit()
                except Exception as ex:
                    load_win.destroy()
                    messagebox.showerror("Ошибка", f"Не удалось установить автоматически. Ошибка:\n{ex}")
                    self.root.deiconify()
                    self.show_main_interface()
                return
            else:
                self.show_main_interface()
                return

        for widget in self.root.winfo_children(): widget.destroy()
        
        self.center_window(1300, 850)
        self.root.configure(bg="#000000")
        
        def finish_intro(e=None):
            self.show_main_interface()

        try:
            player = IKDVideoPlayer(self.root, v_path, finish_intro)
            player.place(x=0, y=0, relwidth=1, relheight=1)
            player.play()
            
        except Exception as e:
            messagebox.showerror("Ошибка плеера", f"Сбой при запуске видео:\n{e}")
            finish_intro()

if __name__ == "__main__":
    root = tk.Tk()
    app = GrokPromptManager(root)
    root.mainloop()