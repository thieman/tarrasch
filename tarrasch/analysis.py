import requests

def upload_analysis(pgn_string):
    """Uploads a PGN to lichess.org and returns the URL
    to view the analysis."""

    r = requests.post('http://en.lichess.org/import', data={'pgn': pgn_string}, timeout=15)
    r.raise_for_status()
    return r.request.url
