"""
config.py - Konfigürasyon dosyası
"""

# Sezon bilgileri
SEASON_START = "2023"
SEASON_END = "2024"

# Base URL
#BASE_URL = "https://www.sahadan.com/puan-durumu/türkiye-süper-lig/{}-{}/fikstur/482ofyysbdbeoxauk19yg7tdt"
BASE_URL = "https://www.sahadan.com/puan-durumu/ingiltere-premier-lig/{}-{}/fikstur/2kwbbcootiqqgmrzs6o5inle5"
#            'https://www.sahadan.com/puan-durumu/ingiltere-premier-lig/fikstur/2kwbbcootiqqgmrzs6o5inle5'

# URL'yi oluşturan fonksiyon
def get_url():
    return BASE_URL.format(SEASON_START, SEASON_END)  