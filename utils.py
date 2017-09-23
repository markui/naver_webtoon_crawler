from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from collections import namedtuple
from episode import Episode

# 3. 받아온 정보를 담을 namedtuple() 변수 type를 생성한다
Webtoon = namedtuple('Webtoon', ['title_id', 'img_url', 'title'])
# Episode = namedtuple('Episode', ['no', 'img_url', 'title', 'rating', 'created_date'])

LIST_HTML_HEAD = '''<html>
<head>
    <meta charset="utf-8">
</head>
<body>
<table>
'''

LIST_HTML_TR = '''<tr>
    <td>{image_url}</td>
    <td>{title}</td>
    <td>{rating}</td>
    <td>{created_date}</td>
</tr>
'''

LIST_HTML_TAIL = '''<table>
</body>
</html>
'''


# 특정 페이지에 있는 모든 에피소드를 리스트로 가져온다. / 페이지 수를 정의하지 않는다면
def get_page_episode_list(webtoon, page=1):
    webtoon_base_url = 'http://comic.naver.com/webtoon/list.nhn'
    response = requests.get(webtoon_base_url, params={'titleId': webtoon.title_id, 'page': page})
    soup = BeautifulSoup(response.text, 'html.parser')

    webtoon_page_episodes = soup.select('tr')[1:]

    webtoon_page_episode_list = [

        Episode(
                webtoon=webtoon,
                no=parse_qs(urlparse(item.select_one('td a').attrs.get('href')).query)['no'][0],
                url_thumbnail=item.select_one('td a img').attrs.get('src'),
                title=item.select_one('td.title a').text,
                rating=item.select_one('div.rating_type strong').text,
                created_date=item.select_one('td.num').text)

        for item
        in webtoon_page_episodes
        if not item.attrs.get('class')

    ]

    return webtoon_page_episode_list
