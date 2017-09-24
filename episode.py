import os
from urllib.parse import urlencode

import pickle
import requests
from bs4 import BeautifulSoup


class Episode:
    """
    namedtupel 'Episode'와 같은 역할을 할 수 있도록 생성
    """

    def __init__(self, webtoon, no, url_thumbnail, title, rating, created_date):
        self._webtoon = webtoon
        self._no = no
        self._url_thumbnail = url_thumbnail
        self._title = title
        self._rating = rating
        self._created_date = created_date
        self.num_images = 0

        self.thumbnail_dir = f'webtoon/{self.webtoon.title_id}_thumbnail'
        self.image_dir = f'webtoon/{self.webtoon.title_id}_images/{self.no}'
        # ex) webtoon/마왕이 되는 중2야_images/1/1.jpg
        # ex) webtoon/마왕이 되는 중2야_images/1/2.jpg
        # self.save_thumbnail()

    @property
    def webtoon(self):
        return self._webtoon

    @property
    def no(self):
        return self._no

    @property
    def url_thumbnail(self):
        return self._url_thumbnail

    @property
    def title(self):
        return self._title

    @property
    def rating(self):
        return self._rating

    @property
    def created_date(self):
        return self._created_date

    @property
    def has_thumbnail(self):
        """
        현재경로/webtoon/{self.webtoon.title_id}_thumbnail/{self.no}.jpg
          파일이 있는지 검사 후 리턴
        :return:
        """
        path = f'webtoon/{self.thumbnail_dir}/{self.no}.jpg'
        return os.path.exists(path)

    def save_thumbnail(self, force_update=True):
        """
        Episode 자신의 img_url에 있는 이미지를 저장한다
        :param force_update:
        :return:
        """
        # 만약 thumbnail이 경로에 없거나 있더라도 강제 업데이트이면,
        if not self.has_thumbnail or force_update:
            # thumbnail image 저장할 디렉토리 생성
            os.makedirs(f'{self.thumbnail_dir}', exist_ok=True)
            # request로 url_thumbnail 정보 받아오기
            response = requests.get(self.url_thumbnail)
            # 받아온 이미지 이진 데이터를 이미지 파일로 경로에 저장
            filepath = f'{self.thumbnail_dir}/{self.no}.jpg'
            with open(filepath, 'wb') as f:
                f.write(response.content)

    def _save_images(self):
        """
        자기자신의 페이지(각 episode페이지)의 img들을 다운로드
        webtoon
         /{self.webtoon.title_id}_images/{self.no}/{각 loop index}.jpg
        :return:
        """
        # 이미지들을 저장할 디렉토리를 생성한다 f'webtoon/{self.webtoon.title_id}_images/{self.no}'
        os.makedirs(self.image_dir, exist_ok=True)

        # requests 모듈에 적절한 인자 값을 줘서 해당 에피소드로부터 모든 img_url 들을 받아온다.
        # http://comic.naver.com/webtoon/detail.nhn?titleId=641253&no=149
        params = {
            'titleId': self.webtoon.title_id,
            'no': self.no,
        }

        url_contents = "http://comic.naver.com/webtoon/detail.nhn?" + urlencode(params)
        response = requests.get(url_contents)
        soup = BeautifulSoup(response.text, 'html.parser')
        episode_img_list = soup.select('.wt_viewer img')
        episode_img_url_list = [img.attrs.get('src') for img in episode_img_list]

        # bs4를 통해 img_url들을 loop로 돌며 img를 개별로 하나씩 저장
        # /{self.webtoon.title_id}_images/{self.no}/{각 loop index}.jpg
        for index, img_url in enumerate(episode_img_url_list):
            # 웹툰 본문은 권한이 없으면 403 Error가 발생하므로, \
            # headers에 Referer 정보를 제공해서 request를 보내야 함
            headers = {
                'Referer': url_contents
            }
            image_file_data = requests.get(img_url, headers=headers).content
            open(self.image_dir + f'/{index + 1}.jpg', 'wb').write(image_file_data)
        else:
            self.num_images = index + 1

    def _make_html(self):
        pass
