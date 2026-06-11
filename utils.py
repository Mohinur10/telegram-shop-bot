import requests
import time
import os

def upload_to_telegraph(photo_file_id, bot, max_retries=3):
    endpoints = [
        'https://telegra.ph/upload',
        'https://graph.org/upload'
    ]
    file_data = None
    try:
        file_info = bot.get_file(photo_file_id)
        file_data = bot.download_file(file_info.file_path)
    except Exception as e:
        print(f"[ERROR] Rasm yuklab olinmadi: {e}")
        return None

    for attempt in range(max_retries):
        for url in endpoints:
            try:
                files = {'file': ('image.jpg', file_data, 'image/jpeg')}
                resp = requests.post(url, files=files, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0 and 'src' in data[0]:
                        return 'https://telegra.ph' + data[0]['src']
                    elif isinstance(data, dict) and data.get('error'):
                        print(f"[ERROR] Telegra.ph xatosi: {data['error']}")
                else:
                    print(f"[WARN] {url} javob kodi {resp.status_code}")
            except Exception as e:
                print(f"[WARN] {url} ga ulanishda xatolik: {e}")
        time.sleep(1)

    # Fallback: ImgBB (bepul API kaliti kerak)
    api_key = os.getenv('IMGBB_API_KEY')
    if api_key:
        import base64
        b64 = base64.b64encode(file_data).decode('utf-8')
        try:
            resp = requests.post(
                'https://api.imgbb.com/1/upload',
                data={'key': api_key, 'image': b64},
                timeout=15
            )
            if resp.status_code == 200:
                json_data = resp.json()
                if json_data.get('success'):
                    return json_data['data']['url']
        except Exception as e:
            print(f"[ERROR] ImgBB yuklash xatosi: {e}")
    return None