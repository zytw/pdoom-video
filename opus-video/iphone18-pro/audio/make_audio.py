# 正片配乐：120 BPM，C 大调，C-G-Am-F 循环；底鼓 + 拍手 + 踩镲 + 贝斯 + 铺底和弦 + 拨弦琶音 + 钟琴主题
import numpy as np, wave, sys
SR = 48000; DUR = 38.0; N = int(SR * DUR); B = 0.5; BAR = 2.0
def midi(m): return 440 * 2 ** ((m - 69) / 12)
mix = np.zeros((N, 2))
def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N: return
    j = min(N, i + len(sig)); s = sig[: j - i] * gain
    mix[i:j, 0] += s * np.sqrt((1 - pan) / 2) * 1.414; mix[i:j, 1] += s * np.sqrt((1 + pan) / 2) * 1.414
def tt(d): return np.arange(int(d * SR)) / SR
def pluck(f, dur=0.5, bright=1.0):
    t = tt(dur); env = np.exp(-t * 7) * (1 - np.exp(-t * 400))
    return sum((1 / k ** 1.3) * np.sin(2 * np.pi * f * k * t * (1 + 0.0015 * (k - 1))) * np.exp(-t * 3 * k * bright) for k in range(1, 7)) * env
def bell(f, dur=1.4):
    t = tt(dur)
    s = np.sin(2*np.pi*f*t) + 0.5*np.sin(2*np.pi*f*2.76*t)*np.exp(-t*4) + 0.25*np.sin(2*np.pi*f*5.4*t)*np.exp(-t*8)
    return s * np.exp(-t * 2.4) * (1 - np.exp(-t * 600))
def kick(dur=0.35):
    t = tt(dur); f = 50 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
rng = np.random.default_rng(7)
def clap(dur=0.2):
    t = tt(dur); n = np.diff(rng.standard_normal(len(t)), prepend=0); env = np.exp(-t * 25)
    for d in (0.0, 0.012, 0.024): env += 0.6 * np.exp(-np.clip(t - d, 0, None) * 120) * (t >= d)
    return n * env * 0.35
def hat(dur=0.06):
    t = tt(dur); n = np.diff(np.diff(rng.standard_normal(len(t)), prepend=0), prepend=0)
    return n * np.exp(-t * 70) * 0.12
def bass(f, dur=0.45):
    t = tt(dur); env = np.minimum(1, t / 0.005) * np.exp(-t * 3)
    return (np.sin(2*np.pi*f*t) + 0.35*np.sin(2*np.pi*2*f*t) + 0.12*np.sin(2*np.pi*3*f*t)) * env
def pad(freqs, start, dur, gain=0.09):
    t = tt(dur); env = np.minimum(1, t / 0.25) * np.clip((dur - t) / 0.4, 0, 1)
    s = sum(np.sin(2*np.pi*f*t) + 0.6*np.sin(2*np.pi*f*1.004*t) + 0.25*np.sin(2*np.pi*2*f*t) for f in freqs)
    add(s * env / len(freqs), start, gain)

PROG = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [57, 60, 64]), (41, [57, 60, 65])]   # C G Am F
NBARS = int(DUR / BAR)
for b in range(NBARS):
    t0 = b * BAR; root, ch = PROG[b % 4]
    last = b == NBARS - 1
    if last: root, ch = 48, [60, 64, 67, 72]
    pad([midi(m) for m in ch], t0, BAR + 0.3)
    # 鼓：光圈段（8–14s）前半小节收一点，突出咔嗒声
    for i in range(4):
        tb = t0 + i * B
        if last and i > 0: break
        add(kick(), tb, 0.6)
        if i % 2 == 1: add(clap(), tb, 0.45, 0.1)
        add(hat(), tb + B / 2, 0.8, -0.3)
    for i in range(8 if not last else 1):
        add(bass(midi(root + (12 if i % 4 == 3 else 0))), t0 + i * B / 2, 0.32)
    # 拨弦琶音（16 分音符），芯片段和价格段更密
    arp = ch + [ch[0] + 12]
    dense = 4 <= t0 < 8 or 30 <= t0 < 34
    if not last:
        for i in range(16 if dense else 8):
            step = B / 4 if dense else B / 2
            add(pluck(midi(arp[i % 4] + 12), 0.35), t0 + i * step, 0.16, 0.4 * (-1) ** i)
# 钟琴主题：每个镜头开头一个短乐句
HOOK = [(0, 79), (0.25, 81), (0.5, 84), (1.0, 88)]
for t0 in [0, 4, 8, 14, 18, 22, 26, 30, 34]:
    for dt, m in HOOK: add(bell(midi(m)), t0 + dt, 0.13, 0.15)
# 结尾和弦 + 长钟声
for m in [72, 76, 79, 84]: add(bell(midi(m), 3.0), 34.5, 0.12)
fade = np.ones(N); k = int(36.6 * SR); fade[k:] = np.linspace(1, 0, N - k) ** 1.5
mix *= fade[:, None]
mix /= np.abs(mix).max() / 0.8
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
