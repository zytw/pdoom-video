# 5 秒片头配乐：120 BPM，C 大调，拨弦琶音 + 底鼓 + 拍手 + 标题钟琴
import json, numpy as np, wave, sys
SR = 48000; DUR = 5.0; N = int(SR * DUR)
t_all = np.arange(N) / SR
def midi(m): return 440 * 2 ** ((m - 69) / 12)
mix = np.zeros((N, 2))
def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR); j = min(N, i + len(sig)); s = sig[: j - i] * gain
    mix[i:j, 0] += s * (1 - pan) ** 0.5 * 0.9 ** 0; mix[i:j, 1] += s * (1 + pan) ** 0.5
def pluck(f, dur=0.5, bright=1.0):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 7) * (1 - np.exp(-t * 400))
    s = sum((1 / k ** 1.3) * np.sin(2 * np.pi * f * k * t * (1 + 0.0015 * (k - 1))) * np.exp(-t * 3 * k * bright) for k in range(1, 7))
    return s * env
def bell(f, dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2*np.pi*f*t) + 0.5*np.sin(2*np.pi*f*2.76*t)*np.exp(-t*4) + 0.25*np.sin(2*np.pi*f*5.4*t)*np.exp(-t*8)
    return s * np.exp(-t * 2.2) * (1 - np.exp(-t * 600))
def kick(dur=0.35):
    t = np.arange(int(dur * SR)) / SR
    f = 50 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
def clap(dur=0.2):
    rng = np.random.default_rng(7); t = np.arange(int(dur * SR)) / SR
    n = rng.standard_normal(len(t)); env = np.exp(-t * 25)
    for d in (0.0, 0.012, 0.024): env += 0.6 * np.exp(-np.clip(t - d, 0, None) * 120) * (t >= d)
    # 简单高通
    n = np.diff(n, prepend=0)
    return n * env * 0.35
def pad(freqs, start, dur):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.6).clip(0)
    s = sum(np.sin(2*np.pi*f*t) + 0.6*np.sin(2*np.pi*f*1.003*t) + 0.3*np.sin(2*np.pi*2*f*t) for f in freqs)
    add(s * env / len(freqs), start, 0.10)
B = 0.5
# 0–1s: 箱子下落，轻快上行音
for i, m in enumerate([72, 76, 79]): add(pluck(midi(m), 0.4), 0.05 + i * 0.13, 0.25, -0.2)
# 1–2s: 开箱 + 贴纸弹出，16 分音符琶音 C-E-G-C' / F-A-C
arp = [72, 76, 79, 84, 77, 81, 84, 88]
for i, m in enumerate(arp): add(pluck(midi(m), 0.45), 1.0 + i * 0.125, 0.28, 0.3 * (-1) ** i)
# 2s 起：标题，副歌和弦
pad([midi(60), midi(64), midi(67)], 0.0, 2.0)
pad([midi(65), midi(69), midi(72)], 2.0, 1.0)
pad([midi(67), midi(71), midi(74)], 3.0, 1.0)
pad([midi(60), midi(64), midi(67), midi(72)], 4.0, 1.0)
for b in range(10):
    t0 = b * B
    if t0 >= 2.0: add(kick(), t0, 0.55)
    if t0 >= 2.0 and b % 2 == 1: add(clap(), t0, 0.5)
mel = [(2.25, 84), (2.34, 86), (2.43, 88), (2.52, 91), (3.0, 88), (3.5, 91), (4.0, 96)]
for t0, m in mel: add(bell(midi(m)), t0, 0.22, 0.15)
for t0, m in [(2.0, 53), (3.0, 55), (4.0, 48)]: add(pluck(midi(m), 1.0, 0.3), t0, 0.45)
# 结尾淡出
fade = np.ones(N); k = int(4.5 * SR); fade[k:] = np.linspace(1, 0, N - k) ** 1.5
mix *= fade[:, None]
mix /= np.abs(mix).max() / 0.8
out = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
