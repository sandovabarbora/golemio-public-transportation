import requests
import logging


def get_stops(base_url, token, stop_names):
    params = {
        'names[]': stop_names,
        'offset': 0
    }

    headers = {
        'accept': 'application/json',
        'X-Access-Token': token
    }

    response = requests.get(base_url, params=params, headers=headers)
    if response.status_code != 200:
        logging.error(f'Error: {response.status_code}')
        return

    return response.json()