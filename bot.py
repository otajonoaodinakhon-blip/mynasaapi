import os
import requests
from datetime import datetime
from flask import Flask, request
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
NASA_API_KEY = os.getenv('NASA_API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')

app = Flask(__name__)

# Telegram API url
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# NASA APOD API - har safar random rasm olish uchun count parametri
def get_nasa_apod_images(count=10):
    """
    NASA APOD API dan random rasmlarni olish
    API: https://api.nasa.gov/planetary/apod?api_key=KEY&count=10
    """
    url = f"https://api.nasa.gov/planetary/apod"
    params = {
        'api_key': NASA_API_KEY,
        'count': count,
        'thumbs': True
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        images = response.json()
        print(f"✅ NASA API dan {len(images)} ta rasm olindi")
        return images
    except Exception as e:
        print(f"❌ NASA API xatosi: {e}")
        return []

def send_photo_to_channel(image_url, caption):
    """Rasmni Telegram kanalga yuborish"""
    send_url = f"{TELEGRAM_API}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_ID,
        'photo': image_url,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(send_url, data=payload, timeout=30)
        result = response.json()
        if result.get('ok'):
            print(f"✅ Rasm yuborildi: {image_url[:50]}...")
            return True
        else:
            print(f"❌ Telegram xatosi: {result}")
            return False
    except Exception as e:
        print(f"❌ Yuborish xatosi: {e}")
        return False

def send_batch_to_channel():
    """5 daqiqada 10 ta rasm + ma'lumotni kanalga yuborish"""
    print(f"\n{'='*50}")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 NASA APOD dan 10 ta rasm olinmoqda...")
    
    # NASA API dan 10 ta random rasm olish
    images = get_nasa_apod_images(10)
    
    if not images:
        print("❌ Hech qanday rasm olinmadi")
        return
    
    # Har bir rasmni kanalga yuborish
    success_count = 0
    for i, image_data in enumerate(images, 1):
        # Faqat rasm tipidagi media larni yuborish
        if image_data.get('media_type') != 'image':
            print(f"⏭️ {i}-media video, o'tkazib yuborildi")
            continue
        
        # Rasm URL
        image_url = image_data.get('hdurl') or image_data.get('url')
        if not image_url:
            continue
        
        # Caption tayyorlash - NASA dan kelgan ORIGINAL ma'lumotlar
        title = image_data.get('title', 'No Title')
        date = image_data.get('date', 'Unknown Date')
        explanation = image_data.get('explanation', 'No description')
        copyright_text = image_data.get('copyright', 'NASA')
        
        # Captionni 1024 belgidan qisqa qilish (Telegram limiti)
        if len(explanation) > 800:
            explanation = explanation[:800] + '...'
        
        caption = f"<b>{title}</b>\n\n"
        caption += f"📅 {date}\n"
        caption += f"📸 {copyright_text}\n\n"
        caption += f"{explanation}\n\n"
        caption += f"🔗 <a href='{image_url}'>HD Rasm</a> | NASA APOD"
        
        # Rasmni yuborish
        if send_photo_to_channel(image_url, caption):
            success_count += 1
        
        # Telegram rate limit uchun kichik pauza
        import time
        time.sleep(1)
    
    print(f"✅ {success_count} ta rasm kanalga yuborildi")
    print(f"{'='*50}\n")

# Webhook endpoint (Render uchun)
@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint - hech qanday komanda ishlatilmaydi"""
    return {"status": "ok"}, 200

@app.route('/')
def home():
    return {"status": "NASA Bot ishlayapti", "time": datetime.now().isoformat()}

# Webhook ni sozlash (faqat bir marta)
def setup_webhook():
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        print("⚠️ WEBHOOK_URL topilmadi")
        return
    
    url = f"{TELEGRAM_API}/setWebhook"
    response = requests.post(url, data={'url': webhook_url})
    print(f"Webhook sozlandi: {response.json()}")

if __name__ == '__main__':
    print("\n🚀 NASA APOD Telegram Bot ishga tushmoqda...")
    print(f"📢 Kanal ID: {CHANNEL_ID}")
    print(f"🔑 NASA API Key: {NASA_API_KEY[:10]}...")
    
    # Webhook ni sozlash
    setup_webhook()
    
    # Scheduler - har 5 daqiqada 10 ta rasm yuborish
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_batch_to_channel, 'interval', minutes=5)
    scheduler.start()
    
    print("✅ Bot ishga tushdi!")
    print("🕐 Har 5 daqiqada 10 ta NASA APOD rasmi kanalga yuboriladi")
    
    # Birinchi yuborishni darhol boshlash
    send_batch_to_channel()
    
    # Flask serverni ishga tushirish
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
