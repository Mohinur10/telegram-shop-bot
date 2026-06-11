import requests

def upload_to_telegraph(photo_file_id, bot):
    try:
        file_info = bot.get_file(photo_file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        files = {'file': ('image.jpg', downloaded_file, 'image/jpeg')}
        response = requests.post('https://telegra.ph/upload', files=files)
        
        if response.status_code == 200:
            res_json = response.json()
            # Telegra.ph returns a list of objects on success
            if isinstance(res_json, list) and len(res_json) > 0 and 'src' in res_json[0]:
                return 'https://telegra.ph' + res_json[0]['src']
            elif isinstance(res_json, dict) and 'error' in res_json:
                print(f"Telegra.ph error: {res_json['error']}")
    except Exception as e:
        print(f"Error uploading to Telegra.ph: {e}")
    
    return None
