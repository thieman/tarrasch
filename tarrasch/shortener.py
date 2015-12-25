import requests

def shorten_url(url):
    r = requests.get('http://is.gd/create.php?format=simple&url={}'.format(url))
    r.raise_for_status()
    return r.text
