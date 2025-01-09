"""
scraper.py - Sahadan.com web scraper (Raspberry Pi Headless Mode)
"""

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import random
from fake_useragent import UserAgent
from config import get_url
from logger import get_logger
from csv_handler import save_match_stats
import sys
import datetime
import subprocess
from datetime import datetime, timedelta
import platform

def get_random_delay():
    """İstekler arası rastgele bekleme süresi üretir"""
    # 1-3 saniye arası rastgele bekleme
    return random.uniform(1, 3)

def clear_cookies(driver, logger):
    """Tarayıcı çerezlerini temizler"""
    try:
        driver.delete_all_cookies()
        logger.info("Çerezler temizlendi")
    except Exception as e:
        logger.warning(f"Çerezler temizlenirken hata: {str(e)}")

def setup_driver():
    """Firefox tarayıcısını headless modda başlatır"""
    logger = get_logger()
    logger.info("Firefox tarayıcısı başlatılıyor...")
    
    firefox_options = Options()
    
    # Raspberry Pi için özel ayarlar
    if platform.machine() == 'aarch64' or platform.machine().startswith('arm'):
        firefox_options.binary_location = '/usr/bin/firefox-esr'  # Raspberry Pi'da Firefox ESR kullanılır
    else:
        firefox_options.binary_location = '/usr/bin/firefox'  # Diğer Linux sistemleri için
    
    # Headless mod ayarları
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--no-sandbox")
    firefox_options.add_argument("--disable-dev-shm-usage")
    firefox_options.add_argument("--disable-gpu")
    firefox_options.add_argument("--window-size=1920,1080")
    
    # Rastgele User-Agent ekle
    ua = UserAgent()
    firefox_options.add_argument(f'user-agent={ua.random}')
    
    # WebDriver ve otomasyon özelliklerini gizle
    firefox_options.set_preference("dom.webdriver.enabled", False)
    firefox_options.set_preference('useAutomationExtension', False)
    firefox_options.set_preference("general.useragent.override", ua.random)
    
    # Diğer gizlilik ayarları
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
    firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")
    firefox_options.set_preference("browser.privatebrowsing.autostart", True)
    firefox_options.set_preference("network.cookie.cookieBehavior", 2)
    
    # Raspberry Pi için bellek optimizasyonu
    firefox_options.add_argument("--disable-extensions")
    firefox_options.add_argument("--disable-application-cache")
    firefox_options.add_argument("--disable-notifications")
    firefox_options.add_argument("--disable-infobars")
    
    # uBlock Origin eklentisini yükle
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ublock_path = os.path.join(current_dir, "ublock.xpi")
    logger.debug(f"uBlock Origin yolu: {ublock_path}")
    
    # Geckodriver servisini başlat
    service = Service(
        executable_path=os.path.join(current_dir, "geckodriver"),
        log_path=os.path.join(current_dir, "geckodriver.log")
    )
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Firefox sürücüsü başlatılıyor... (Deneme {retry_count + 1}/{max_retries})")
            driver = webdriver.Firefox(
                service=service,
                options=firefox_options
            )
            
            # uBlock Origin'i yükle
            logger.info("uBlock Origin eklentisi yükleniyor...")
            driver.install_addon(ublock_path, temporary=True)
            time.sleep(1)
            logger.info("uBlock Origin başarıyla yüklendi")
            
            return driver
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Firefox sürücüsü başlatılırken hata: {str(e)}")
            if retry_count < max_retries:
                wait_time = random.uniform(5, 10)
                logger.info(f"Yeniden deneme öncesi {wait_time:.1f} saniye bekleniyor...")
                time.sleep(wait_time)
            else:
                logger.error("Maksimum deneme sayısına ulaşıldı")
                raise

def collect_stats_from_tab(driver, tab_selector, logger):
    """Belirtilen tabdaki istatistikleri toplar"""
    try:
        # İstatistik sayfasının yüklenmesini bekle
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#widget-match-live-stats-1"))
        )
        
        # Tab'ı bulmayı dene
        try:
            tab = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, tab_selector))
            )
            driver.execute_script("arguments[0].click();", tab)
            
            # Tablo içeriğini bul
            table = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#widget-match-live-stats-1 > div > div > div > ul > li.Opta-On > div > table"))
            )
            
            # İstatistikleri ve değerleri topla
            stats = table.find_elements(By.CLASS_NAME, "Opta-Stats-Bars-Text")
            values = table.find_elements(By.CLASS_NAME, "Opta-Outer")
            
            tab_stats = {}
            value_index = 0
            
            for stat in stats:
                stat_name = stat.text.strip()
                if stat_name and value_index + 1 < len(values):
                    home_value = values[value_index].text.strip()
                    away_value = values[value_index + 1].text.strip()
                    tab_stats[stat_name] = (home_value, away_value)
                    value_index += 2
                    
            return tab_stats
        except Exception as tab_error:
            logger.warning(f"Tab bulunamadı veya tıklanamadı: {str(tab_error)}")
            return {}
            
    except Exception as e:
        logger.error(f"Tab istatistikleri toplanırken hata: {str(e)}")
        return {}

def get_match_scores(driver, logger):
    """Maç skorlarını toplar"""
    try:
        # MS Gol bilgilerini al
        home_ms_goal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, 
            '/html/body/div[4]/div[1]/div[1]/div/div[2]/div[2]/div[1]/span[1]'))
        ).text.strip()
        
        away_ms_goal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, 
            '/html/body/div[4]/div[1]/div[1]/div/div[2]/div[2]/div[1]/span[2]'))
        ).text.strip()
        
        # İY Gol bilgisini al ve işle
        iy_score = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, 
            '/html/body/div[4]/div[1]/div[1]/div/div[2]/div[2]/div[2]'))
        ).text.strip()
        
        # İY skorundan sayısal olmayan karakterleri temizle
        iy_score = ''.join(filter(str.isdigit, iy_score))
        
        # İlk yarı skorlarını ayır (ilk karakter ev sahibi, ikinci karakter deplasman)
        home_iy_goal = iy_score[0] if len(iy_score) > 0 else '0'
        away_iy_goal = iy_score[1] if len(iy_score) > 1 else '0'
        
        logger.info(f"Maç Skoru - MS: {home_ms_goal}-{away_ms_goal}, İY: {home_iy_goal}-{away_iy_goal}")
        
        return {
            'MS Gol': home_ms_goal,
            'İY Gol': home_iy_goal,
            'MS Yenilen Gol': away_ms_goal,  # Ev sahibi için MS yenilen gol
            'İY Yenilen Gol': away_iy_goal   # Ev sahibi için İY yenilen gol
        }, {
            'MS Gol': away_ms_goal,
            'İY Gol': away_iy_goal,
            'MS Yenilen Gol': home_ms_goal,  # Deplasman için MS yenilen gol
            'İY Yenilen Gol': home_iy_goal   # Deplasman için İY yenilen gol
        }
        
    except Exception as e:
        logger.error(f"Maç skorları alınırken hata: {str(e)}")
        return {
            'MS Gol': '0', 
            'İY Gol': '0', 
            'MS Yenilen Gol': '0',
            'İY Yenilen Gol': '0'
        }, {
            'MS Gol': '0', 
            'İY Gol': '0', 
            'MS Yenilen Gol': '0',
            'İY Yenilen Gol': '0'
        }

def get_match_result(home_ms_goal, away_ms_goal):
    """Maç sonucunu belirler"""
    home_ms_goal = int(home_ms_goal)
    away_ms_goal = int(away_ms_goal)
    
    if home_ms_goal > away_ms_goal:
        return "Galip", "Mağlup"
    elif home_ms_goal < away_ms_goal:
        return "Mağlup", "Galip"
    else:
        return "Berabere", "Berabere"

def process_matches(driver, elements, start_index, logger):
    """Belirli bir indeksten başlayarak maçları işler"""
    max_retries = 5
    
    for i in range(start_index, min(start_index + 10, len(elements))):
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Her maç öncesi rastgele bekle
                delay = get_random_delay()
                logger.info(f"{delay:.1f} saniye bekleniyor...")
                time.sleep(delay)
                
                # Çerezleri temizle
                clear_cookies(driver, logger)
                
                # Ana pencere ID'sini kaydet
                main_window = driver.current_window_handle
                
                # Maç elementine tıkla
                logger.info(f"{i+1}. maça tıklanıyor... (Deneme {retry_count + 1}/{max_retries})")
                element = elements[i]
                driver.execute_script("arguments[0].click();", element)
                
                # Yeni sekmenin açılmasını bekle
                WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
                
                # Yeni açılan sekmeye geç
                new_window = [window for window in driver.window_handles if window != main_window][0]
                driver.switch_to.window(new_window)
                
                # Takım isimlerini al
                home_team = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "body > div.page-container.page-container--legacy-link-banner-visible > div.above-content.clearfix > div.p0c-soccer-match-details-header > div > div.p0c-soccer-match-details-header__row > a.p0c-soccer-match-details-header__team-name.p0c-soccer-match-details-header__team-name--home"))
                ).text.strip()
                
                away_team = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "body > div.page-container.page-container--legacy-link-banner-visible > div.above-content.clearfix > div.p0c-soccer-match-details-header > div > div.p0c-soccer-match-details-header__row > a.p0c-soccer-match-details-header__team-name.p0c-soccer-match-details-header__team-name--away"))
                ).text.strip()
                
                # Maç tarihini al
                match_date = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "body > div.page-container.page-container--legacy-link-banner-visible > div.above-content.clearfix > div.p0c-soccer-match-details-header > div > div.p0c-soccer-match-details-header__info-container > p:nth-child(2) > span"))
                ).text.strip()
                
                # Maç skorlarını al
                home_scores, away_scores = get_match_scores(driver, logger)
                
                # Maç sonucunu belirle
                home_result, away_result = get_match_result(home_scores['MS Gol'], away_scores['MS Gol'])
                
                # Sonuçları istatistiklere ekle
                home_scores['Sonuç'] = home_result
                away_scores['Sonuç'] = away_result
                
                logger.info(f"Maç: {home_team} vs {away_team} - Tarih: {match_date}")
                
                # İstatistik butonunu bekle ve tıkla
                logger.info("İstatistik butonuna tıklanıyor...")
                stats_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    "body > div.page-container.page-container--legacy-link-banner-visible > div.above-content.clearfix > div.widget-match-detail-submenu > div > a.widget-match-detail-submenu__icon.widget-match-detail-submenu__icon--stats"))
                )
                driver.execute_script("arguments[0].click();", stats_button)
                
                # İstatistik sayfasının yüklenmesini bekle
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#widget-match-live-stats-1"))
                )
                
                # Tüm istatistikleri topla
                home_stats = home_scores.copy()  # Skorları ekle
                away_stats = away_scores.copy()  # Skorları ekle
                
                # Tab selectors
                tab_selectors = [
                    '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[1]/a',
                    '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[2]/a',
                    '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[3]/a',
                    '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[4]/a',
                    '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[5]/a'
                ]
                
                # Her tab için istatistikleri topla
                for tab_selector in tab_selectors:
                    tab_stats = collect_stats_from_tab(driver, tab_selector, logger)
                    # İstatistikleri ana sözlüklere ekle
                    for stat_name, (home_value, away_value) in tab_stats.items():
                        home_stats[stat_name] = home_value
                        away_stats[stat_name] = away_value
                
                # İstatistikleri CSV'ye kaydet
                save_match_stats(home_team, away_team, True, home_stats, match_date, logger)
                save_match_stats(away_team, home_team, False, away_stats, match_date, logger)
                
                # Sekmeyi kapat ve ana pencereye geri dön
                logger.info("Sekme kapatılıyor...")
                driver.close()
                driver.switch_to.window(main_window)
                
                break  # Başarılı işlem sonrası döngüden çık
                
            except Exception as e:
                retry_count += 1
                logger.error(f"{i+1}. maç işlenirken hata: {str(e)}")
                
                try:
                    driver.quit()
                except:
                    pass
                
                logger.info("Tarayıcı yeniden başlatılıyor...")
                driver = setup_driver()
                
                url = get_url()
                logger.info(f"Ziyaret edilecek URL: {url}")
                driver.get(url)
                logger.info("Sayfa açıldı")
                
                time.sleep(random.uniform(5, 10))
                
                elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "p0c-competition-match-list__status"))
                )
                
                if retry_count >= max_retries:
                    logger.error(f"{i+1}. maç için maksimum deneme sayısına ulaşıldı, sonraki maça geçiliyor")
                    break

def save_progress(current_index, match_date, logger):
    """İlerleme ve son maç tarihini kaydeder"""
    try:
        # İlerleme bilgisini kaydet
        progress_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'progress.txt')
        with open(progress_file, 'w', encoding='utf-8') as f:
            f.write(f"{current_index}\n{match_date}")
        logger.info(f"İlerleme kaydedildi: {current_index}. maç, Tarih: {match_date}")
        return True
    except Exception as e:
        logger.error(f"İlerleme kaydedilirken hata: {str(e)}")
        return False

def load_progress(logger):
    """Kaydedilen ilerlemeyi ve son maç tarihini yükler"""
    try:
        progress_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'progress.txt')
        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    current_index = int(lines[0].strip())
                    last_match_date = lines[1].strip()
                    logger.info(f"İlerleme yüklendi: {current_index}. maç, Son Tarih: {last_match_date}")
                    return current_index, last_match_date
                else:
                    return 0, None
        return 0, None
    except Exception as e:
        logger.error(f"İlerleme yüklenirken hata: {str(e)}")
        return 0, None

def schedule_next_run(target_date, logger):
    """Programın bir sonraki çalışmasını planlar"""
    try:
        # Hedef tarihi ayarla (23:30)
        target_datetime = datetime.strptime(target_date, "%d.%m.%Y").replace(hour=23, minute=30)
        
        # Cron job oluştur
        current_file = os.path.abspath(__file__)
        python_path = sys.executable
        cron_command = f'30 23 {target_datetime.day} {target_datetime.month} * {python_path} {current_file}'
        
        # Mevcut cron jobları al
        try:
            existing_crons = subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL).decode()
        except subprocess.CalledProcessError:
            # Kullanıcının crontab'ı yoksa boş bir liste başlat
            existing_crons = ""
        
        # Yeni cron job ekle
        with open('/tmp/crontab.txt', 'w') as f:
            if existing_crons.strip():
                f.write(existing_crons)
                if not existing_crons.endswith('\n'):
                    f.write('\n')
            f.write(f'{cron_command}\n')
        
        # Crontab'ı güncelle
        try:
            subprocess.run(['crontab', '/tmp/crontab.txt'], check=True)
            os.remove('/tmp/crontab.txt')
            
            # Planlanan zamanı kaydet
            schedule_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'next_run.txt')
            with open(schedule_file, 'w', encoding='utf-8') as f:
                f.write(f"{target_date} 23:30")
            
            logger.info(f"Program {target_date} 23:30'da çalışacak şekilde planlandı")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Crontab güncellenirken hata: {str(e)}")
            # Alternatif olarak at komutu kullan
            try:
                target_time = target_datetime.strftime("%Y%m%d2330")
                at_command = f'echo "{python_path} {current_file}" | at {target_time}'
                subprocess.run(at_command, shell=True, check=True)
                
                # Planlanan zamanı kaydet
                schedule_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'next_run.txt')
                with open(schedule_file, 'w', encoding='utf-8') as f:
                    f.write(f"{target_date} 23:30")
                
                logger.info(f"Program {target_date} 23:30'da çalışacak şekilde planlandı (at komutu ile)")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"At komutu ile planlama yapılırken hata: {str(e)}")
                return False
            
    except Exception as e:
        logger.error(f"Program planlanırken hata: {str(e)}")
        return False

def check_match_date(match_date, driver, logger):
    """Maç tarihini kontrol eder ve gerekirse programı planlar"""
    try:
        # Tarihleri parse et
        match_datetime = datetime.strptime(match_date, "%d.%m.%Y")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Tarihleri karşılaştır
        if match_datetime > today:
            logger.info(f"Gelecek tarihli maç bulundu: {match_date}")
            
            # Daha önce planlanmış bir çalışma var mı kontrol et
            schedule_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'next_run.txt')
            if os.path.exists(schedule_file):
                with open(schedule_file, 'r', encoding='utf-8') as f:
                    scheduled_date = f.read().strip()
                    logger.info(f"Zaten planlanmış çalışma mevcut: {scheduled_date}")
                    return False
            
            # Yeni çalışma planla
            if schedule_next_run(match_date, logger):
                logger.info("Program duraklatılıyor...")
                # Tarayıcıyı düzgün şekilde kapat
                try:
                    driver.quit()
                except:
                    pass
                sys.exit(0)
            
        return False
    except Exception as e:
        logger.error(f"Tarih kontrolü yapılırken hata: {str(e)}")
        return False

def click_match_elements(driver, logger):
    """Maç elementlerine tıklayıp istatistik sayfasına gider"""
    try:
        # Maç elementlerini bul
        logger.info("Maç elementleri aranıyor...")
        elements = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "p0c-competition-match-list__status"))
        )
        logger.info(f"Toplam {len(elements)} adet maç bulundu")
        
        # Kaydedilen ilerlemeyi yükle
        start_index, last_saved_date = load_progress(logger)
        logger.info(f"İşlem {start_index}. maçtan devam ediyor...")
        
        # Her 10 maçta bir tarayıcıyı yenile ve uzun bekle
        while start_index < len(elements):
            for i in range(start_index, min(start_index + 10, len(elements))):
                retry_count = 0
                max_retries = 5
                
                while retry_count < max_retries:
                    try:
                        # Her maç öncesi rastgele bekle
                        delay = get_random_delay()
                        logger.info(f"{delay:.1f} saniye bekleniyor...")
                        time.sleep(delay)
                        
                        # Çerezleri temizle
                        clear_cookies(driver, logger)
                        
                        # Ana pencere ID'sini kaydet
                        main_window = driver.current_window_handle
                        
                        # Maç elementine tıkla
                        logger.info(f"{i+1}. maça tıklanıyor... (Deneme {retry_count + 1}/{max_retries})")
                        element = elements[i]
                        driver.execute_script("arguments[0].click();", element)
                        
                        # Yeni sekmenin açılmasını bekle
                        WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
                        
                        # Yeni açılan sekmeye geç
                        new_window = [window for window in driver.window_handles if window != main_window][0]
                        driver.switch_to.window(new_window)
                        
                        # Takım isimlerini al
                        home_team = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 
                            "body > div.page-container.page-container--legacy-link-banner-visible > div.above-content.clearfix > div.p0c-soccer-match-details-header > div > div.p0c-soccer-match-details-header__row > a.p0c-soccer-match-details-header__team-name.p0c-soccer-match-details-header__team-name--home"))
                        ).text.strip()
                        
                        away_team = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 
                            "body > div.page-container.page-container--legacy-link-banner-visible > div.above-content.clearfix > div.p0c-soccer-match-details-header > div > div.p0c-soccer-match-details-header__row > a.p0c-soccer-match-details-header__team-name.p0c-soccer-match-details-header__team-name--away"))
                        ).text.strip()
                        
                        # BAY kontrolü
                        if home_team == 'BAY' or away_team == 'BAY':
                            logger.info(f"BAY maçı atlanıyor: {home_team} vs {away_team}")
                            driver.close()
                            driver.switch_to.window(main_window)
                            save_progress(i + 1, last_saved_date, logger)
                            break
                        
                        # Maç tarihini al
                        match_date = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 
                            "body > div.page-container.page-container--legacy-link-banner-visible > div.above-content.clearfix > div.p0c-soccer-match-details-header > div > div.p0c-soccer-match-details-header__info-container > p:nth-child(2) > span"))
                        ).text.strip()
                        
                        # Tarih kontrolü yap
                        check_match_date(match_date, driver, logger)
                        
                        # Maç skorlarını al
                        home_scores, away_scores = get_match_scores(driver, logger)
                        
                        # Maç sonucunu belirle
                        home_result, away_result = get_match_result(home_scores['MS Gol'], away_scores['MS Gol'])
                        
                        # Sonuçları istatistiklere ekle
                        home_scores['Sonuç'] = home_result
                        away_scores['Sonuç'] = away_result
                        
                        logger.info(f"Maç: {home_team} vs {away_team} - Tarih: {match_date}")
                        
                        # İstatistik butonunu bekle ve tıkla
                        logger.info("İstatistik butonuna tıklanıyor...")
                        stats_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 
                            "body > div.page-container.page-container--legacy-link-banner-visible > div.above-content.clearfix > div.widget-match-detail-submenu > div > a.widget-match-detail-submenu__icon.widget-match-detail-submenu__icon--stats"))
                        )
                        driver.execute_script("arguments[0].click();", stats_button)
                        
                        # İstatistik sayfasının yüklenmesini bekle
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "#widget-match-live-stats-1"))
                        )
                        
                        # Tüm istatistikleri topla
                        home_stats = home_scores.copy()  # Skorları ekle
                        away_stats = away_scores.copy()  # Skorları ekle
                        
                        # Tab selectors
                        tab_selectors = [
                            '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[1]/a',
                            '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[2]/a',
                            '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[3]/a',
                            '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[4]/a',
                            '//*[@id="widget-match-live-stats-1"]/div/div/div/div/ul/li[5]/a'
                        ]
                        
                        # Her tab için istatistikleri topla
                        for tab_selector in tab_selectors:
                            tab_stats = collect_stats_from_tab(driver, tab_selector, logger)
                            # İstatistikleri ana sözlüklere ekle
                            for stat_name, (home_value, away_value) in tab_stats.items():
                                home_stats[stat_name] = home_value
                                away_stats[stat_name] = away_value
                        
                        # İstatistikleri CSV'ye kaydet
                        save_match_stats(home_team, away_team, True, home_stats, match_date, logger)
                        save_match_stats(away_team, home_team, False, away_stats, match_date, logger)
                        
                        # Sekmeyi kapat ve ana pencereye geri dön
                        logger.info("Sekme kapatılıyor...")
                        driver.close()
                        driver.switch_to.window(main_window)
                        
                        # Her maçtan sonra ilerlemeyi ve tarihi kaydet
                        save_progress(i + 1, match_date, logger)
                        
                        break  # Başarılı işlem sonrası döngüden çık
                        
                    except Exception as e:
                        retry_count += 1
                        logger.error(f"{i+1}. maç işlenirken hata: {str(e)} (Deneme {retry_count}/{max_retries})")
                        
                        try:
                            driver.quit()
                        except:
                            pass
                        
                        if retry_count < max_retries:
                            logger.info("Tarayıcı yeniden başlatılıyor...")
                            driver = setup_driver()
                            
                            url = get_url()
                            logger.info(f"Ziyaret edilecek URL: {url}")
                            driver.get(url)
                            logger.info("Sayfa açıldı")
                            
                            time.sleep(random.uniform(5, 10))
                            
                            elements = WebDriverWait(driver, 5).until(
                                EC.presence_of_all_elements_located((By.CLASS_NAME, "p0c-competition-match-list__status"))
                            )
                        else:
                            logger.error(f"{i+1}. maç için maksimum deneme sayısına ulaşıldı, sonraki maça geçiliyor")
                            save_progress(i + 1, match_date if 'match_date' in locals() else last_saved_date, logger)
            
            if start_index + 10 < len(elements):
                logger.info("10 maç tamamlandı, uzun bekleme yapılıyor...")
                # 10 maç sonrası 5-10 saniye arası bekle
                wait_time = random.uniform(5, 10)
                logger.info(f"{wait_time:.1f} saniye bekleniyor...")
                time.sleep(wait_time)
                
                logger.info("Tarayıcı yeniden başlatılıyor...")
                driver.quit()
                
                # Yeni oturum başlatmadan önce de bekle
                time.sleep(random.uniform(5, 10))
                
                driver = setup_driver()
                logger.info("Firefox başarıyla yeniden başlatıldı")
                
                url = get_url()
                logger.info(f"Ziyaret edilecek URL: {url}")
                driver.get(url)
                logger.info("Sayfa açıldı")
                
                time.sleep(get_random_delay())
                
                elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "p0c-competition-match-list__status"))
                )
            
            start_index += 10
        
        # Tüm maçlar tamamlandığında progress.txt dosyasını sil
        try:
            progress_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'progress.txt')
            if os.path.exists(progress_file):
                os.remove(progress_file)
                logger.info("İlerleme dosyası silindi")
                
                # Sezon bilgilerini güncelle
                if update_season_config(logger):
                    # Tarayıcıyı kapat
                    logger.info("Tarayıcı kapatılıyor...")
                    driver.quit()
                    logger.info("Tarayıcı başarıyla kapatıldı")
                    
                    # Uygulamayı yeniden başlat
                    restart_application(logger)
                
        except Exception as e:
            logger.error(f"İlerleme dosyası silinirken hata: {str(e)}")
                
    except Exception as e:
        logger.error(f"Maç elementleri işlenirken hata oluştu: {str(e)}")
        raise

def update_season_config(logger):
    """Sezon bilgilerini günceller"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.py')
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Mevcut sezon değerlerini al
        current_start = None
        current_end = None
        
        for line in lines:
            if 'SEASON_START = ' in line:
                current_start = line.split('"')[1]
            elif 'SEASON_END = ' in line:
                current_end = line.split('"')[1]
        
        # 2010-2011 sezonuna ulaşıldıysa programı sonlandır
        if current_start == "2014" and current_end == "2015":
            logger.info("2014-2015 sezonuna ulaşıldı. Program sonlandırılıyor...")
            sys.exit(0)
            
        # Sezon değerlerini güncelle
        for i, line in enumerate(lines):
            if 'SEASON_START = ' in line:
                current_year = line.split('"')[1]
                new_year = str(int(current_year) - 1)
                lines[i] = f'SEASON_START = "{new_year}"\n'
            elif 'SEASON_END = ' in line:
                current_year = line.split('"')[1]
                new_year = str(int(current_year) - 1)
                lines[i] = f'SEASON_END = "{new_year}"\n'
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        logger.info(f"Sezon bilgileri güncellendi: {new_year}-{str(int(new_year) + 1)}")
        return True
        
    except Exception as e:
        logger.error(f"Sezon bilgileri güncellenirken hata: {str(e)}")
        return False

def save_last_match_date(match_date, logger):
    """Son maç tarihini kaydeder"""
    try:
        last_match_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_match.txt')
        with open(last_match_file, 'w', encoding='utf-8') as f:
            f.write(match_date)
        logger.info(f"Son maç tarihi kaydedildi: {match_date}")
        return True
    except Exception as e:
        logger.error(f"Son maç tarihi kaydedilirken hata: {str(e)}")
        return False

def get_last_match_date(logger):
    """Son kaydedilen maç tarihini okur"""
    try:
        last_match_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last_match.txt')
        if os.path.exists(last_match_file):
            with open(last_match_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        logger.error(f"Son maç tarihi okunurken hata: {str(e)}")
    return None

def restart_application(logger):
    """Uygulamayı yeniden başlatır"""
    try:
        logger.info("Uygulama yeniden başlatılıyor...")
        python = sys.executable
        script_path = os.path.abspath(__file__)
        os.execl(python, python, script_path)
    except Exception as e:
        logger.error(f"Uygulama yeniden başlatılırken hata: {str(e)}")

def main():
    """Ana program fonksiyonu"""
    logger = get_logger()
    try:
        driver = setup_driver()
        url = get_url()
        logger.info(f"Ziyaret edilecek URL: {url}")
        driver.get(url)
        logger.info("Sayfa açıldı")
        
        click_match_elements(driver, logger)
    except Exception as e:
        logger.error(f"Program çalışırken hata: {str(e)}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main() 