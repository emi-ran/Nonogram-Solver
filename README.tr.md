# 🧩 Nonogram Solver & Otomatik Oynatıcı (Auto-Player)

<p align="center">
  <a href="README.md">English</a> •
  <a href="README.tr.md"><b>Türkçe</b></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-green.svg" alt="OpenCV">
  <img src="https://img.shields.io/badge/ADB-Android%20Automation-orange.svg" alt="ADB">
  <img src="https://img.shields.io/badge/License-MIT-purple.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Tests-23%20Passing-brightgreen.svg" alt="Tests">
</p>

Android cihazlarda çalışan popüler **Nonogram.com** oyunları için geliştirilmiş; bilgisayarlı görü (Computer Vision), hızlı kısıt yayılımı (Constraint Propagation) ve ADB otomasyonunu birleştiren **yüksek performanslı dinamik çözücü ve otonom oynatıcı**.

---

## 🌟 Öne Çıkan Özellikler

- 👁️ **Dinamik Izgara ve İpucu Algılama:** Ekran görüntüsündeki Nonogram ızgara boyutunu (5x5, 10x10, 15x15, 20x20 vb.) ve satır/sütun sayı ipuçlarını OpenCV şablon eşleme ve kontur analiziyle sıfır hata ile okur.
- ⚡ **Işık Hızında Çözüm Motoru:** Dinamik programlama (memoized line-solver) ve kısıt yayılımı ile 20x20 Expert tahtaları bile **< 15 milisaniye** içinde çözer.
- 📱 **Sıfır Gecikmeli Toplu Tıklama (Batch ADB):** Tüm dokunma komutlarını tek bir interaktif ADB shell oturumunda göndererek gecikmeyi sıfıra indirir.
- 🤖 **Tam Otonom Oyun Döngüsü:**
  - **Normal Mod:** Bölümleri ardı ardına çözer, sonraki bölüme geçer, menüleri yönetir.
  - **Günün Mücadelesi (Daily):** Günlük görevleri çözer ve tüm görevler bittiğinde otomatik durur.
  - **Lilac Roses & Özel Etkinlikler:** Turuncu hikaye haritası, ödül pencereleri ve ara animasyonları algılayarak etkinlikleri kesintisiz tamamlar.
- 🎨 **Akıllı Tıklama Desenleri (`--random [MODE]`):**
  - `random`: Tamamen rastgele karıştırılmış insan benzeri dokunma.
  - `ping_pong`: Bir baştan (sol üst), bir sondan (sağ alt) ortaya doğru buluşan dokunma.
  - `center_out`: Merkezden dışarı doğru halka/daire dalgaları halinde yayılan dokunma.
  - `reverse`: Tersten (sağ alttan sol üste) dokunma.
  - `snake`: Satır satır yön değiştiren zigzag / yılan dokunma.
- 🔋 **Cihaz Yönetimi:** Ekran kapalıysa uyandırır, kilit ekranını kaydırarak açar ve oyunu otomatik başlatır. Birden fazla cihaz bağlıysa interaktif seçim menüsü sunar.

---

## 📋 Gereksinimler

1. **Python 3.9+**
2. **Android Debug Bridge (ADB)** yüklü ve `PATH` ortam değişkenine ekli olmalıdır.
3. Android telefonunuzda **Geliştirici Seçenekleri** ve **USB Hata Ayıklama (USB Debugging)** açık olmalıdır.

### Kurulum

```powershell
# Depoyu klonlayın
git clone https://github.com/emi-ran/Nonogram-Solver.git
cd Nonogram-Solver

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

---

## 🚀 Kullanım Kılavuzu

### 1. Otonom Oyun Modları (`--auto`)

Botun sürekli olarak ekranı okuyup, çözüp, sonraki bölüme geçmesini sağlar:

```powershell
# 1. Normal (Klasik) Mod:
python main.py --auto --mode normal

# 2. Günlük Görevler Modu (Daily Challenges):
python main.py --auto --mode daily
# Belirli bir bölüm hedefi ile:
python main.py --auto --mode daily --max-levels 5

# 3. Lilac Roses Etkinlik Modu:
python main.py --auto --mode lilac
# veya
python main.py --auto --mode lilac_roses

# 4. Diğer Etkinlikler (Rise & Dice, Adventure):
python main.py --auto --mode event
```

---

### 2. Tıklama Desenleri (`--random [MODE]`)

Çözülen karelerin ekrana hangi sırayla basılacağını belirleyebilirsiniz:

```powershell
# İki uçtan merkeze doğru buluşarak:
python main.py --auto --mode lilac --random ping_pong

# Merkezden dışa doğru halkalar halinde yayılarak:
python main.py --auto --mode lilac --random center_out

# Tersten (sağ alttan sol üste):
python main.py --auto --mode lilac --random reverse

# Zigzag / Yılan şeklinde:
python main.py --auto --mode lilac --random snake

# Tamamen rastgele karıştırarak:
python main.py --auto --mode lilac --random
```

---

### 3. Tek Bölüm Çözme & Geliştirici Araçları

```powershell
# Mevcut ekrandaki tahtayı tek seferlik çöz ve tıkla:
python main.py --apply
python main.py --apply --random center_out

# Sadece çözüm analizini gör (dokunma yapmaz / kuru deneme):
python main.py

# Cihazdan anlık ekran görüntüsü alıp çık:
python main.py --screenshot
python main.py --screenshot my_screen.png

# Çevrimdışı yerel bir görsel dosyasını çöz:
python main.py --offline assets/samples/Hard.png
```

---

## 📂 Proje Mimarisi

```text
Nonogram-Solver/
├── assets/
│   └── samples/                 # Test ve şablon görselleri
├── src/
│   └── nonogram/
│       ├── automation/
│       │   ├── auto_player.py   # Otonom oyun döngüsü orkestratörü
│       │   ├── patterns.py      # Tıklama desenleri (Ping-Pong, Center-Out vb.)
│       │   ├── runner.py        # Uçtan uca pipeline çalıştırıcı
│       │   ├── states.py        # Durum makinesi (Board, Menu, Completed vb.)
│       │   └── modes/           # Mod stratejileri (Normal, Daily, Events)
│       ├── device/
│       │   └── adb.py           # ADB kontrolörü, kilit açma & toplu dokunma
│       ├── solver/
│       │   ├── engine.py        # Nonogram kısıt yayılım çözücüsü
│       │   └── models.py        # Bulmaca ve düzen veri modelleri
│       └── vision/
│           ├── grid.py          # Izgara çizgisi ve koordinat çıkarma
│           ├── ocr.py           # Sayı ipuçlarını okuma motoru
│           └── templates.py     # OCR sayı şablonları
├── tests/                       # Kapsamlı birim ve entegrasyon testleri (23 test)
├── DEVELOPMENT.md               # Detaylı teknik geliştirici dokümantasyonu
├── main.py                      # Sade ve zengin CLI giriş noktası
└── requirements.txt
```

---

## 🧪 Testleri Çalıştırma

Tüm test paketini çalıştırmak için:

```powershell
python -m unittest discover -s tests
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.
