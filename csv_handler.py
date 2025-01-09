"""
csv_handler.py - CSV işlemleri için yardımcı modül
"""

import os
import csv
from datetime import datetime

# Tüm olası istatistik başlıkları
ALL_STATS_HEADERS = [
    'Tarih',
    'Rakip',
    'Ev Sahibi/Deplasman',
    'MS Gol',
    'İY Gol',
    'MS Yenilen Gol',
    'İY Yenilen Gol',
    'Sonuç',
    'Topla Oynama',
    'İkili Mücadele Kazanma',
    'Hava Topu Kazanma',
    'Pas Arası',
    'Ofsayt',
    'Korner',
    'Toplam Pas',
    'İsabetli Pas',
    'Pas İsabeti %',
    'Toplam Orta',
    'İsabetli Orta',
    'Toplam Şut',
    'İsabetli Şut',
    'İsabetsiz Şut',
    'Engellenen Şut',
    'Direkten Dönen Şut',
    'Gol Beklentisi (xG)',
    'Rakip Ceza Sahasında Topla Buluşma',
    'Pas Arası',
    'Uzaklaştırma',
    'Faul',
    'Sarı Kart',
    'İkinci Sarıdan Kırmızı Kart',
    'Kırmızı Kart'
]

def create_stats_folder():
    """İstatistikler için klasör oluşturur"""
    stats_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stats')
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)
    return stats_dir

def save_match_stats(team_name, opponent, is_home, stats_data, match_date, logger):
    """Maç istatistiklerini CSV dosyasına kaydeder"""
    try:
        stats_dir = create_stats_folder()
        csv_file = os.path.join(stats_dir, f"{team_name}.csv")
        
        # Verileri başlıklarla eşleştir
        row_data = {}
        
        # Tüm başlıklar için varsayılan değer olarak '0' ata
        for header in ALL_STATS_HEADERS:
            row_data[header] = '0'
        
        # Temel verileri ekle
        row_data['Tarih'] = match_date
        row_data['Rakip'] = opponent
        row_data['Ev Sahibi/Deplasman'] = 'Ev Sahibi' if is_home else 'Deplasman'
        
        # İstatistik verilerini eşleştir
        for key, value in stats_data.items():
            if key in ALL_STATS_HEADERS:
                row_data[key] = value
            else:
                logger.warning(f"Bilinmeyen istatistik başlığı: {key}")
        
        # Dosya yoksa başlıkları yaz
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=ALL_STATS_HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_data)
        
        logger.info(f"{team_name} için istatistikler CSV'ye kaydedildi")
        return True
        
    except Exception as e:
        logger.error(f"{team_name} için CSV kaydetme hatası: {str(e)}")
        return False

def get_existing_matches(team_name):
    """Belirtilen takımın mevcut maçlarını CSV'den okur"""
    try:
        stats_dir = create_stats_folder()
        csv_file = os.path.join(stats_dir, f"{team_name}.csv")
        
        if not os.path.exists(csv_file):
            return []
            
        matches = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                matches.append(row)
                
        return matches
        
    except Exception:
        return [] 