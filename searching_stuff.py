import random
import requests
import utils


def search(request):
    key = utils.read_config()['key']
    response = requests.get(f'https://www.googleapis.com/customsearch/v1?&key={key}&'
                            f'cx=21b004bff34927799&searchType=image&q={request}').json()
    data = response['items']
    links = [item['link'] for item in data]
    return links


def get_random_url(request):
    try:
        links = search(request)
        return random.choice(links) if links != [] else None
    except Exception:
        return None
