import requests
import random


def get_random_url(request):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                             ' Chrome/98.0.4758.109 Safari/537.36 OPR/84.0.4316.52'}
    response = requests.get(f"https://yandex.ru/images/search?text={request}", headers=headers).text
    data = [x.split('"><img')[0] for x in response.split('<a class="serp-item__link" href="')][1:]

    urls = list()
    for index, item in enumerate(list(data)[:10]):
        url = item.split('img_url=')[1].split('&amp')[0]
        url = url.replace('%2F', '/')
        url = url.replace('%3A', ':')
        urls.append(url)
    return random.choice(urls) if urls != [] else None
