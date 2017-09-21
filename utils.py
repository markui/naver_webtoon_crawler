from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from collections import namedtuple

Episode = namedtuple('Episode', ['no', 'img_url', 'title', 'rating', 'created_date'])


# 특정 페이지에 있는 모든 에피소드를 리스트로 가져온다. / 페이지 수를 정의하지 않는다면
def get_page_episode_list(webtoon_id, page=1):
    webtoon_base_url = 'http://comic.naver.com/webtoon/list.nhn'
    response = requests.get(webtoon_base_url, params={'titleId': webtoon_id, 'page': page})
    soup = BeautifulSoup(response.text, 'html.parser')

    webtoon_page_episodes = soup.select('tr')[1:]

    webtoon_page_episode_list = [
        Episode(no=parse_qs(urlparse(item.select_one('td a').attrs.get('href')).query)['no'][0],
                img_url=item.select_one('td a img').attrs.get('src'),
                title=item.select_one('td.title a').text,
                rating=item.select_one('div.rating_type strong').text,
                created_date=item.select_one('td.num').text)

        for item
        in webtoon_page_episodes
        if not item.attrs.get('class')

    ]

    return webtoon_page_episode_list