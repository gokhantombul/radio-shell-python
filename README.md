# ♬ Radio Shell

**Terminal üzerinden Türkiye ve Dünya FM radyo istasyonlarını dinleyin.**

```
  ╔══════════════════════════════════════════════════════════════╗
  ║   ♬  ░░░ RADIO SHELL ░░░  ♬                                  ║
  ║   Terminal FM Radio Player - Türkiye & Dünya                 ║
  ║   Python 3.10+ · prompt_toolkit · rich                       ║
  ╚══════════════════════════════════════════════════════════════╝
```

---

## Gereksinimler

| Araç | Sürüm | Kurulum |
|------|-------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| ffmpeg (ffplay) | Herhangi | Aşağıya bakın |

**ffmpeg kurulumu:**

| Platform | Komut |
|----------|-------|
| macOS | `brew install ffmpeg` |
| Arch Linux | `sudo pacman -S ffmpeg` |
| Ubuntu / Debian | `sudo apt install ffmpeg` |
| Fedora | `sudo dnf install ffmpeg` |
| Windows | `winget install Gyan.FFmpeg` |

---

## Kurulum ve Çalıştırma

### Yöntem 1 — Tek seferlik çalıştırma

```bash
git clone https://github.com/kullanici/radio-shell-python.git
cd radio-shell-python

# Linux / macOS
chmod +x radio.sh
./radio.sh

# Windows (cmd veya PowerShell)
radio.bat
```

`radio.sh` / `radio.bat` ilk çalıştırmada Python sanal ortamı oluşturur ve bağımlılıkları otomatik yükler.

---

### Yöntem 2 — `radio` komutunu globale al

Kurulumdan sonra her terminalden sadece `radio` yazarak uygulamayı açabilirsiniz.

**Linux / macOS:**

```bash
./radio.sh --install
# → /usr/local/bin/radio veya ~/.local/bin/radio sembolik bağlantısı oluşturulur

radio   # artık her yerden çalışır

# Kaldırmak için:
./radio.sh --uninstall
```

> `~/.local/bin` PATH'te yoksa `radio.sh --install` sizi bilgilendirir ve hangi satırı ekleyeceğinizi gösterir.

**Windows (cmd veya PowerShell):**

```batch
radio.bat --install
:: → %USERPROFILE%\.local\bin\radio.bat oluşturulur

:: Klasörü kalıcı olarak PATH'e ekleyin (bir kez yeterli):
setx PATH "%PATH%;%USERPROFILE%\.local\bin"

:: Yeni terminal açın:
radio

:: Kaldırmak için:
radio.bat --uninstall
```

---

### Yöntem 3 — Docker

```bash
# Tek komutla build & çalıştır
./docker-run.sh

# Veya docker compose ile
docker compose up --build

# Veya manuel
docker build -t radio-shell .
docker run --rm -it \
  -v ~/.radio-shell:/root/.radio-shell \
  radio-shell
```

> **macOS + Docker Ses Notu:** macOS'ta Docker container'ı ses cihazına doğrudan erişemez.
> Tam ses desteği için `./radio.sh` ile doğrudan terminalde çalıştırmanız önerilir.
> Linux'ta Docker içinden ses sorunsuz çalışır (`/dev/snd` mount ile).

---

## Komut Referansı

### İstasyon Listeleme

| Komut | Açıklama |
|-------|----------|
| `listele` | İlk 50 istasyonu listeler (varsayılan) |
| `listele -n 20` | İlk 20 istasyonu listeler |
| `listele --hepsi` | Tüm 90+ istasyonu listeler |
| `turkiye` | Sadece Türkiye istasyonlarını listeler |
| `ulkeler` | Mevcut ülkeleri ve istasyon sayılarını gösterir |
| `ulke -i <ülke>` | Belirli bir ülkenin istasyonları |
| `turler` | Mevcut müzik türlerini listeler |
| `tur -i <tür>` | Belirli bir türdeki istasyonlar |
| `ara -s <kelime>` | İsim, ülke veya türe göre arama |
| `online-ara -s <kelime>` | radio-browser.info üzerinden online arama |

### Oynatma

| Komut | Açıklama |
|-------|----------|
| `cal -i <id>` | İstasyonu çalar (ID veya isim) |
| `son` | Son çalınan istasyonu tekrar çalar |
| `dur` | Çalmayı durdurur |
| `durum` | Şu an çalan istasyonu ve şarkı bilgisini gösterir |
| `ses -s <0-100>` | Ses seviyesini ayarlar |
| `sonraki` | Son listede bir sonraki istasyona geçer |
| `onceki` | Son listede bir önceki istasyona geçer |
| `karistir [-u ülke] [-t tür] [-f]` | Rastgele istasyon çalar |
| `uyku -d <dakika>` | Süre sonunda oynatmayı durdurur |
| `uyku iptal` | Uyku zamanlayıcısını iptal eder |
| `gecmis [-n adet]` | Son görülen şarkı bilgilerini listeler |

### Kayıt

| Komut | Açıklama |
|-------|----------|
| `kaydet` | Çalan yayını MP3 olarak kaydetmeye başlar |
| `kayitdur` | Aktif kaydı durdurur |

### Favoriler

| Komut | Açıklama |
|-------|----------|
| `favori -i <id>` | İstasyonu favorilere ekler / çıkarır (★) |
| `favoriler` | Favori istasyon listesi |

### Yönetim

| Komut | Açıklama |
|-------|----------|
| `ekle --id <id> --isim <isim> --ulke <ülke> --tur <tür> --url <url>` | Yeni özel istasyon ekler |
| `duzenle --id <id> [--isim ...] [--ulke ...] [--tur ...] [--url ...]` | Özel istasyonu düzenler |
| `sil --id <id>` | Özel istasyonu siler |
| `online-ekle -i <id>` | radio-browser.info'dan istasyon ekler |
| `iceaktar -d <dosya.m3u\|dosya.pls> [-u ülke] [-t tür] [-p önek]` | Playlist'ten özel istasyon ekler |
| `kontrol [-i <id>]` | Akış URL'lerini kontrol eder |
| `tema [-i <tema>]` | Renk temasını listeler veya değiştirir |
| `bildirim` | Masaüstü bildirimlerini açar / kapatır |
| `istatistik` | Dinleme istatistiklerini gösterir |
| `sistem` | Sistem ve RAM kullanım bilgilerini gösterir |
| `temizle` | Terminal ekranını temizler |

### Diğer

| Komut | Açıklama |
|-------|----------|
| `help` / `?` | Yardım menüsünü gösterir |
| `exit` / `q` | Uygulamadan çıkar |

---

## Kullanım Örnekleri

```
# Power FM'i çal
radio> cal -i tr-powerfm

# TRT FM'i çal
radio> cal -i tr-trt-fm

# Jazz istasyonu ara
radio> ara -s jazz

# BBC Radio listele
radio> ulke -i UK

# Ses seviyesini 70'e ayarla
radio> ses -s 70

# Son çalınan istasyonu yeniden başlat
radio> son

# 30 dakika sonra otomatik durdur
radio> uyku -d 30

# M3U playlist içe aktar
radio> iceaktar -d ~/Downloads/radyolar.m3u -u Özel -t Karma

# Power FM'i favorilere ekle
radio> favori -i tr-powerfm

# Özel istasyon ekle
radio> ekle --id benim-radyom --isim "Benim Radyom" --ulke Türkiye --tur Pop --url http://stream.example.com/live

# Durdur
radio> dur
```

---

## Dahili İstasyonlar (90+)

### Türkiye
| İstasyon | Tür | ID |
|----------|-----|----|
| TRT FM | Pop/Türkçe | `tr-trt-fm` |
| TRT Radyo 1 | Haber/Kültür | `tr-trt-radyo1` |
| TRT Radyo 3 | Klasik/Caz | `tr-trt-radyo3` |
| TRT Nağme | Türk Halk Müziği | `tr-trt-nagme` |
| TRT Kurdî | Kürtçe | `tr-trt-kurdi` |
| PowerTürk | Türkçe Pop | `tr-powerturk` |
| Power FM | Pop/Dance | `tr-powerfm` |
| Kral FM | Türkçe Pop | `tr-kralmuzik` |
| Kral Pop | Pop | `tr-kralpop` |
| SlowTürk | Slow/Romantik | `tr-slowturk` |
| JoyTürk | Rock/Alternatif | `tr-joyturk` |
| Joy FM | Yabancı Pop | `tr-joyfm` |
| Süper FM | Türkçe Pop | `tr-superfm` |
| Best FM | Pop | `tr-bestfm` |
| Metro FM | Dance/Electronic | `tr-metro` |
| Radyo D | Pop | `tr-radyod` |
| Number One FM | Pop/Dance | `tr-numberone` |
| Radyo Eksen | Rock/Indie | `tr-radyoeksen` |
| Açık Radyo | Karma/Kültür | `tr-acikmuzik` |

### Dünya
| İstasyon | Ülke | Tür | ID |
|----------|------|-----|----|
| BBC Radio 1–4 | UK | Çeşitli | `uk-bbc-radio1` … |
| Classic FM | UK | Klasik | `uk-classicfm` |
| KEXP 90.3 FM | USA | Indie/Alt | `us-kexp` |
| Jazz24 | USA | Jazz | `us-jazz24` |
| SomaFM Groove Salad | USA | Ambient/Chill | `us-soma-groovesalad` |
| FIP Radio | Fransa | Eclectic | `fr-fip` |
| France Musique | Fransa | Klasik | `fr-francemusique` |
| SWR3 | Almanya | Pop/Rock | `de-swr3` |
| RAI Radio 2 | İtalya | Pop | `it-rai-radio2` |
| J-Wave | Japonya | Pop/Urban | `jp-jwave` |

---

## Yeni İstasyon Nasıl Eklenir?

**Uygulama içinden:**
```
radio> ekle --id my-station --isim "Benim Radyom" --ulke Türkiye --tur Pop --url http://stream.example.com/radio.mp3
```

**JSON dosyasıyla** (`~/.radio-shell/custom-stations.json`):
```json
{
  "stations": [
    {
      "id": "my-station",
      "name": "Benim Radyom",
      "country": "Türkiye",
      "genre": "Pop",
      "url": "http://stream.example.com/radio.mp3",
      "favorite": false
    }
  ]
}
```

---

## Proje Yapısı

```
radio-shell-python/
├── radio.sh                        # Linux/macOS başlatıcı (--install / --uninstall)
├── radio.bat                       # Windows başlatıcı    (--install / --uninstall)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── docker-run.sh
├── src/
│   ├── radio/
│   │   ├── main.py                 # Giriş noktası, servis bağlama
│   │   ├── shell.py                # prompt_toolkit REPL + otomatik tamamlama
│   │   ├── player.py               # ffplay süreç yönetimi, ICY metadata
│   │   ├── ui.py                   # rich konsol, 4 renk teması
│   │   ├── models.py               # RadioStation, UserSettings veri modelleri
│   │   ├── config.py               # RadioConfig (dizin yolları)
│   │   ├── commands_basic.py       # Listeleme & arama komutları
│   │   ├── commands_playback.py    # Oynatma komutları
│   │   ├── commands_management.py  # İstasyon yönetimi, tema, istatistik
│   │   └── services/
│   │       ├── station_service.py
│   │       ├── settings_service.py
│   │       ├── statistics_service.py
│   │       ├── radio_browser_service.py
│   │       ├── notification_service.py
│   │       └── system_service.py
│   └── main/resources/
│       └── stations.json           # 90+ dahili istasyon
└── tests/
```

---

## Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| Dil | Python 3.10+ |
| REPL / Tamamlama | prompt_toolkit |
| Terminal UI | rich |
| Ses Oynatıcı | ffplay (ffmpeg) |
| Kayıt | ffmpeg `-c copy` |
| Online Arama | radio-browser.info API |
| Sistem Bilgisi | psutil |
| Container | Docker (multi-stage) |

---

## Kalıcı Veri

Tüm kullanıcı verisi `~/.radio-shell/` altında saklanır:

```
~/.radio-shell/
├── favorites.json        # Favori istasyon ID'leri
├── custom-stations.json  # Kullanıcı tarafından eklenen istasyonlar
├── settings.json         # Ses seviyesi, son çalınan istasyon, bildirim ayarı
├── stats.json            # Dinleme istatistikleri
├── theme                 # Seçili renk teması
└── recordings/           # MP3 kayıtları
```

Docker kullanırken bu dizin volume olarak mount edilir; container yeniden başlatmalarında verileriniz korunur.

---

---

# ♬ Radio Shell — English

**Listen to FM radio stations from Turkey and around the world, directly from your terminal.**

---

## Requirements

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| ffmpeg (ffplay) | Any | See below |

**ffmpeg installation:**

| Platform | Command |
|----------|---------|
| macOS | `brew install ffmpeg` |
| Arch Linux | `sudo pacman -S ffmpeg` |
| Ubuntu / Debian | `sudo apt install ffmpeg` |
| Fedora | `sudo dnf install ffmpeg` |
| Windows | `winget install Gyan.FFmpeg` |

---

## Setup & Running

### Method 1 — One-off run

```bash
git clone https://github.com/user/radio-shell-python.git
cd radio-shell-python

# Linux / macOS
chmod +x radio.sh
./radio.sh

# Windows (cmd or PowerShell)
radio.bat
```

On first run, `radio.sh` / `radio.bat` automatically creates a Python virtual environment and installs dependencies.

---

### Method 2 — Install `radio` as a global command

After installation you can launch the app from any terminal by typing `radio`.

**Linux / macOS:**

```bash
./radio.sh --install
# → creates a symlink at /usr/local/bin/radio or ~/.local/bin/radio

radio   # works from anywhere now

# To uninstall:
./radio.sh --uninstall
```

> If `~/.local/bin` is not in your PATH, `radio.sh --install` will warn you and show the exact line to add for Bash, Zsh, or Fish.

**Windows (cmd or PowerShell):**

```batch
radio.bat --install
:: → creates %USERPROFILE%\.local\bin\radio.bat

:: Add that folder to PATH permanently (once):
setx PATH "%PATH%;%USERPROFILE%\.local\bin"

:: Open a new terminal, then:
radio

:: To uninstall:
radio.bat --uninstall
```

---

### Method 3 — Docker

```bash
# Build & run in one command
./docker-run.sh

# Or with docker compose
docker compose up --build

# Or manually
docker build -t radio-shell .
docker run --rm -it \
  -v ~/.radio-shell:/root/.radio-shell \
  radio-shell
```

> **macOS + Docker Audio Note:** Docker on macOS cannot directly access the audio device.
> For full audio support, run directly in terminal with `./radio.sh`.
> On Linux, audio works inside Docker containers (via `/dev/snd` mount).

---

## Command Reference

### Listing Stations

| Command | Description |
|---------|-------------|
| `listele` | List first 50 stations (default) |
| `listele -n 20` | List first 20 stations |
| `listele --hepsi` | List all 90+ stations |
| `turkiye` | List Turkish stations only |
| `ulkeler` | Show available countries and station counts |
| `ulke -i <country>` | Stations from a specific country |
| `turler` | List available music genres |
| `tur -i <genre>` | Stations of a specific genre |
| `ara -s <query>` | Search by name, country, or genre |
| `online-ara -s <query>` | Search radio-browser.info online |

### Playback

| Command | Description |
|---------|-------------|
| `cal -i <id>` | Play a station (by ID or name) |
| `son` | Play the last station again |
| `dur` | Stop playback |
| `durum` | Show currently playing station and song info |
| `ses -s <0-100>` | Set volume level |
| `sonraki` | Next station in the last list |
| `onceki` | Previous station in the last list |
| `karistir [-u country] [-t genre] [-f]` | Play a random station |
| `uyku -d <minutes>` | Stop playback after a delay |
| `uyku iptal` | Cancel the sleep timer |
| `gecmis [-n count]` | Show recent song metadata history |

### Recording

| Command | Description |
|---------|-------------|
| `kaydet` | Start recording the current stream as MP3 |
| `kayitdur` | Stop the active recording |

### Favorites

| Command | Description |
|---------|-------------|
| `favori -i <id>` | Toggle station as favorite (★) |
| `favoriler` | Show favorite stations list |

### Management

| Command | Description |
|---------|-------------|
| `ekle --id <id> --isim <name> --ulke <country> --tur <genre> --url <url>` | Add a custom station |
| `duzenle --id <id> [--isim ...] [--ulke ...] [--tur ...] [--url ...]` | Edit a custom station |
| `sil --id <id>` | Remove a custom station |
| `online-ekle -i <id>` | Add a station from radio-browser.info |
| `iceaktar -d <file.m3u\|file.pls> [-u country] [-t genre] [-p prefix]` | Import stations from a playlist |
| `kontrol [-i <id>]` | Check stream URLs |
| `tema [-i <theme>]` | List or change color theme |
| `bildirim` | Toggle desktop notifications |
| `istatistik` | Show listening statistics |
| `sistem` | Show system and RAM usage |
| `temizle` | Clear the terminal screen |

### Other

| Command | Description |
|---------|-------------|
| `help` / `?` | Show help menu |
| `exit` / `q` | Quit the application |

---

## Usage Examples

```
# Play Power FM
radio> cal -i tr-powerfm

# Play BBC Radio 1
radio> cal -i uk-bbc-radio1

# Search for jazz stations
radio> ara -s jazz

# List UK stations
radio> ulke -i UK

# Set volume to 70
radio> ses -s 70

# Play the last station again
radio> son

# Stop automatically after 30 minutes
radio> uyku -d 30

# Import an M3U playlist
radio> iceaktar -d ~/Downloads/stations.m3u -u Custom -t Mixed

# Add Power FM to favorites
radio> favori -i tr-powerfm

# Add a custom station
radio> ekle --id my-station --isim "My Radio" --ulke Turkey --tur Pop --url http://stream.example.com/live

# Stop playback
radio> dur
```

---

## Adding New Stations

**From within the app:**
```
radio> ekle --id my-station --isim "My Radio" --ulke Turkey --tur Pop --url http://stream.example.com/radio.mp3
```

**Via JSON file** (`~/.radio-shell/custom-stations.json`):
```json
{
  "stations": [
    {
      "id": "my-station",
      "name": "My Radio",
      "country": "Turkey",
      "genre": "Pop",
      "url": "http://stream.example.com/radio.mp3",
      "favorite": false
    }
  ]
}
```

---

## Project Structure

```
radio-shell-python/
├── radio.sh                        # Linux/macOS launcher (--install / --uninstall)
├── radio.bat                       # Windows launcher    (--install / --uninstall)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── docker-run.sh
├── src/
│   ├── radio/
│   │   ├── main.py                 # Entry point, service wiring
│   │   ├── shell.py                # prompt_toolkit REPL + tab completion
│   │   ├── player.py               # ffplay process management, ICY metadata
│   │   ├── ui.py                   # rich console, 4 color themes
│   │   ├── models.py               # RadioStation, UserSettings data models
│   │   ├── config.py               # RadioConfig (directory paths)
│   │   ├── commands_basic.py       # Listing & search commands
│   │   ├── commands_playback.py    # Playback commands
│   │   ├── commands_management.py  # Station management, themes, statistics
│   │   └── services/
│   │       ├── station_service.py
│   │       ├── settings_service.py
│   │       ├── statistics_service.py
│   │       ├── radio_browser_service.py
│   │       ├── notification_service.py
│   │       └── system_service.py
│   └── main/resources/
│       └── stations.json           # 90+ built-in stations
└── tests/
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| REPL / Completion | prompt_toolkit |
| Terminal UI | rich |
| Audio Player | ffplay (ffmpeg) |
| Recording | ffmpeg `-c copy` |
| Online Search | radio-browser.info API |
| System Info | psutil |
| Container | Docker (multi-stage) |

---

## Persistent Data

All user data is stored under `~/.radio-shell/`:

```
~/.radio-shell/
├── favorites.json        # Favorite station IDs
├── custom-stations.json  # User-added stations
├── settings.json         # Volume, last station, notification setting
├── stats.json            # Listening statistics
├── theme                 # Selected color theme
└── recordings/           # MP3 recordings
```

When using Docker, this directory is mounted as a volume so your data persists across container restarts.

---

## License

MIT License — free to use, modify, and distribute.
