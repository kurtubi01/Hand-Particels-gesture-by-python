"""
Hand Gesture Particles
----------------------
Jendela 1 : "Hand Sensor Monitor"  -> kamera + garis tangan (landmark) + status hijau
Jendela 2 : Pygame particles       -> berubah sesuai gesture

Gesture:
  5 jari (telapak terbuka)            -> partikel biru/putih menyebar
  1 jari (telunjuk)                   -> tulisan "Vrizi" besar
  2 jari (telunjuk + tengah)          -> tulisan "I LOVE YOU"
  3 jari (telunjuk + tengah + manis)  -> bentuk hati (love)
  Kepalan                             -> bentuk hati (love)
  Jempol (acungkan jempol)            -> planet bercincin oranye
Tekan  R  untuk mulai/stop REKAM video (disimpan di folder "rekaman").
Tekan  Q  atau  ESC  untuk keluar.
"""

import os
import time
import math
import threading
from datetime import datetime
from collections import deque, Counter

import cv2
import numpy as np
import mediapipe as mp

# supaya posisi/ukuran jendela tidak kacau di Windows (DPI scaling)
try:
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

import pygame

# ----------------------------------------------------------------------------
# KONFIGURASI
# ----------------------------------------------------------------------------
W, H = 700, 620          # ukuran jendela partikel (otomatis menyesuaikan layar kanan)
S = 1.0                  # faktor skala bentuk (otomatis)
N = 8000                 # jumlah partikel
CAM_W, CAM_H = 640, 480
CAM_INDEX = 0

# Kalau jendela Pygame tidak muncul / hitam di laptop kamu, ubah jadi True.
# Partikel akan ditampilkan di jendela OpenCV bernama "Particles".
RENDER_IN_OPENCV = False

# Rekam video (tekan R): gabungkan kamera + partikel jadi satu video MP4
RECORD_WITH_CAMERA = True   # False = hanya jendela partikel
RECORD_FPS = 30

# Hati (kepalan): False = bergoyang kiri-kanan (selalu terlihat bentuk hati),
# True = berputar penuh 360 derajat.
HEART_SPIN = False

# Ukuran hati (kepalan). Kecil = 6, sedang = 9, besar = 12, sangat besar = 15
HEART_SIZE = 12

# Teks per gesture: (tulisan, lebar teks relatif terhadap jendela, warna1, warna2)
TEXTS = {
    "one": ("Vrizi", 0.55, (40, 200, 255), (170, 240, 255)),
    "two": ("I LOVE YOU", 0.70, (40, 200, 255), (170, 240, 255)),
}
HEART_GESTURES = ("fist", "three")

shared_data = {
    "running": True,
    "gesture": "none",
    "hand": (0.5, 0.5),   # posisi pergelangan tangan (0..1)
    "frame": None,
}

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


# ----------------------------------------------------------------------------
# DETEKSI GESTURE
# ----------------------------------------------------------------------------
def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def detect_gesture(lm):
    wrist = lm[0]
    # jari telunjuk, tengah, manis, kelingking: ujung lebih jauh dari sendi PIP
    pairs = [(8, 6), (12, 10), (16, 14), (20, 18)]
    idx, mid, ring, pinky = [dist(lm[t], wrist) > dist(lm[p], wrist) * 1.05 for t, p in pairs]
    # jempol terjulur: ujung jempol jauh dari pangkal telunjuk (relatif ukuran telapak)
    palm = dist(lm[0], lm[9])
    thumb = dist(lm[4], lm[5]) > 0.65 * palm

    if idx and mid and ring and pinky:
        return "open"      # 5 jari
    if idx and mid and ring and not pinky:
        return "three"     # telunjuk + tengah + manis
    if idx and mid and not ring and not pinky:
        return "two"       # telunjuk + tengah
    if idx and not mid and not ring and not pinky:
        return "one"       # telunjuk saja
    if not (idx or mid or ring or pinky):
        return "thumb" if thumb else "fist"
    return "none"


# ----------------------------------------------------------------------------
# THREAD KAMERA
# ----------------------------------------------------------------------------
def camera_loop():
    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.6,
    )
    history = deque(maxlen=5)
    landmark_style = mp_draw.DrawingSpec(color=(80, 120, 255), thickness=3, circle_radius=3)
    connection_style = mp_draw.DrawingSpec(color=(200, 220, 255), thickness=2)

    prev = time.time()
    while shared_data["running"]:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        gesture = "none"
        if result.multi_hand_landmarks:
            hl = result.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(
                frame, hl, mp_hands.HAND_CONNECTIONS, landmark_style, connection_style
            )
            gesture = detect_gesture(hl.landmark)
            shared_data["hand"] = (hl.landmark[9].x, hl.landmark[9].y)

        history.append(gesture)
        stable = Counter(history).most_common(1)[0][0]
        shared_data["gesture"] = stable

        now = time.time()
        fps = 1.0 / max(now - prev, 1e-6)
        prev = now
        cv2.putText(
            frame,
            f"HAND SENSOR ACTIVE | {stable.upper()} | {fps:.0f} FPS",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
        shared_data["frame"] = frame
        time.sleep(0.01)

    cap.release()
    hands.close()


# ----------------------------------------------------------------------------
# PARTIKEL
# ----------------------------------------------------------------------------
rng = np.random.default_rng()


def lerp_colors(c1, c2, n):
    t = rng.random((n, 1))
    return c1 + (c2 - c1) * t


def get_work_area():
    """Area layar tanpa taskbar (Windows)."""
    try:
        import ctypes
        from ctypes import wintypes
        r = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(r), 0)
        return r.left, r.top, r.right, r.bottom
    except Exception:
        return None


def make_writer(width, height):
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rekaman")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, datetime.now().strftime("partikel_%Y%m%d_%H%M%S.mp4"))
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), RECORD_FPS, (width, height))
    return writer, path


def compose_frame(particles_bgr, cam_frame, out_w, out_h):
    """Gabungkan kamera (kiri) + partikel (kanan) lalu potong ke ukuran video."""
    img = particles_bgr
    if RECORD_WITH_CAMERA and cam_frame is not None:
        h = particles_bgr.shape[0]
        cam = cv2.resize(cam_frame, (int(cam_frame.shape[1] * h / cam_frame.shape[0]), h))
        img = np.hstack([cam, particles_bgr])
    return np.ascontiguousarray(img[:out_h, :out_w])


def build_scatter():
    local = np.column_stack([
        rng.uniform(-W / 2 * 0.97, W / 2 * 0.97, N),
        rng.uniform(-H / 2 * 0.97, H / 2 * 0.97, N),
        rng.uniform(-300 * S, 300 * S, N),
    ])
    white = np.array([210, 215, 255], float)
    blue = np.array([70, 110, 255], float)
    col = lerp_colors(blue, white, N)
    return local, col


def build_sphere():
    d = rng.normal(size=(N, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    r = 120 * rng.random(N) ** (1 / 3)
    local = d * r[:, None]
    col = lerp_colors(np.array([255, 50, 60], float), np.array([255, 150, 160], float), N)
    return local, col


def build_heart():
    """Hati (hanya garis tepi) dari partikel - kepalan tangan."""
    t = np.linspace(0, 2 * math.pi, 4000)
    hx = 16 * np.sin(t) ** 3
    hy = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    sc = HEART_SIZE
    cx, cy = hx * sc, -(hy - 2) * sc
    # sebar partikel merata sepanjang garis (berdasarkan panjang busur)
    seg = np.hypot(np.diff(cx), np.diff(cy))
    arc = np.concatenate([[0], np.cumsum(seg)])
    u = rng.uniform(0, arc[-1], N)
    x = np.interp(u, arc, cx) + rng.normal(0, HEART_SIZE * 0.07, N)
    y = np.interp(u, arc, cy) + rng.normal(0, HEART_SIZE * 0.07, N)
    z = rng.normal(0, HEART_SIZE * 0.1, N)
    local = np.column_stack([x, y, z])
    col = lerp_colors(np.array([255, 35, 85], float), np.array([255, 110, 150], float), N)
    return local, col


_point = {}


def build_point():
    """Planet bercincin (jempol): bola berpita + 3 pita cincin yang mengorbit."""
    R = 90.0
    n_core = int(N * 0.55)
    n_ring = N - n_core

    # bola: titik tersebar merata (Fibonacci sphere)
    i = np.arange(n_core) + 0.5
    phi = np.arccos(1 - 2 * i / n_core)
    th = math.pi * (1 + 5 ** 0.5) * i
    core = np.column_stack([
        R * np.sin(phi) * np.cos(th),
        R * np.cos(phi),
        R * np.sin(phi) * np.sin(th),
    ]) + rng.normal(0, 0.6, (n_core, 3))
    lat = core[:, 1] / R
    band = (0.5 + 0.5 * np.sin(lat * 8.0 + 0.6 * np.sin(lat * 3.0)))[:, None]
    col_core = np.array([255, 135, 20], float) + (np.array([255, 205, 95], float) - np.array([255, 135, 20], float)) * band
    col_core += rng.normal(0, 6, col_core.shape)

    # cincin: 3 pita dengan celah di antaranya
    bands = [(1.45, 1.66, 0.22, (255, 215, 130)),
             (1.74, 2.02, 0.40, (240, 170, 70)),
             (2.10, 2.40, 0.38, (205, 135, 55))]
    rad, cols = [], []
    for k, (r0, r1, share, c) in enumerate(bands):
        n = n_ring - sum(len(r) for r in rad) if k == len(bands) - 1 else int(n_ring * share)
        rad.append(np.sqrt(rng.uniform(r0 ** 2, r1 ** 2, n)) * R)
        cols.append(np.tile(np.array(c, float), (n, 1)) + rng.normal(0, 8, (n, 3)))
    rad = np.concatenate(rad)
    col_ring = np.vstack(cols)

    _point["core"] = core
    _point["rad"] = rad
    _point["ang"] = rng.uniform(0, 2 * math.pi, n_ring)
    _point["yoff"] = rng.normal(0, 0.9, n_ring)
    _point["speed"] = (1.45 * R / rad) ** 1.5

    local = point_local(0.0)
    return local, np.clip(np.vstack([col_core, col_ring]), 0, 255)


def point_local(t):
    """Posisi planet + cincin pada waktu t (bola berputar, cincin mengorbit)."""
    core = rotate_y(_point["core"], t * 0.7)
    ang = _point["ang"] + t * 0.9 * _point["speed"]
    rad = _point["rad"]
    x = np.cos(ang) * rad
    z = np.sin(ang) * rad
    y = _point["yoff"]
    tilt = 0.42                       # kemiringan cincin
    ct, st = math.cos(tilt), math.sin(tilt)
    y2 = y * ct - z * st
    z2 = y * st + z * ct
    roll = -0.30                      # miring diagonal ala Saturnus
    cr, sr = math.cos(roll), math.sin(roll)
    ring = np.column_stack([x * cr - y2 * sr, x * sr + y2 * cr, z2])
    return np.vstack([core, ring])


def build_text(text, frac, c1, c2):
    font = pygame.font.SysFont("arialblack", 220)
    surf = font.render(text, True, (255, 255, 255))
    alpha = pygame.surfarray.array_alpha(surf)
    pts = np.argwhere(alpha > 160).astype(float)  # (x, y)
    x0, x1 = pts[:, 0].min(), pts[:, 0].max()
    y0, y1 = pts[:, 1].min(), pts[:, 1].max()
    bw, bh = x1 - x0, y1 - y0
    # ambil titik merata tanpa duplikat supaya huruf tajam & jelas
    pick = rng.choice(len(pts), N, replace=len(pts) < N)
    xy = pts[pick]
    fit = min((W * frac) / bw, (H * 0.55) / bh)   # sebesar mungkin tapi tetap muat
    local = np.column_stack([
        (xy[:, 0] - (x0 + x1) / 2) * fit,
        (xy[:, 1] - (y0 + y1) / 2) * fit,
        rng.normal(0, 1.5, N),
    ])
    col = lerp_colors(np.array(c1, float), np.array(c2, float), N)
    return local, col


def rotate_y(p, a):
    c, s = math.cos(a), math.sin(a)
    x = p[:, 0] * c + p[:, 2] * s
    z = -p[:, 0] * s + p[:, 2] * c
    return np.column_stack([x, p[:, 1], z])


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
def main():
    global W, H, S
    pygame.init()
    try:
        dw, dh = pygame.display.get_desktop_sizes()[0]
    except Exception:
        dw, dh = 1366, 768
    wa = get_work_area() or (0, 0, dw, dh - 48)
    px = CAM_W + 40                       # mulai tepat di kanan jendela kamera
    W = max(400, wa[2] - px - 16)         # sampai tepi kanan layar
    H = max(400, (wa[3] - wa[1]) - 44)    # sampai atas taskbar
    S = min(W, H) / 620.0
    os.environ["SDL_VIDEO_WINDOW_POS"] = f"{px},{wa[1] + 36}"
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Particles")
    label_font = pygame.font.SysFont("consolas", 18)
    print("[INFO] Jendela Pygame dibuat:", screen.get_size(), "di x =", px)
    clock = pygame.time.Clock()

    shapes = {
        "open": build_scatter(),
        "none": None,  # diisi di bawah
    }
    heart = build_heart()
    for g in HEART_GESTURES:
        shapes[g] = heart
    for g, (txt, frac, c1, c2) in TEXTS.items():
        shapes[g] = build_text(txt, frac, c1, c2)
    shapes["thumb"] = build_point()
    shapes["none"] = shapes["open"]

    threading.Thread(target=camera_loop, daemon=True).start()

    cv2.namedWindow("Hand Sensor Monitor", cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow("Hand Sensor Monitor", 20, 60)

    pos = rng.uniform(-300, 300, (N, 3))
    vel = np.zeros((N, 3))
    cur_col = shapes["open"][1].copy()
    angle = 0.0
    off = np.zeros(2)
    scatter_local = shapes["open"][0].copy()

    writer, rec_start, rec_written = None, 0.0, 0
    while shared_data["running"]:
        toggle_rec = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                shared_data["running"] = False
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_q):
                shared_data["running"] = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                toggle_rec = True

        # tampilkan kamera
        frame = shared_data["frame"]
        if frame is not None:
            cv2.imshow("Hand Sensor Monitor", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            shared_data["running"] = False
        if key == ord("r"):
            toggle_rec = True

        gesture = shared_data["gesture"]
        is_scatter = gesture in ("open", "none")
        local, tcol = shapes[gesture]

        if is_scatter:
            scatter_local += rng.normal(0, 0.8, scatter_local.shape)
            local = scatter_local

        # posisi bentuk mengikuti tangan
        hx, hy = shared_data["hand"]
        want = np.array([(hx - 0.5) * W * 0.9, (hy - 0.5) * H * 0.9])
        if is_scatter:
            want[:] = 0
        if gesture in TEXTS:   # teks jangan sampai terpotong tepi jendela
            frac = TEXTS[gesture][1]
            lim = max(0.0, (1 - frac) / 2 * W - 20)
            want[0] = np.clip(want[0], -lim, lim)
            want[1] = np.clip(want[1], -0.2 * H, 0.2 * H)
        off += (want - off) * 0.08

        is_heart = gesture in HEART_GESTURES
        angle += 0.02 if is_heart else 0.012
        if gesture in TEXTS or gesture == "thumb":
            a = 0.0
        elif is_heart and not HEART_SPIN:
            a = 0.55 * math.sin(time.time() * 1.5)
        else:
            a = angle
        if gesture == "thumb":
            local = point_local(time.time())
        target = rotate_y(local, a)
        if not is_scatter and gesture not in TEXTS:
            target *= S
        if is_heart:   # detak jantung
            target *= 1.0 + 0.06 * math.sin(time.time() * 6)
        target[:, 0] += off[0]
        target[:, 1] += off[1]

        # fisika partikel
        if gesture in TEXTS:        # teks: kuat menarik, sedikit getar -> tajam
            pull, damp, noise = 0.16, 0.76, 0.05
        elif gesture == "thumb":    # planet: rapi, hampir tanpa getar
            pull, damp, noise = 0.22, 0.68, 0.03
        elif is_heart:              # hati
            pull, damp, noise = 0.20, 0.70, 0.02
        elif is_scatter:
            pull, damp, noise = 0.012, 0.86, 0.45
        else:
            pull, damp, noise = 0.05, 0.86, 0.45
        vel += (target - pos) * pull
        vel *= damp
        vel += rng.normal(0, noise, vel.shape)
        pos += vel
        cur_col += (tcol - cur_col) * 0.07

        # proyeksi 3D -> 2D
        f = 650.0 * S
        scale = f / np.clip(f + pos[:, 2], 100 * S, None)
        sx = (W / 2 + pos[:, 0] * scale).astype(int)
        sy = (H / 2 + pos[:, 1] * scale).astype(int)
        bright = np.clip(scale, 0.45, 1.3)[:, None]
        if gesture == "thumb":   # sisi depan terang, sisi belakang redup -> terlihat 3D
            bright = np.clip(0.95 - 0.45 * pos[:, 2] / (160 * S), 0.35, 1.2)[:, None]
        colors = np.clip(cur_col * bright, 0, 255).astype(np.uint8)

        buf = np.zeros((W, H, 3), dtype=np.uint8)
        ps = 3 if (S >= 1.3 and gesture in ("one", "open", "none")) else 2   # ukuran titik partikel
        ok = (sx >= 0) & (sx < W - ps) & (sy >= 0) & (sy < H - ps)
        zz = pos[:, 2][ok]
        order = np.argsort(-zz)          # gambar yang jauh dulu, yang dekat terakhir
        sx, sy, colors = sx[ok][order], sy[ok][order], colors[ok][order]
        if is_heart:   # cahaya (glow) neon di sekeliling garis hati
            gc = (colors * 0.30).astype(np.uint8)
            for dx in range(-2, 4):
                for dy in range(-2, 4):
                    buf[np.clip(sx + dx, 0, W - 1), np.clip(sy + dy, 0, H - 1)] = gc
        for dx in range(ps):
            for dy in range(ps):
                buf[sx + dx, sy + dy] = colors

        screen.fill((0, 0, 0))
        screen.blit(pygame.surfarray.make_surface(buf), (0, 0))
        screen.blit(label_font.render(f"Gesture: {gesture}", True, (0, 255, 0)), (10, 8))

        # ---- rekam video (tekan R) ----
        if toggle_rec:
            if writer is None:
                cam_w = int(CAM_W * H / CAM_H) if RECORD_WITH_CAMERA else 0
                out_w, out_h = (cam_w + W) // 2 * 2, H // 2 * 2
                writer, rec_path = make_writer(out_w, out_h)
                rec_start, rec_written = time.time(), 0
                print("[REC] Mulai merekam ->", rec_path)
            else:
                writer.release()
                writer = None
                print("[REC] Selesai. Video tersimpan di:", rec_path)
        if writer is not None:
            expected = int((time.time() - rec_start) * RECORD_FPS) + 1
            frame_img = compose_frame(
                cv2.cvtColor(np.ascontiguousarray(buf.transpose(1, 0, 2)), cv2.COLOR_RGB2BGR),
                shared_data["frame"], out_w, out_h)
            for _ in range(min(3, max(0, expected - rec_written))):   # jaga kecepatan video tetap normal
                writer.write(frame_img)
                rec_written += 1
            secs = int(time.time() - rec_start)
            pygame.draw.circle(screen, (255, 40, 40), (W - 110, 18), 7)
            screen.blit(label_font.render(f"REC {secs // 60:02d}:{secs % 60:02d}", True, (255, 80, 80)), (W - 95, 8))
        pygame.display.flip()

        if RENDER_IN_OPENCV:
            img = cv2.cvtColor(np.ascontiguousarray(buf.transpose(1, 0, 2)), cv2.COLOR_RGB2BGR)
            cv2.imshow("Particles", img)
        clock.tick(60)

    if writer is not None:
        writer.release()
    pygame.quit()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()