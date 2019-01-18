from sys import argv
from requests import get, head
from lxml import html
from os.path import exists
from fake_useragent import UserAgent
from click import command, option, argument
from mutagen.id3 import ID3, TIT2, TALB, COMM


def get_num(value: str)-> tuple:
    if '-' in value:
        begin, end = value.split('-')
        if not begin:
            begin = '1'
        if not end:
            end = '-1'
        return begin, end
    elif value.isdigit():
        return value, value
    return '-1', '-1'

@command()
@option('-s', '--show', required=False, is_flag=True, help='Вывести список композиций')
@option('-d','--download', default='-', required=False, help='список скачиваемых композиций в формате <Start>:<End>')
@argument('name', nargs=-1)
def get_song(show, download, name):
    begin, end = [int(value) for value in get_num(download)]
    url_base = "http://zaycev.net"
    url_add = ''
    ua = UserAgent()
    header = {
        'User-Agent':
            ua.random}
    param = None
    if name:
        url_add = "search.html"
        query = '+'.join(name)
        param = {"query_search": query}
    http = get(f'{url_base}/{url_add}', headers=header, params=param)
    response = html.fromstring(http.text)
    links = response.xpath('//div[@data-rbt-content-id]/@data-url')
    artists = response.xpath('//*[@itemprop="byArtist"]/a/text()')
    songs = response.xpath('//*[@itemprop="name"]/a/text()')
    begin = max(begin, 1)
    if end == -1 or end > len(songs):
        end = len(songs)
    begin = min(begin, end)
    if show:
        print('Доступные композиции:')
    if links:
        i = 1
        shift = 0
        while True:
            url = get(f'{url_base}{links[i - 1]}').json()['url']
            presence = head(url)
            if presence.status_code != 200 and presence.headers.get('Content-Type') != 'audio/mpeg':
                i += 1
                continue
            shift += 1
            if shift >= begin:
                title = f'{artists[i-1].strip()} – {songs[i-1].strip()}.mp3'
                size = round(int(presence.headers.get('Content-Length', '0')) / 1048576, 1)
                if show:
                    print(f'{shift}. {title} ({size} Мб)')
                else:
                    while exists(title):
                        title = '_' + title
                    number = '' if begin == end else f"{shift}."
                    print(f"Загружается: {number}{title}", end='', flush=True)
                    song = get(url, stream=True)
                    with open(title, 'wb') as file:
                        for index, chunk in enumerate(song.iter_content(1048576)):
                            text = f"\rЗагружается: {number}{title}{'.' * (index % 4)}"
                            print(f"\r{' ' * (len(text) + 2)}", end='', flush=True)
                            print(text, end='', flush=True)
                            file.write(chunk)
                    audio = ID3(title)
                    song_name = audio['TIT2'][0][:-13]
                    audio.add(TIT2(text=song_name))
                    audio.add(TALB(text=''))
                    audio.add(COMM(lang='eng', text=''))
                    audio.save()
                    print(f"\rЗагружено: {number}{title}     ")
            if shift >= end or i >=len(links):
                break
            i += 1
    # else:
    #     exit(2)


if __name__ == '__main__':
    # if len(argv) > 1:
    #     if '=' in argv[-1]:
    #         get_song(*argv[1:-1], count=get_num(argv[-1].split('=')[-1]))
    #     else:
    #         get_song(*argv[1:], count=('1', '1'))
    # else:
    #     get_song(*'', count=get_num('l',))
    get_song()
