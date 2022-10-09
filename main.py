
import urllib.request, json 
import time
import sys
import requests
webhook_url = 'WEBHOOK_URL'

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'McLaren/600 CFNetwork/1325.0.1 Darwin/21.1.0')]
def get_data():
    response = opener.open('https://www.mclaren.com/racing/api/feed/v1/commentary/')
    data = json.load(response)
    return data

sources_dict = {
    'cm': ("McLaren", "https://pbs.twimg.com/ext_tw_video_thumb/1446191112947970054/pu/img/o0FYOlkp44Q770aT.jpg"),
    'p_RIC': ("Daniel's Engineer", "https://media-cdn.mclaren.com/media/images/galleries/GP2102_092405MS1_5133.jpg"),
    'p_NOR': ("Lando's Engineer", "https://media-cdn.mclaren.com/media/images/galleries/GP2102_092405MS1_5133.jpg"),
    'd_RIC': ("Daniel Ricciardo", "https://media-cdn.mclaren.com/media/images/drivers/hero/DR_website_hero_image_March_2022.jpg"),
    'd_NOR': ("Lando Norris", "https://media-cdn.mclaren.com/media/images/drivers/hero/LN_website_hero_image_March_2022.jpg")
}


if __name__ == '__main__':
    try:
        _, event_selection, mode = sys.argv
    except ValueError:
        print("Usage: python main.py <event> <mode>")
        print("events include R, Q, P3, P2, P1")
        print("mode must be either discord or console")
        exit(1)
    if mode == 'discord':
        current_length = len(get_data()[event_selection])
    else:
        current_length = 0
    
    while True:
        time.sleep(1)
        current_data = get_data()
        if len(current_data[event_selection]) > current_length:
            for message in range(len(current_data[event_selection])-current_length - 1, -1, -1):
                if mode == 'console':
                    print(current_data[event_selection][message]['source'])
                    print(current_data[event_selection][message]['commentary'])
                elif mode == 'discord':
                    data = {
                        "username": sources_dict[current_data[event_selection][message]['source']][0],
                        "content": current_data[event_selection][message]['commentary'],
                        "avatar_url": sources_dict[current_data[event_selection][message]['source']][1]
                    }
                    result = requests.post(webhook_url, json = data)
            current_length = len(current_data[event_selection])