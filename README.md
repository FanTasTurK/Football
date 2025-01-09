"""
# Sahadan.com Veri Toplama Uygulaması / Data Collection Application

[English version below | İngilizce versiyon aşağıda](#english)

## 🇹🇷 Türkçe

Bu uygulama, Selenium WebDriver kullanarak sahadan.com web sitesinden Premier Lig maç istatistiklerini otomatik olarak toplar ve yapılandırılmış CSV dosyalarına kaydeder.

### Teknik Özellikler

- Selenium WebDriver ile otomasyon
- Headless Firefox tarayıcı desteği
- uBlock Origin reklam engelleyici entegrasyonu
- Çoklu oturum yönetimi ve çerez kontrolü
- Dinamik bekleme süreleri ve yeniden deneme mekanizması
- Yapılandırılabilir loglama sistemi
- Otomatik hata kurtarma ve ilerleme kaydı
- Sezon bazlı veri toplama ve otomatik sezon geçişi
- Raspberry Pi desteği ve optimizasyonları
- Systemd servis entegrasyonu
- Otomatik planlama ve zamanlama sistemi

### Sistem Gereksinimleri

#### Yazılım Gereksinimleri
- Python 3.8 veya üzeri
- Firefox ESR (Raspberry Pi için)
- Geckodriver
- Xvfb (X Virtual Frame Buffer)

#### Python Kütüphaneleri
```bash
selenium==4.15.2          # Web otomasyon için
webdriver-manager==4.0.1  # WebDriver yönetimi
beautifulsoup4==4.12.2    # HTML parse işlemleri
pandas==2.0.3            # Veri manipülasyonu
requests==2.31.0         # HTTP istekleri
fake-useragent==1.4.0    # User-Agent rotasyonu
python-dotenv==1.0.0     # Ortam değişkenleri
pyvirtualdisplay==3.0    # Sanal ekran yönetimi
psutil==5.9.5           # Sistem kaynak yönetimi
```

### Proje Yapısı

```
Football/
│
├── scraper.py           # Ana program dosyası
├── config.py           # Konfigürasyon ayarları
├── logger.py           # Loglama işlemleri
├── csv_handler.py      # CSV dosya işlemleri
├── requirements.txt    # Bağımlılıklar
├── setup_raspberry.sh  # Raspberry Pi kurulum scripti
├── control_scraper.sh  # Servis kontrol scripti
│
├── logs/               # Log dosyaları
│   └── scraper.log    # Güncel log dosyası
│
├── stats/              # İstatistik dosyaları
│   ├── Arsenal.csv
│   ├── Chelsea.csv
│   └── ...
│
├── geckodriver         # Firefox WebDriver
└── ublock.xpi         # uBlock Origin eklentisi
```

### Kurulum

1. Python Sanal Ortam Oluşturma:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Bağımlılıkların Yüklenmesi:
```bash
pip install -r requirements.txt
```

3. Raspberry Pi için Otomatik Kurulum:
```bash
sudo bash setup_raspberry.sh
```

4. Servis Kontrolü:
```bash
sudo bash control_scraper.sh
```

### CSV Dosya Yapısı ve Örnek Veri

Arsenal.csv dosyasından örnek veri:

```csv
Tarih,Rakip,Ev Sahibi/Deplasman,MS Gol,İY Gol,MS Yenilen Gol,İY Yenilen Gol,Sonuç,Topla Oynama,İkili Mücadele Kazanma,Hava Topu Kazanma,Pas Arası,Ofsayt,Korner,Toplam Pas,İsabetli Pas,Pas İsabeti %,Toplam Orta,İsabetli Orta,Toplam Şut,İsabetli Şut,İsabetsiz Şut,Engellenen Şut,Direkten Dönen Şut,Gol Beklentisi (xG),Rakip Ceza Sahasında Topla Buluşma,Uzaklaştırma,Faul,Sarı Kart,İkinci Sarıdan Kırmızı Kart,Kırmızı Kart
29.08.2023,Chelsea,Ev Sahibi,2,1,0,0,Galip,55,48,12,15,2,6,423,378,89,22,8,15,7,5,3,0,2.1,18,15,12,2,0,0
```

### Performans Optimizasyonları

1. **Bellek Yönetimi:**
   - Her 10 maçta bir tarayıcı yeniden başlatılır
   - Çerezler düzenli olarak temizlenir
   - Gereksiz DOM elementleri temizlenir
   - Raspberry Pi için özel bellek optimizasyonları

2. **Ağ Optimizasyonları:**
   - uBlock Origin ile reklam engelleme
   - Headless mod ile kaynak tasarrufu
   - Dinamik bekleme süreleri
   - Akıllı yeniden deneme mekanizması

3. **Hata Toleransı:**
   - 5 kez yeniden deneme mekanizması
   - Otomatik kurtarma sistemi
   - İlerleme kaydı
   - Sezon bazlı otomatik planlama

### Servis Yönetimi

```bash
# Servisleri başlatma
sudo systemctl start xvfb
sudo systemctl start football-scraper

# Servisleri durdurma
sudo systemctl stop football-scraper
sudo systemctl stop xvfb

# Servis durumunu kontrol etme
sudo systemctl status football-scraper

# Logları görüntüleme
sudo journalctl -u football-scraper -f
```

### Log Sistemi

```python
logger.info("İşlem başlatılıyor...")
logger.debug("Teknik detay...")
logger.warning("Dikkat edilmesi gereken durum...")
logger.error("Hata durumu...")
```

Log dosyası örneği:
```log
2024-01-05 18:49:08,538 - SahadanScraper - INFO - Scraper başlatılıyor...
2024-01-05 18:49:09,415 - SahadanScraper - INFO - Firefox başlatılıyor...
2024-01-05 18:49:10,631 - SahadanScraper - INFO - uBlock Origin yüklendi
```

---

## 🇬🇧 English <a name="english"></a>

This application automatically collects match statistics from sahadan.com for the Premier League using Selenium WebDriver and saves them to structured CSV files.

### Technical Features

- Selenium WebDriver automation
- Headless Firefox browser support
- uBlock Origin ad blocker integration
- Multi-session management and cookie control
- Dynamic wait times and retry mechanism
- Configurable logging system
- Automatic error recovery and progress tracking
- Season-based data collection and automatic season transition
- Raspberry Pi support and optimizations
- Systemd service integration
- Automatic scheduling system

### System Requirements

#### Software Requirements
- Python 3.8 or higher
- Firefox ESR (for Raspberry Pi)
- Geckodriver
- Xvfb (X Virtual Frame Buffer)

#### Python Libraries
```bash
selenium==4.15.2          # For web automation
webdriver-manager==4.0.1  # WebDriver management
beautifulsoup4==4.12.2    # HTML parsing
pandas==2.0.3            # Data manipulation
requests==2.31.0         # HTTP requests
fake-useragent==1.4.0    # User-Agent rotation
python-dotenv==1.0.0     # Environment variables
pyvirtualdisplay==3.0    # Virtual display management
psutil==5.9.5           # System resource management
```

### Project Structure

```
Football/
│
├── scraper.py           # Main program file
├── config.py           # Configuration settings
├── logger.py           # Logging operations
├── csv_handler.py      # CSV file operations
├── requirements.txt    # Dependencies
├── setup_raspberry.sh  # Raspberry Pi setup script
├── control_scraper.sh  # Service control script
│
├── logs/               # Log files
│   └── scraper.log    # Current log file
│
├── stats/              # Statistics files
│   ├── Arsenal.csv
│   ├── Chelsea.csv
│   └── ...
│
├── geckodriver         # Firefox WebDriver
└── ublock.xpi         # uBlock Origin extension
```

### Installation

1. Creating Python Virtual Environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Installing Dependencies:
```bash
pip install -r requirements.txt
```

3. Automatic Setup for Raspberry Pi:
```bash
sudo bash setup_raspberry.sh
```

4. Service Control:
```bash
sudo bash control_scraper.sh
```

### CSV File Structure and Sample Data

Sample data from Arsenal.csv:

```csv
Date,Opponent,Home/Away,FT Goals,HT Goals,FT Conceded,HT Conceded,Result,Possession,Duels Won,Aerial Duels,Interceptions,Offsides,Corners,Total Passes,Accurate Passes,Pass Accuracy %,Total Crosses,Accurate Crosses,Total Shots,Shots on Target,Shots off Target,Blocked Shots,Woodwork,Expected Goals (xG),Touches in Box,Clearances,Fouls,Yellow Cards,Second Yellow,Red Cards
29.08.2023,Chelsea,Home,2,1,0,0,Win,55,48,12,15,2,6,423,378,89,22,8,15,7,5,3,0,2.1,18,15,12,2,0,0
```

### Performance Optimizations

1. **Memory Management:**
   - Browser restart every 10 matches
   - Regular cookie cleanup
   - Unnecessary DOM elements cleanup
   - Special memory optimizations for Raspberry Pi

2. **Network Optimizations:**
   - Ad blocking with uBlock Origin
   - Resource saving with headless mode
   - Dynamic wait times
   - Smart retry mechanism

3. **Error Tolerance:**
   - 5-time retry mechanism
   - Automatic recovery system
   - Progress tracking
   - Season-based automatic scheduling

### Service Management

```bash
# Starting services
sudo systemctl start xvfb
sudo systemctl start football-scraper

# Stopping services
sudo systemctl stop football-scraper
sudo systemctl stop xvfb

# Checking service status
sudo systemctl status football-scraper

# Viewing logs
sudo journalctl -u football-scraper -f
```

### Logging System

```python
logger.info("Starting process...")
logger.debug("Technical detail...")
logger.warning("Situation requiring attention...")
logger.error("Error condition...")
```

Log file example:
```log
2024-01-05 18:49:08,538 - SahadanScraper - INFO - Starting scraper...
2024-01-05 18:49:09,415 - SahadanScraper - INFO - Starting Firefox...
2024-01-05 18:49:10,631 - SahadanScraper - INFO - uBlock Origin loaded
```
""" 