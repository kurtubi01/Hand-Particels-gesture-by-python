# ✋ Hand Gesture Particles

Partikel interaktif yang berubah bentuk mengikuti **gesture tangan** kamu, dideteksi langsung dari webcam secara real-time.

Angkat 1 jari, muncul tulisan. Acungkan jempol, muncul planet bercincin. Kepalkan tangan, muncul hati neon. Semua bergerak mengikuti posisi tanganmu.

> 📸 Tambahkan screenshot atau GIF hasilnya di sini, misalnya `![demo](screenshots/demo.gif)`

---

## ✨ Fitur

- Deteksi tangan real-time memakai **MediaPipe Hands**
- Hingga **8000 partikel** dengan efek 3D, glow, dan detak jantung
- 6 gesture dengan bentuk partikel berbeda
- Jendela partikel otomatis menyesuaikan layar (menempel di sebelah kanan jendela kamera)
- **Rekam video** langsung dari program (tekan `R`), hasilnya tajam tanpa blur

---

## 🖐️ Daftar Gesture

| Gesture | Hasil |
|---|---|
| 🖐️ 5 jari (telapak terbuka) | Titik biru/putih menyebar |
| ☝️ 1 jari (telunjuk) | Tulisan **Vrizi** |
| ✌️ 2 jari (telunjuk + tengah) | Tulisan **I LOVE YOU** |
| 🤟 3 jari (telunjuk + tengah + manis) | Bentuk **hati** neon |
| ✊ Kepalan | Bentuk **hati** neon |
| 👍 Jempol | **Planet bercincin** oranye |

---

## 🧰 Kebutuhan

- Windows 10/11 (sudah dites di Windows)
- **Python 3.10** (disarankan, sama dengan yang dipakai saat pengembangan)
- Webcam
- Library: `numpy`, `opencv-contrib-python`, `mediapipe`, `pygame` (lihat `requirements.txt`)

> ⚠️ Versi library sengaja dikunci. `mediapipe 0.10.14` hanya cocok dengan `numpy 1.x`, dan `mp.solutions.hands` sudah dihapus di mediapipe versi baru.

---

## 🚀 Cara Install

### 1. Clone repository

```bash
git clone https://github.com/USERNAME/hand-gesture-particles.git
cd hand-gesture-particles
```

Atau klik **Code → Download ZIP**, ekstrak, lalu buka folder hasil ekstraknya di CMD.

### 2. Buat virtual environment (disarankan)

```bash
python -m venv venv
venv\Scripts\activate
```

Kalau berhasil, di depan baris terminal muncul `(venv)`.

### 3. Update pip

```bash
python -m pip install --upgrade pip
```

### 4. Install semua library

```bash
pip install -r requirements.txt
```

Atau satu per satu, **urutannya jangan diubah**:

```bash
pip install "numpy==1.26.4"
pip install "opencv-contrib-python==4.10.0.84"
pip install "mediapipe==0.10.14"
pip install "ml_dtypes==0.5.1"
pip install "pygame==2.6.1"
```

### 5. Cek instalasi

```bash
python -c "import cv2, mediapipe, numpy, pygame; print(cv2.__version__, numpy.__version__, mediapipe.__version__)"
```

Hasil yang benar kira-kira:

```
4.10.0 1.26.4 0.10.14
```

---

## ▶️ Cara Menjalankan

```bash
python hand.py
```

Dua jendela akan muncul:

1. **Hand Sensor Monitor**: kamera, garis tangan, dan status gesture (teks hijau)
2. **Particles**: partikel yang berubah sesuai gesture

Arahkan tangan ke kamera dengan cahaya yang cukup, lalu coba setiap gesture.

### Kontrol keyboard

| Tombol | Fungsi |
|---|---|
| `R` | Mulai / stop rekam video |
| `Q` atau `ESC` | Keluar |

---

## 🎥 Cara Merekam Video

1. Jalankan program, lalu tekan **R**. Di pojok kanan atas jendela partikel muncul `● REC 00:05`.
2. Tekan **R** lagi untuk berhenti.
3. Video tersimpan di folder `rekaman/` dengan nama seperti `partikel_20261003_190501.mp4`.

Isi video berupa kamera (kiri) dan partikel (kanan), 30 FPS. Kalau mau partikelnya saja, ubah `RECORD_WITH_CAMERA = False` di bagian atas `index.py`.

> Ukuran file cukup besar (sekitar 6 MB per detik) karena titik-titik kecil sulit dikompres. Itu yang menjaga hasilnya tetap tajam.

---

## ⚙️ Kustomisasi

Semua pengaturan ada di bagian atas `index.py`.

| Pengaturan | Fungsi |
|---|---|
| `N = 8000` | Jumlah partikel (turunkan ke `5000` kalau terasa berat) |
| `HEART_SIZE = 12` | Ukuran hati (6 kecil, 12 besar, 15 sangat besar) |
| `HEART_SPIN = False` | `True` = hati berputar 360°, `False` = bergoyang kiri-kanan |
| `RECORD_WITH_CAMERA = True` | Rekaman menyertakan kamera atau tidak |
| `RECORD_FPS = 30` | Frame rate video rekaman |
| `CAM_INDEX = 0` | Nomor kamera (ganti ke `1` kalau kamera tidak muncul) |
| `RENDER_IN_OPENCV = False` | `True` = partikel tampil di jendela OpenCV (cadangan kalau jendela Pygame bermasalah) |

### Mengganti tulisan dan warna

Edit dictionary `TEXTS`:

```python
TEXTS = {
    "one": ("Vrizi", 0.55, (40, 200, 255), (170, 240, 255)),
    "two": ("I LOVE YOU", 0.70, (40, 200, 255), (170, 240, 255)),
}
```

Isinya berurutan: `(tulisan, lebar relatif jendela, warna awal RGB, warna akhir RGB)`.

---

## 🛠️ Troubleshooting

**`ERROR: Could not find a version that satisfies the requirement 4.10.0.84`**
Tanda `==` hilang atau berubah saat copy-paste. Beri tanda kutip pada nama paket, misalnya `pip install "opencv-contrib-python==4.10.0.84"`.

**Konflik versi numpy atau OpenCV**
Uninstall dulu semua, lalu install ulang sesuai urutan di atas:

```bash
pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless mediapipe pygame numpy ml_dtypes jax jaxlib protobuf
```

**Kamera tidak muncul**
Ubah `CAM_INDEX = 0` menjadi `1`, dan pastikan kamera tidak dipakai aplikasi lain (Zoom, Meet, dll).

**Jendela partikel tidak muncul atau hitam**
Cek ikon Python kedua di taskbar. Kalau tetap bermasalah, ubah `RENDER_IN_OPENCV = True`.

**Gesture tidak terbaca**
Pastikan cahaya cukup dan telapak tangan menghadap kamera. Untuk 3 jari, kelingking harus benar-benar dilipat. Untuk jempol, julurkan jempol lurus dan lipat keempat jari lainnya.

**Peringatan merah `SymbolDatabase` / `feedback_manager` di terminal**
Itu hanya peringatan dari mediapipe dan tidak mengganggu program.

**Terasa lag**
Turunkan `N` di `index.py`.

---

## 📁 Struktur Project

```
hand-gesture-particles/
├── index.py            # program utama
├── requirements.txt    # daftar library
├── README.md           # dokumentasi ini
└── rekaman/            # hasil rekaman video (dibuat otomatis)
```

---

## 🧠 Cara Kerja Singkat

1. **Thread kamera** membaca webcam, lalu MediaPipe mendeteksi 21 titik landmark tangan.
2. Jari yang terangkat dihitung dari jarak ujung jari ke pergelangan tangan, lalu dipetakan ke gesture.
3. **Loop utama (Pygame)** menggerakkan ribuan partikel menuju bentuk target memakai fisika sederhana (tarikan, peredam, dan getaran kecil).
4. Posisi 3D diproyeksikan ke 2D, lalu digambar dengan NumPy.

---

## 🙏 Teknologi

- [MediaPipe](https://developers.google.com/mediapipe): deteksi tangan
- [OpenCV](https://opencv.org/): kamera dan perekaman video
- [Pygame](https://www.pygame.org/): tampilan partikel
- [NumPy](https://numpy.org/): perhitungan partikel

---

## 📄 Lisensi

Tambahkan lisensi sesuai keinginanmu, misalnya [MIT](https://choosealicense.com/licenses/mit/).
