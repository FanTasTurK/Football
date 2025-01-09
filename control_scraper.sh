#!/bin/bash

# Renk tanımlamaları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log fonksiyonları
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
    error "Bu script root yetkisi gerektirir. 'sudo bash control_scraper.sh' şeklinde çalıştırın."
    exit 1
fi

# Fonksiyonlar
start_services() {
    log "Xvfb servisi başlatılıyor..."
    systemctl start xvfb
    sleep 2
    log "Football scraper servisi başlatılıyor..."
    systemctl start football-scraper
    sleep 2
    
    if systemctl is-active --quiet xvfb && systemctl is-active --quiet football-scraper; then
        log "Tüm servisler başarıyla başlatıldı"
    else
        error "Servisler başlatılırken hata oluştu"
        show_status
    fi
}

stop_services() {
    log "Football scraper servisi durduruluyor..."
    systemctl stop football-scraper
    sleep 2
    log "Xvfb servisi durduruluyor..."
    systemctl stop xvfb
    sleep 2
    
    if ! systemctl is-active --quiet xvfb && ! systemctl is-active --quiet football-scraper; then
        log "Tüm servisler başarıyla durduruldu"
    else
        error "Servisler durdurulurken hata oluştu"
        show_status
    fi
}

restart_services() {
    log "Servisler yeniden başlatılıyor..."
    stop_services
    sleep 2
    start_services
}

show_status() {
    echo -e "\n${YELLOW}Servis Durumları:${NC}"
    echo -e "\n${GREEN}Xvfb Servisi:${NC}"
    systemctl status xvfb --no-pager
    echo -e "\n${GREEN}Football Scraper Servisi:${NC}"
    systemctl status football-scraper --no-pager
}

show_logs() {
    echo -e "\n${YELLOW}Son 50 log satırı gösteriliyor...${NC}"
    journalctl -u football-scraper -n 50 --no-pager
}

disable_autostart() {
    log "Otomatik başlatma devre dışı bırakılıyor..."
    systemctl disable xvfb
    systemctl disable football-scraper
    log "Otomatik başlatma devre dışı bırakıldı"
}

# Menü
show_menu() {
    echo -e "\n${YELLOW}Football Scraper Kontrol Paneli${NC}"
    echo "1) Servisleri Başlat"
    echo "2) Servisleri Durdur"
    echo "3) Servisleri Yeniden Başlat"
    echo "4) Durum Kontrolü"
    echo "5) Logları Göster"
    echo "6) Otomatik Başlatmayı Devre Dışı Bırak"
    echo "7) Çıkış"
    echo -n "Seçiminiz (1-7): "
}

# Ana döngü
while true; do
    show_menu
    read -r choice
    
    case $choice in
        1)
            start_services
            ;;
        2)
            stop_services
            ;;
        3)
            restart_services
            ;;
        4)
            show_status
            ;;
        5)
            show_logs
            ;;
        6)
            disable_autostart
            ;;
        7)
            log "Program sonlandırılıyor..."
            exit 0
            ;;
        *)
            error "Geçersiz seçim!"
            ;;
    esac
    
    echo -e "\nDevam etmek için ENTER tuşuna basın..."
    read -r
done 