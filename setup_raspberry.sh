#!/bin/bash

# Renk tanımlamaları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log fonksiyonu
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] HATA: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] UYARI: $1${NC}"
}

# Root kontrolü
if [ "$EUID" -ne 0 ]; then
    error "Bu script root yetkisi gerektirir. 'sudo bash setup_raspberry.sh' şeklinde çalıştırın."
    exit 1
fi

# Çalışma dizinini belirle
WORK_DIR="/home/pi/Football"
CURRENT_USER="server"

# Sistem güncellemesi
log "Sistem güncelleniyor..."
apt-get update && apt-get upgrade -y

# Gerekli paketlerin kurulumu
log "Gerekli paketler kuruluyor..."
apt-get install -y python3-pip \
    firefox-esr \
    geckodriver \
    xvfb \
    python3-dev \
    libatlas-base-dev \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libdbus-glib-1-2 \
    xorg \
    dbus-x11 \
    libxtst6 \
    libxt6 \
    libxinerama1 \
    git

# Swap alanı oluşturma
log "Swap alanı kontrol ediliyor ve oluşturuluyor..."
if [ ! -f /swapfile ]; then
    log "2GB swap alanı oluşturuluyor..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    log "Swap alanı başarıyla oluşturuldu"
else
    warning "Swap dosyası zaten mevcut"
fi

# DISPLAY değişkenini ayarla
log "DISPLAY değişkeni ayarlanıyor..."
if ! grep -q "DISPLAY=:99" /etc/environment; then
    echo "DISPLAY=:99" >> /etc/environment
    log "DISPLAY değişkeni eklendi"
else
    warning "DISPLAY değişkeni zaten mevcut"
fi

# Xvfb service dosyası oluştur
log "Xvfb service dosyası oluşturuluyor..."
cat > /etc/systemd/system/xvfb.service << EOL
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac

[Install]
WantedBy=multi-user.target
EOL

# Football scraper service dosyası oluştur
log "Football scraper service dosyası oluşturuluyor..."
cat > /etc/systemd/system/football-scraper.service << EOL
[Unit]
Description=Football Data Scraper
After=network.target xvfb.service

[Service]
Type=simple
User=${CURRENT_USER}
Environment=DISPLAY=:99
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=${WORK_DIR}
ExecStart=/usr/bin/python3 ${WORK_DIR}/scraper.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# Çalışma dizinini oluştur ve izinleri ayarla
log "Çalışma dizini oluşturuluyor..."
mkdir -p ${WORK_DIR}
chown -R ${CURRENT_USER}:${CURRENT_USER} ${WORK_DIR}

# Python paketlerini kur
log "Python paketleri kuruluyor..."
sudo -u ${CURRENT_USER} python3 -m pip install --upgrade pip
if [ -f ${WORK_DIR}/requirements.txt ]; then
    sudo -u ${CURRENT_USER} python3 -m pip install -r ${WORK_DIR}/requirements.txt
else
    error "requirements.txt dosyası bulunamadı!"
    exit 1
fi

# Servisleri etkinleştir ve başlat
log "Servisler etkinleştiriliyor..."
systemctl daemon-reload
systemctl enable xvfb
systemctl start xvfb
systemctl enable football-scraper
systemctl start football-scraper

# Kurulum durumunu kontrol et
log "Kurulum durumu kontrol ediliyor..."

if systemctl is-active --quiet xvfb; then
    log "Xvfb servisi aktif"
else
    error "Xvfb servisi başlatılamadı"
fi

if systemctl is-active --quiet football-scraper; then
    log "Football scraper servisi aktif"
else
    error "Football scraper servisi başlatılamadı"
fi

# Logları görüntüleme komutlarını göster
echo -e "\n${GREEN}Kurulum tamamlandı!${NC}"
echo -e "\n${YELLOW}Faydalı komutlar:${NC}"
echo "Scraper loglarını görüntülemek için: sudo journalctl -u football-scraper -f"
echo "Xvfb loglarını görüntülemek için: sudo journalctl -u xvfb -f"
echo "Servisi yeniden başlatmak için: sudo systemctl restart football-scraper"
echo "Servis durumunu kontrol etmek için: sudo systemctl status football-scraper" 