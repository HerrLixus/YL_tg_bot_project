import requests
from pprint import pprint
response = requests.get(f"https://yandex.ru/images/search?text={input()}").text
data = [x.split('"><img')[0] for x in response.split('<a class="serp-item__link" href="')][1:]


for index, item in enumerate(list(data)[:10]):
    url = item.split('img_url=')[1].split('&amp')[0]
    url = url.replace('%2F', '/')
    url = url.replace('%3A', ':')
    response = requests.get(url).content
    with open(str(index) + '.jpeg', 'wb') as file:
        file.write(response)
