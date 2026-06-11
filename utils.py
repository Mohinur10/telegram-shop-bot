import requests

def upload_to_telegraph(photo_file_id, bot):
    try:
        file_info = bot.get_file(photo_file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        files = {'fileToUpload': ('image.jpg', downloaded_file, 'image/jpeg')}
        data = {'reqtype': 'fileupload'}
        response = requests.post('https://catbox.moe/user/api.php', data=data, files=files)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            print(f"Catbox upload error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error uploading image: {e}")
    
    return None