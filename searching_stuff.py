import requests
import random


def get_random_url(request):
    response = requests.get(f"https://yandex.ru/images/search?text={request}").text
    data = [x.split('"><img')[0] for x in response.split('<a class="serp-item__link" href="')][1:]

    urls = list()
    for index, item in enumerate(list(data)[:10]):
        url = item.split('img_url=')[1].split('&amp')[0]
        url = url.replace('%2F', '/')
        url = url.replace('%3A', ':')
        urls.append(url)

    return random.choice(urls)
