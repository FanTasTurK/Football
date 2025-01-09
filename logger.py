"""
logger.py - Loglama işlemleri için yardımcı modül
"""

import logging
import os
import glob
from datetime import datetime

def setup_logger():
    """Loglama sistemini yapılandırır"""
    # Log dosyası için klasör oluştur
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Eski log dosyalarını temizle
    for old_log in glob.glob(os.path.join(log_dir, '*.log')):
        try:
            os.remove(old_log)
        except Exception as e:
            print(f"Eski log dosyası silinirken hata oluştu: {str(e)}")
    
    # Sabit log dosya adı
    log_filename = os.path.join(log_dir, 'scraper.log')
    
    # Logger'ı yapılandır
    logger = logging.getLogger('SahadanScraper')
    logger.setLevel(logging.DEBUG)
    
    # Önceki handler'ları temizle
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Dosyaya yazma için handler
    file_handler = logging.FileHandler(log_filename, encoding='utf-8', mode='w')
    file_handler.setLevel(logging.DEBUG)
    
    # Konsola yazma için handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Format belirle
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Handler'ları logger'a ekle
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Yeni oturum başlangıcını logla
    logger.info("="*50)
    logger.info(f"Yeni oturum başlatıldı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*50)
    
    return logger

def get_logger():
    """Mevcut logger'ı döndürür, yoksa yeni bir tane oluşturur"""
    logger = logging.getLogger('SahadanScraper')
    if not logger.handlers:
        logger = setup_logger()
    return logger 