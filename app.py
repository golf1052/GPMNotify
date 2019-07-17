from flask import Flask, request
from gmusicapi import Mobileclient
import oauth2client
import json
import datetime

app = Flask(__name__)

@app.route('/', methods=['POST'])
def process():
    body = request.json
    if 'api' in body:
        endpoint = body['api']
        if endpoint == 'login':
            api = Mobileclient()
            flow = oauth2client.client.OAuth2WebServerFlow(**api._session_class.oauth._asdict())
            url = flow.step1_get_authorize_url()
            return {'url': url}
        elif endpoint == 'new_releases':
            api = Mobileclient()
            credentials = oauth2client.client.OAuth2Credentials.from_json(body['creds'])
            api._authtype = 'oauth'
            api.session.login(credentials)
            albums = get_albums(api)
            return {'albums': albums}
    elif 'auth' in body:
        code = body['auth']
        api = Mobileclient()
        flow = oauth2client.client.OAuth2WebServerFlow(**api._session_class.oauth._asdict())
        credentials = flow.step2_exchange(code)
        string_creds = credentials.to_json()
        return {'creds': string_creds}
    return ''

def get_albums(api):
    all_songs = api.get_all_songs()
    all_albums = set()
    for song in all_songs:
        if 'albumId' in song:
            all_albums.add(song['albumId'])
    
    all_artists = set()
    for album_id in all_albums:
        album = api.get_album_info(album_id, False)
        if 'artistId' in album:
            for artist_id in album['artistId']:
                all_artists.add(artist_id)
        
    current_year = datetime.datetime.now().year
    album_id_map = {}
    albums = []
    for artist_id in all_artists:
        artist = api.get_artist_info(artist_id, max_top_tracks=0, max_rel_artist=0)
        if 'albums' in artist:
            for album in artist['albums']:
                if 'year' in album:
                    if album['year'] == current_year:
                        if album['albumId'] not in album_id_map:
                            album_id_map[album['albumId']] = album
    
    for album_id, album in album_id_map.iteritems():
        albums.append(create_simple_album_from_album(album))
    return albums

def create_simple_album_from_album(album):
    return {'albumId': album['albumId'], 'artist': album['artist'], 'name': album['name'], 'year': album['year']}

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
