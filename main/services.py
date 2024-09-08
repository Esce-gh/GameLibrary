import requests
from django.conf import settings
from django.core.cache import cache
import logging


logger = logging.getLogger(__name__)


class Igdb:
    def __init__(self):
        self.client_id = settings.TWITCH_CLIENT_ID
        self.client_secret = settings.TWITCH_CLIENT_SECRET

    def _get_authentication_headers(self):
        return {
            'Client-ID': self.client_id,
            'Authorization': f"Bearer {self.get_access_token()}",
        }

    def get_access_token(self):
        token = cache.get('access_token')
        if token is None:
            self._renew_access_token()
            token = cache.get('access_token')
        return token

    def _renew_access_token(self):
        url = 'https://id.twitch.tv/oauth2/token'
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }

        response = requests.post(url, params=params)
        response.raise_for_status()

        token_data = response.json()
        cache.set('access_token', token_data['access_token'], timeout=token_data['expires_in'])

    def extended_search(self, title, excluded_ids):
        url = "https://api.igdb.com/v4/games"
        headers = self._get_authentication_headers()
        exclude_string = ''
        if excluded_ids:
            exclude_string = f'& id != {"(" + ",".join(map(str, excluded_ids)) + ")"}'
        query = (f'fields id,name,total_rating_count,cover.image_id, websites.url, websites.category; '
                 f'where name ~ *"{title}"* &'
                 f' (category=0 | category=2 | category=8 | category=9) &'
                 f' version_parent = null'
                 f' {exclude_string};'
                 f'sort total_rating_count desc;'
                 f'limit 10;')

        response = requests.post(url, headers=headers, data=query)
        response.raise_for_status()
        response = response.json()
        for g in response:
            if 'cover' in g:
                g['image_id'] = g['cover']['image_id']
            else:
                g['image_id'] = None
            g.pop('cover', None)
            for w in g['websites']:
                if w['category'] != 13:
                    continue
                if w['url'][-1] == '/':
                    w['url'] = w['url'][:-1]
                try:
                    g['steam_id'] = int(w['url'].split("/")[-1])
                except ValueError:
                    try:
                        g['steam_id'] = int(w['url'].split("/")[-2])
                    except ValueError:
                        logger.exception(f'Could not parse steam id for url {w["url"]}')
                break
            g.pop('websites', None)
        return response

    def get_games_by_id(self, ids):
        url = "https://api.igdb.com/v4/games/"
        headers = self._get_authentication_headers()
        query = f'fields name, id; where id = {"(" + ",".join(map(str, ids)) + ")"};'
        response = requests.post(url, headers=headers, data=query)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def save_covers(image_id, size):
        url = f"https://images.igdb.com/igdb/image/upload/t_cover_{size}/{image_id}.jpg"
        response = requests.get(url)
        response.raise_for_status()
        with open(f"./static/covers/{size}_{image_id}.jpg", "wb") as f:
            f.write(response.content)


class SteamApi:
    def __init__(self):
        self.key = settings.STEAM_API_KEY

    def get_user_library(self, url):
        url = (f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
               f"?key={self.key}&"
               f"steamid={self._get_user_id(url)}&"
               f"format=json")
        response = requests.get(url)
        response.raise_for_status()
        response = response.json()['response']['games']
        return response

    @staticmethod
    def _get_user_id(url):
        url = f'https://steamid.venner.io/raw.php?input={url}'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['steamid64']
