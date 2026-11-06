# -*- coding: utf-8 -*-
"""Тапалка с собачкой.

Тапы -> очки. Задания -> монеты. Монеты -> уровни питомца (1-50).
Каждые 10 уровней открывается новый мир (фон меняется).
Работает без интернета.
Запуск в Pydroid 3: сначала установите Kivy (меню Pip), потом откройте файл и нажмите Run.
"""
import json
import math
import os
import random
import struct
import wave
from datetime import date, datetime


_LOG_PATH = None


def _log(msg):
    """Короткие отметки о ходе запуска в crash_log.txt: сначала пробуем папку Download
    (её видно в проводнике), потом папку рядом с main.py. По последней строке видно,
    где игра остановилась."""
    global _LOG_PATH
    try:
        line = "%s %s\n" % (datetime.now().strftime("%H:%M:%S"), msg)
        try:
            here = os.path.dirname(os.path.abspath(__file__))
        except Exception:
            here = "."
        candidates = [_LOG_PATH] if _LOG_PATH else [
            "/storage/emulated/0/Download/crash_log.txt",
            os.path.join(here, "crash_log.txt"),
        ]
    except Exception:
        return
    for path in candidates:
        try:
            if os.path.exists(path) and os.path.getsize(path) > 20000:
                os.remove(path)
            with open(path, "a", encoding="utf-8") as f:
                if _LOG_PATH is None:
                    f.write("(лог: %s)\n" % path)
                f.write(line)
            _LOG_PATH = path
            return
        except Exception:
            continue


_log("=== запуск: начало ===")

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import (Color, Ellipse, InstructionGroup, Line, PopMatrix,
                           PushMatrix, Rectangle, Scale, Translate,
                           Triangle)
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

import kivy

_log("kivy загружен, версия " + str(getattr(kivy, "__version__", "?")))

# ---------------------------------------------------------------- настройки
MAX_LEVEL = 50
BG = (0.99, 0.95, 0.85, 1)
TEXT = (0.2, 0.13, 0.08, 1)
STAGES = ["Щенок", "Подросток", "Взрослая собака", "Чемпион", "Легенда"]
WORLDS = ["Солнечный луг", "Закат", "Звёздная ночь", "Космос", "Золотые небеса"]

# Если на слабом телефоне всё равно тормозит: поставьте FANCY_BG = False
# (фон станет неподвижной картинкой) или уменьшите BG_FPS.
FANCY_BG = False  # облегчённый режим для Android/Pydroid 3
BG_FPS = 12  # для слабых телефонов; на мощных можно 20-30
UI_FPS = 15  # как часто обновляются надписи при быстрых тапах
# Если со звуком на телефоне что-то не так, поставьте SOUND_ENABLED = False:
# игра тогда вообще не трогает звуковую часть.
SOUND_ENABLED = False  # временно отключено для стабильного запуска
# Если прошлый запуск вылетел, игра сама включает безопасный режим (без анимации фона
# и звука). Чтобы вернуть всё обратно, поставьте True, запустите игру один раз
# и верните False.
RESET_SAFE_MODE = True  # принудительно включаем безопасный режим
GUARD_VERSION = 8  # менять не нужно

# Что получает питомец на этих уровнях (рисуется в Dog.redraw)
UNLOCKS = {
    2: "красный ошейник",
    5: "праздничный колпак",
    10: "тёмные очки",
    15: "бабочка",
    20: "корона",
    30: "золотой ошейник",
    40: "крылья",
    50: "золотая аура",
}

# Миры (фоны). sky: цвета неба сверху, из середины и снизу. hills: два слоя холмов.
THEMES = [
    dict(  # 0 Солнечный луг
        sky=[(0.28, 0.58, 1.0), (0.55, 0.80, 1.0), (0.88, 0.96, 1.0)],
        hills=[(0.52, 0.82, 0.40), (0.33, 0.67, 0.29)],
        cloud=(1, 1, 1, 0.92), stars=0, body="sun",
        spark=(1.0, 1.0, 0.75),
        text=(0.10, 0.18, 0.30, 1), accent=(0.85, 0.2, 0.1, 1)),
    dict(  # 1 Закат
        sky=[(0.30, 0.20, 0.55), (0.95, 0.42, 0.38), (1.0, 0.82, 0.48)],
        hills=[(0.35, 0.22, 0.42), (0.20, 0.12, 0.30)],
        cloud=(1.0, 0.75, 0.70, 0.75), stars=18, body="sunset",
        spark=(1.0, 0.9, 0.6),
        text=(1, 1, 1, 1), accent=(1.0, 0.92, 0.45, 1)),
    dict(  # 2 Звёздная ночь
        sky=[(0.02, 0.03, 0.12), (0.06, 0.09, 0.28), (0.14, 0.20, 0.48)],
        hills=[(0.06, 0.12, 0.20), (0.03, 0.08, 0.12)],
        cloud=None, stars=60, body="moon",
        spark=(0.8, 0.9, 1.0),
        text=(1, 1, 1, 1), accent=(1.0, 0.92, 0.45, 1)),
    dict(  # 3 Космос
        sky=[(0.05, 0.0, 0.15), (0.28, 0.05, 0.45), (0.05, 0.30, 0.50)],
        hills=[(0.22, 0.12, 0.40), (0.12, 0.06, 0.26)],
        cloud=None, stars=100, body="planet",
        spark=(1.0, 0.7, 1.0),
        text=(1, 1, 1, 1), accent=(0.6, 1.0, 0.9, 1)),
    dict(  # 4 Золотые небеса
        sky=[(0.45, 0.30, 0.80), (0.95, 0.65, 0.85), (1.0, 0.93, 0.65)],
        hills=[(1.0, 0.85, 0.45), (0.90, 0.65, 0.25)],
        cloud=(1, 1, 1, 0.85), stars=25, body="rays",
        spark=(1.0, 1.0, 0.8),
        text=(1, 1, 1, 1), accent=(1.0, 0.95, 0.4, 1)),
]


# ---------------------------------------------------------------- вспомогательное
def fmt(n):
    return f"{n:,}".replace(",", " ")


def upgrade_cost(level):
    """Цена перехода с уровня level на level+1 (1->2 стоит 12 монет)."""
    return round(10 * 1.25 ** level)


def stage_of(level):
    return min(level // 10, len(STAGES) - 1)


def next_unlock(level):
    for lvl in sorted(UNLOCKS):
        if lvl > level:
            return lvl, UNLOCKS[lvl]
    return None


def lerp(c1, c2, t):
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


# цвет шерсти плавно меняется с каждым уровнем: песочный -> коричневый -> серо-голубой -> золотой
COLOR_STOPS = [
    (1, (0.93, 0.78, 0.55)),
    (15, (0.68, 0.46, 0.28)),
    (30, (0.55, 0.60, 0.72)),
    (50, (1.00, 0.80, 0.20)),
]


def coat_color(level):
    for (l1, c1), (l2, c2) in zip(COLOR_STOPS, COLOR_STOPS[1:]):
        if level <= l2:
            return lerp(c1, c2, (level - l1) / (l2 - l1))
    return COLOR_STOPS[-1][1]


def make_gradient(stops, rows=64):
    """Вертикальный градиент в виде текстуры. stops: цвета сверху, из середины, снизу."""
    buf = bytearray()
    for i in range(rows):
        p = 1 - i / (rows - 1)  # строка 0 - низ картинки
        if p < 0.5:
            c = lerp(stops[0], stops[1], p / 0.5)
        else:
            c = lerp(stops[1], stops[2], (p - 0.5) / 0.5)
        buf.extend(int(v * 255) for v in c)
        buf.append(255)
    tex = Texture.create(size=(1, rows), colorfmt="rgba")
    tex.blit_buffer(bytes(buf), colorfmt="rgba", bufferfmt="ubyte")
    tex.mag_filter = "linear"
    tex.min_filter = "linear"
    return tex


# ---------------------------------------------------------------- задания (50 штук)
def build_tasks():
    tasks = []

    def add(kind, title, targets, rewards):
        for target, reward in zip(targets, rewards):
            tasks.append({
                "id": f"{kind}_{target}",
                "kind": kind,
                "title": title.format(fmt(target)),
                "target": target,
                "reward": reward,
            })

    add("taps", "Сделай {} тапов",
        [100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000, 1000000],
        [15, 40, 80, 150, 300, 500, 800, 1200, 1600, 2000])
    add("level", "Прокачай питомца до {} уровня",
        [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
        [20, 40, 60, 100, 150, 250, 400, 600, 800, 1000])
    add("days", "Играй {} дн.",
        [1, 2, 3, 5, 7, 10, 14, 21, 30, 50],
        [15, 20, 30, 50, 70, 100, 150, 250, 350, 500])
    add("spent", "Потрать {} монет на прокачку",
        [100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 75000, 100000],
        [10, 30, 60, 100, 150, 250, 400, 600, 700, 800])
    add("points", "Накопи {} очков",
        [500, 2500, 10000, 50000, 150000, 500000, 1000000, 2500000, 5000000, 10000000],
        [15, 30, 60, 120, 200, 350, 500, 700, 900, 1200])
    return tasks


TASKS = build_tasks()


# ---------------------------------------------------------------- звуки
# Звуки не лежат файлами: игра сама синтезирует их в фоне уже после запуска
# и кладёт в папку приложения (повторно не создаёт).
# Ноты выбраны повыше: маленькие динамики телефонов (например, Galaxy A03)
# плохо воспроизводят низкие звуки.
SAMPLE_RATE = 16000
TAP_NOTES = [659.25, 783.99, 880.0, 987.77]  # ми, соль, ля, си: любая последовательность звучит мелодично


def _tone(freq, dur, vol=0.5, drop=0.0, decay=8.0, bright=0.35):
    """Мягкий «колокольчик»: синус + тихая октава и плавное затухание.
    drop меняет высоту в самом начале: отрицательный даёт «буп» вверх, положительный вниз."""
    n = int(SAMPLE_RATE * dur)
    fade = int(SAMPLE_RATE * 0.006)
    phase = 0.0
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        f = freq * (1 + drop * math.exp(-t * 70))
        phase += 2 * math.pi * f / SAMPLE_RATE
        env = min(1.0, t / 0.002) * math.exp(-t * decay)  # плавный старт, без щелчка
        s = math.sin(phase) + bright * math.sin(2 * phase) * math.exp(-t * 25)
        if i > n - fade:
            env *= (n - i) / fade
        out.append(vol * env * s)
    return out


def _mix(parts, total):
    buf = [0.0] * int(SAMPLE_RATE * total)
    for start, samples in parts:
        k = int(SAMPLE_RATE * start)
        for j, v in enumerate(samples):
            if k + j < len(buf):
                buf[k + j] += v
    return buf


def _save_wav(path, samples, gain=0.9):
    """Записывает wav, доводя громкость до gain от максимума (без искажений)."""
    peak = max(1e-9, max(abs(v) for v in samples))
    k = gain / peak
    frames = b"".join(struct.pack("<h", int(v * k * 32767)) for v in samples)
    tmp = path + ".tmp"  # сначала во временный файл: оборванная запись не испортит звук
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(frames)
    os.replace(tmp, path)


def make_sound_file(folder, name):
    """Создаёт wav нужного звука (если его ещё нет) и возвращает путь."""
    path = os.path.join(folder, name + ".wav")
    if os.path.exists(path):
        return path
    if name.startswith("tap"):
        samples = _tone(TAP_NOTES[int(name[3:])], 0.14, vol=0.8, drop=-0.18, decay=24)
        _save_wav(path, samples, 0.9)
    elif name == "levelup":
        arp = [659.25, 783.99, 987.77, 1318.5]  # ми-соль-си-ми вверх
        parts = [(i * 0.09, _tone(f, 0.5, vol=0.45, decay=5.5)) for i, f in enumerate(arp)]
        _save_wav(path, _mix(parts, 0.09 * 3 + 0.5), 0.95)
    elif name == "claim":
        parts = [(0.0, _tone(987.77, 0.28, vol=0.45, decay=9)),
                 (0.08, _tone(1318.5, 0.32, vol=0.45, decay=8))]
        _save_wav(path, _mix(parts, 0.42), 0.9)
    else:  # nope
        _save_wav(path, _tone(330.0, 0.14, vol=0.5, drop=0.3, decay=20, bright=0.1), 0.7)
    return path


class Sounds:
    """Звуки загружаются по одному после запуска игры (окно появляется сразу).
    Если звук на устройстве недоступен, игра просто работает без него."""

    NAMES = ["tap0", "tap1", "tap2", "tap3", "levelup", "claim", "nope"]

    def __init__(self, folder, state):
        self.folder = folder
        self.state = state
        self.enabled = False
        self.loaded = False
        self.loading = False
        self.taps = []
        self.one = {}
        self.last = -1
        self.queue = []

    def _probe(self, on):
        """Метка «идёт загрузка звука»: если приложение вылетит прямо во время неё,
        при следующем запуске звук отключится, а игра запустится."""
        self.state.data["sound_probe"] = on
        self.state.save()

    def start_loading(self):
        if not SOUND_ENABLED or self.loaded or self.loading:
            return
        try:
            os.makedirs(self.folder, exist_ok=True)
            self.queue = list(self.NAMES)
            self.loading = True
            self._probe(True)
            Clock.schedule_once(self._step, 0.7)
        except Exception:
            self.queue = []
            self.loading = False

    def _step(self, dt):
        if not self.queue:
            return
        name = self.queue.pop(0)
        _log("звук: " + name)
        try:
            path = make_sound_file(self.folder, name)
            from kivy.core.audio import SoundLoader
            s = SoundLoader.load(path)
            if s:
                if name.startswith("tap"):
                    s.volume = 1.0
                    self.taps.append(s)
                else:
                    self.one[name] = s
        except Exception:
            self.queue = []  # любая ошибка: звук отключается, игра идёт дальше
            self.loading = False
            self._probe(False)
            return
        if self.queue:
            Clock.schedule_once(self._step, 0.05)
        else:
            self.loading = False
            self.loaded = True
            self._probe(False)
            _log("звук: загружен")

    def play(self, name):
        if not self.enabled:
            return
        try:
            if name == "tap":
                if not self.taps:
                    return
                i = random.randrange(len(self.taps))
                if i == self.last:
                    i = (i + 1) % len(self.taps)
                self.last = i
                self.taps[i].play()
            else:
                s = self.one.get(name)
                if s:
                    s.play()
        except Exception:
            pass


# ---------------------------------------------------------------- сохранение
class State:
    def __init__(self, path):
        self.path = path
        self.data = {
            "points": 0, "coins": 0, "level": 1, "taps": 0,
            "spent": 0, "days": [], "claimed": [], "sound": False,
            "boot_ok": True, "safe": False, "sound_probe": False, "sound_broken": False,
        }
        self.load()
        today = date.today().isoformat()
        if today not in self.data["days"]:
            self.data["days"].append(today)

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data.update(json.load(f))
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except OSError:
            pass

    def progress(self, kind):
        d = self.data
        return {
            "taps": d["taps"],
            "level": d["level"],
            "days": len(d["days"]),
            "spent": d["spent"],
            "points": d["points"],
        }[kind]


# ---------------------------------------------------------------- живой фон
class Background(Widget):
    """Анимированный фон: небо-градиент, солнце/луна/планета, облака, звёзды,
    холмы, летящие искорки и падающие звёзды. Мир зависит от уровня питомца.

    Чтобы не тормозило, неподвижные части (небо и холмы) рисуются один раз,
    а каждый кадр перерисовываются только движущиеся."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.t = 0.0
        self.animated = True
        self.theme_idx = -1
        self.th = THEMES[0]
        self.tex = None
        self.star_buckets = [[], [], []]
        self.shoot = None
        # искорки: x, y, скорость подъёма, фаза
        self.sparks = [(random.random(), random.random(),
                        0.02 + random.random() * 0.05, random.random() * 6.28)
                       for _ in range(12)]
        self.spark_buckets = [self.sparks[i::3] for i in range(3)]
        # облака: x, y, размер, скорость
        self.clouds = [(0.10, 0.80, 1.0, 0.010), (0.45, 0.66, 0.7, 0.016),
                       (0.75, 0.90, 0.85, 0.012), (0.95, 0.56, 0.6, 0.020)]
        # четыре слоя снизу вверх
        self.l_sky = InstructionGroup()    # неподвижный: градиент
        self.l_air = InstructionGroup()    # движется: звёзды, солнце, облака
        self.l_hills = InstructionGroup()  # неподвижный: холмы
        self.l_spark = InstructionGroup()  # движется: искорки
        for g in (self.l_sky, self.l_air, self.l_hills, self.l_spark):
            self.canvas.add(g)
        self.set_theme(0)
        self.bind(pos=self.layout, size=self.layout)

    def set_theme(self, idx):
        if idx == self.theme_idx:
            return
        self.theme_idx = idx
        self.th = THEMES[idx]
        self.tex = None  # без текстуры: совместимее со слабыми Android-устройствами
        rng = random.Random(idx)
        stars = [(rng.random(), rng.uniform(0.35, 1.0), rng.uniform(0.6, 2.2))
                 for _ in range(self.th["stars"])]
        self.star_buckets = [stars[i::3] for i in range(3)]
        self.shoot = None
        self.layout()

    def start(self):
        Clock.unschedule(self._tick)
        if FANCY_BG and self.animated:
            Clock.schedule_interval(self._tick, 1 / BG_FPS)

    def stop(self):
        Clock.unschedule(self._tick)

    def _tick(self, dt):
        self.t += dt
        if self.theme_idx in (2, 3):
            if self.shoot is None:
                if random.random() < 0.01:
                    self.shoot = [random.uniform(0.35, 0.95),
                                  random.uniform(0.65, 0.95), 0.0]
            else:
                self.shoot[2] += dt
                if self.shoot[2] > 0.7:
                    self.shoot = None
        self.animate()

    def layout(self, *args):
        """Неподвижные слои: рисуются при смене размера или мира."""
        w, h = self.size
        if w <= 1 or h <= 1:
            return
        x0, y0 = self.pos
        th = self.th

        g = self.l_sky
        g.clear()
        g.add(Color(*th["sky"][1], 1))
        g.add(Rectangle(pos=self.pos, size=self.size))

        g = self.l_hills
        g.clear()
        g.add(Color(*th["hills"][0]))
        g.add(Ellipse(pos=(x0 - 0.2 * w, y0 - 0.28 * h), size=(0.9 * w, 0.5 * h)))
        g.add(Ellipse(pos=(x0 + 0.35 * w, y0 - 0.30 * h), size=(1.0 * w, 0.46 * h)))
        g.add(Color(*th["hills"][1]))
        g.add(Ellipse(pos=(x0 - 0.4 * w, y0 - 0.35 * h), size=(1.1 * w, 0.45 * h)))
        g.add(Ellipse(pos=(x0 + 0.30 * w, y0 - 0.38 * h), size=(1.3 * w, 0.45 * h)))

        self.animate()

    @staticmethod
    def _disc(g, cx, cy, r, rgb, a=1.0):
        g.add(Color(rgb[0], rgb[1], rgb[2], a))
        g.add(Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r)))

    def animate(self):
        """Движущиеся слои; в облегчённом режиме не рисуем их."""
        if not FANCY_BG:
            self.l_air.clear()
            self.l_spark.clear()
            return
        w, h = self.size
        if w <= 1 or h <= 1:
            return
        x0, y0 = self.pos
        th = self.th
        t = self.t
        m = min(w, h)
        disc = self._disc

        def X(f):
            return x0 + f * w

        def Y(f):
            return y0 + f * h

        g = self.l_air
        g.clear()

        # звёзды мерцают (три группы с разной яркостью)
        for k, bucket in enumerate(self.star_buckets):
            if not bucket:
                continue
            g.add(Color(1, 1, 1, 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2 + k * 2.1))))
            for sx, sy, size in bucket:
                d = size * dp(1.6)
                g.add(Ellipse(pos=(X(sx) - d / 2, Y(sy) - d / 2), size=(d, d)))

        # падающая звезда
        if self.shoot is not None:
            sx, sy, age = self.shoot
            p = age / 0.7
            hx, hy = X(sx - 0.25 * p), Y(sy - 0.10 * p)
            g.add(Color(1, 1, 1, 1 - p))
            g.add(Line(points=[hx, hy, hx + 0.10 * w, hy + 0.04 * h], width=dp(1.5)))

        # солнце / закат / луна / планета / лучи
        body = th["body"]
        if