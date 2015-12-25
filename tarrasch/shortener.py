import requests

def shorten_url(url):
    r = requests.post('http://is.gd/create.php',
                      data={'url': url,
                            'shorturl': '',
                            'opt': 0})
    r.raise_for_status()
    return r.text
