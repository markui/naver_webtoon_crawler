import os
from urllib.parse import parse_qs, urlparse
import requests
from bs4 import BeautifulSoup
import utils
import pickle
import glob


# 크롤링하는 방법
# 1. from naver_crawler import NaverWebtoonCralwer
# 2. my_crawler = NaverWebtoonCrawler()
# 3. 웹툰명 입력
# 4. my_crawler.update_episode_list() => my_crawler.episode_list 에 목록 저장
# 5. my_crawler.total_episode_count(), my_crawler.up_to_date()
# 6. my_crawler.save()



# 에피소드별, 이미지 , 썸네일 저장방법
# for episode in my_cralwer.episode_list:
#   episode.save_thumbnail() 혹은 episode._save_images()

# 크롤링 해온 정보를 모두 html에 표시




class NaverWebtoonCrawler:
    """
    class NaverWebtoonCrawler생성

        인스턴스 메서드
            def get_episode_list(self, page)
                해당 페이지의 episode_list를 생성, self.episode_list에 할당
            def clear_episode_list(self)
                자신의 episode_list를 빈 리스트로 만듬
            def get_all_episode_list(self)
                webtoon_id의 모든 episode를 생성
            def add_new_episode_list(self)
                새로 업데이트된 episode목록만 생성
    """

    def __init__(self, webtoon_title=None, webtoon_title_id=None):
        """
        1. webtoon_title이 주어지면
            1-1. 해당 웹툰 검색결과를 가져와서
            1-2. 검색결과가 1개면 해당 웹툰을
                self.webtoon에 할당
            1-3. 검색결과가 2개 이상이면 선택가능하도록 목록을 보여주고
                input으로 입력받음
            1-4. 검색결과가 없으면 다시 웹툰을 검색하도록 함

        2. webtoon_title이 주어지지 않으면
            2-1. 웹툰 검색을 할 수 있는 input을 띄워줌
            2-2. 이후는 위의 1-2, 1-3을 따라감

        3. webtoon_id를 쓰던 코드를 전부 수정 (self.webtoon을 사용)
            self.webtoon은 Webtoon타입 namedtuple
        """
        # webtoon_title_id로 무엇이 왔다면,
        if webtoon_title_id:
            webtoon_search_results = self.find_webtoon(webtoon_title_id=webtoon_title_id)
            self.webtoon = webtoon_search_results[0]
            self.episode_list = self.load(init=True)

        # webtoon_title_id로 아무것도 오지 않았다면
        else:
            # webtoon title로 무엇이 왔다면,
            if webtoon_title:
                search_title = webtoon_title
                webtoon_search_results = self.find_webtoon(search_title)
                self.webtoon = webtoon_search_results[0]
                self.episode_list = self.load(init=True)
            # webtoon title로 아무것도 오지 않았다면, input을 입력할 때까지 input 받기
            else:
                while True:
                    search_title = input('검색할 웹툰명을 입력해주세요: ')
                    if search_title:
                        # input을 받은 search_title 을 바탕으로 웹툰 목록 가져오기
                        webtoon_search_results = self.find_webtoon(search_title)

                        # 1. 검색한 웹툰의 제목과 일치하는 웹상의 웹툰이 없을 경우
                        if len(webtoon_search_results) == 0:
                            print('일치하는 검색결과가 없습니다. 다시 검색하세요.')
                            continue
                        # 2. 검색한 웹툰의 제목과 일치하는 웹상의 웹툰이 하나가 있을 경우 => self.webtoon, self.episode_list 에 저장
                        elif len(webtoon_search_results) == 1:
                            print(f'찾은 웹툰 "{webtoon_search_results[0].title}"를 가져옵니다.')
                            self.webtoon = webtoon_search_results[0]
                            self.episode_list = self.load(init=True)
                            break
                        # 3. 검색한 웹툰의 제목과 일치하는 웹상의 웹툰이 여러개일 경우
                        else:
                            for index, found_webtoon in enumerate(webtoon_search_results):
                                print(f'{index + 1}. "{found_webtoon.title}"이라는 웹툰이 발견되었습니다.')
                            print('이 중에 원하는 웹툰의 제목을 선택하여 다시 검색하세요.')
                            continue
                    else:
                        print("적어도 한 글자를 입력해야 합니다!")

    def get_webtoon_list(self):
        """
        네이버 웹툰의 모든 웹툰들을 가져온다
        :return:
        """
        # 1. request를 보내서, response객체를 받아온다.(스크래핑)

        response = requests.get('http://comic.naver.com/webtoon/weekday.nhn')
        # 2. bs4를 통해서 response.text를 파싱한다.(파싱)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 3. 모든 웹툰의 id, img_url 정보를 적절한 namedtuple 형식을 담은 list로 저장하기
        webtoon_columns = soup.select('.list_area.daily_all .col ul')

        webtoon_list = [
            utils.Webtoon(
                title_id=parse_qs(urlparse(li.select_one('a').attrs.get('href')).query)['titleId'][0],
                img_url=li.select_one('img').attrs.get('src'),
                title=li.select_one('img').attrs.get('title')
            )
            for col in webtoon_columns
            for li in col.select('li')
        ]

        # 4. 중복값 없애기
        all_webtoon_list = list(set(webtoon_list))
        # webtoon_list = sorted(list(webtoon_list), key=lambda x: x.title)

        return all_webtoon_list

    def find_webtoon(self, title=None, webtoon_title_id=None):
        """
        title에 주어진 문자열로 get_webtoon_list로 받아온 웹툰 목록에서
        일치하거나 문자열이 포함되는 Webtoon 목록을 리턴
        :param title:
        :return: list(Webtoon)
        """
        if webtoon_title_id:
            wanted_webtoon_list = [
                webtoon
                for webtoon in self.get_webtoon_list()
                if webtoon_title_id == webtoon.title_id
            ]

        if title:
            wanted_webtoon_list = [
                webtoon
                for webtoon in self.get_webtoon_list()
                if title in webtoon.title
            ]

        return wanted_webtoon_list

    def get_last_page_episode(self, page):
        """
        해당 페이지 에피소드 리스트를 가져오는, dummy function
        :param page:
        :return:
        """
        self.episode_list = utils.get_page_episode_list(self.webtoon, page)

    def get_page_episode_list(self, page=1):
        """
        특정 페이지의 에피소드들을 namedtuple로 정렬된 리스트를 가져온다 (최신화부터 내림차순으로)
        :param page:
        :return: 해당 페이지의 에피소드 리스트
        """
        return utils.get_page_episode_list(self.webtoon, page)

    def get_all_episode_list(self, page=1):
        """
        특정 페이지부터 끝까지 모든 에피소드들을 namedtuple로 정렬된 리스트를 가져온다; 인자가 없다면 처음부터~끝 에피소드까지 가져온다 (최신화부터 내림차순으로)
        :param page:
        :return:
        """
        # 기존에 있던 에피소드들 삭제하고 빈 리스트 할당
        self.episode_list = list()
        while True:
            # 처음 start 페이지 게시물들 가져오기
            page_webtoon_list = utils.get_page_episode_list(self.webtoon, page)
            # 기존 리스트에 가져온 해당 페이지 에피소드 리스트 추가하기
            self.episode_list.extend(page_webtoon_list)
            # 만약에 가져왔던 페이지의 에피소드 리스트의 마지막 게시물이 첫번째 게시물이면 추출 종료
            if page_webtoon_list[-1].no == '1':
                break
            # 마지막 게시물이 첫번째 게시물이 아니면 페이지 수 넘어가기
            page += 1

        return self.episode_list

    @property
    def total_episode_count(self):
        """
        webtoon_id에 해당하는 실제 웹툰의 총 episode수를 리턴
        :return: 총 episode수 (int)
        """
        page_1_webtoon_list = utils.get_page_episode_list(self.webtoon)  # 1 페이지의 에피소드 리스트를 가져옴
        return int(page_1_webtoon_list[0].no)  # 1페이지 가장 첫번째 에피소드, 즉 최신화의 에피소드 숫자(no)를 가져옴

    @property
    def up_to_date(self):
        """
        현재 가지고있는 episode_list가 웹상의 최신 episode까지 가지고 있는지
        :return: boolean값
        """
        cur_episode_count = len(self.episode_list)
        total_episode_count = self.total_episode_count
        # if cur_episode_count == total_episode_count:
        #     return True
        # else:
        #     return False
        return cur_episode_count == total_episode_count

    def update_episode_list(self, force_update=False):
        """
        self.episode_list에 존재하지 않는 episode들을 self.episode_list에 추가
        :param force_update: 이미 존재하는 episode도 강제로 업데이트
        :return: 추가된 episode의 수 (int)
        """
        if force_update == True:  # 이미 존재하는 episode까지 강제로 업데이트하려면, 즉 처음부터 끝까지 모든 에피소드 리스트 가져오려면,
            self.get_all_episode_list()  # 처음부터 끝까지 모든 에피소드 리스트 episode_list에 업데이트하기

        else:  # 현재 존재하는 self.episode_list에 존재하지 않는 episode들만 추가하기
            if self.up_to_date:  # 만약 최신화까지 업데이트가 된 상태라면,
                print('최신화까지 이미 업데이트가 된 상태입니다')
                return 0
            elif not self.episode_list:  # 아예 아무런 episode도 가져오지 않은 상태이면
                print('아직 에피소드가 하나도 저장되지 않은 상태입니다.\n첫화부터 최신화까지 업데이트합니다')
                self.get_all_episode_list()
            else:  # 만약 최신화까지 업데이트가 되지 않은 상태라면,
                new_webtoon_list = []
                page = 1
                while True:
                    page_webtoon_list = self.get_page_episode_list(page)
                    for episode in page_webtoon_list:
                        if int(episode.no) > int(self.episode_list[0].no):
                            new_webtoon_list.append(episode)
                        else:
                            self.episode_list = new_webtoon_list + self.episode_list  # 기존의 에피소드 리스트에 새로윤 에피소트 리스트 추가
                            print('{}개의 새로운 웹툰이 추가되었습니다.'.format(len(new_webtoon_list)))
                            return len(new_webtoon_list)  # 추가된 episode의 수를 리턴함(가장 최신화부터 비교함 - while문 빠져나감
                    page += 1  # 페이지 수 증가

    def save(self, path=None):
        """
        현재폴더를 기준으로 db/<webtoon_id>.txt 파일에
        pickle로 self.episode_list를 저장

        1. 폴더 생성시
            os.path.isdir(path('db'))
                path가 directory인지 확인
            os.mkdir(path)
                path의 directory를 생성

        2. 저장시
            pickle.dump(obj, file)
        :return: None(없음)
        """

        # 1. 폴더 생성
        if not os.path.isdir('db'):
            os.mkdir('db')

        # 2. 저장시
        obj = self.episode_list
        path = 'db/{}.txt'.format(self.webtoon.title_id)
        pickle.dump(obj, open(path, 'wb'))  # open() 참조되는 값이 없어서 (변수) 저절로 닫힘!

    def load(self, path=None, init=False):
        """
        현재폴더를 기준으로 db/<webtoon_id>.txt 파일의 내용을 불러와
        pickle로 self.episode_list를 복원

        1. 만약 db폴더가 없으면 or db/webtoon_id.txt파일이 없으면
         => "불러올 파일이 없습니다" 출력

        2. 있으면 복원
        :return: None(없음)
        """

        try:
            path = f'db/{self.webtoon.title_id}.txt'
            return pickle.load(open(path, 'rb'))
        except FileNotFoundError:  # error써주는 게 규약에 맞음
            if init:  # 만약 처음 crawler를 만들 때 load해주는 거면,
                return []
            print('현재까지 수집한 웹툰 리스트 파일이 없습니다.')

    def save_list_thumbnail(self):
        """
        webtoon/{webtoon_id}_thumbnail/<episode_no>.jpg
        1. webtoon/{webtoon_id}_thumbnail이라는 폴더가 존재하는지 확인 후 생성
        2. self.episode_list를 순회하며 각 epsiode의 img_url 경로의 파일을 저장
        :return: 저장한 thumbnail 개수
        """

        # webtoon/{webtoon_id}_thumbnail에 해당하는 폴더 생성

    def make_detail_list_html(self):
        if not os.path.isdir('html'):
            os.mkdir('html')

        for e in self.episode_list:
            if not os.path.isdir(f'html/{self.webtoon.title_id}'):
                os.mkdir(f'html/{self.webtoon.title_id}')
            filename = f'html/{self.webtoon.title_id}/{e.no}.html'
            with open(filename, 'wt') as f:
                for num in range(e.num_images):
                    f.write(open(f'html/episode_images.html', 'rt').read().format(
                        episode_image=os.path.abspath(f'webtoon/{self.webtoon.title_id}_images/{e.no}/{num+1}.jpg')
                    ))

    def make_list_html(self):
        """
        self.episode_list를 html파일로 만들어준다
        webtoon/{webtoon_id}.html
        1. webtoon폴더 있는지 검사 후 생성
        2. webtoon/{webtoon_id}.html 파일객체 할당 또는 with문으로 open
        3. open한 파일에 html 앞부분 작성
        4. episode_list를 for문을 돌며 <tr>...</tr>부분 반복작성
        5. html뒷부분 작성
        6. 파일닫기 또는 with문 빠져나가기
        7. 해당파일 경로 리턴
        ex)
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body>
            <table>
                <!-- 이 부분을 episode_list의 길이만큼 반복 -->
                <tr>
                    <td><img src=".."></td>
                    <td>제목</td>
                    <td>별점</td>
                    <td>날짜</td>
                </tr>
            </table>
        </body>
        </html>
        :return: 파일의 경로
        """

        # 1. 디렉토리가 없다면 디렉토리 생성
        if not os.path.isdir('webtoon'):
            os.mkdir('webtoon')
        # 2. 웹툰 html 파일 있다면 덮어쓰기, 없다면 새로 생성
        filename = f'webtoon/{self.webtoon.title_id}.html'
        with open(filename, 'wt') as f:
            # 3. html 앞부분을 받아와서 오픈한 파일에 작성
            f.write(open('html/list_html_head.html', 'rt').read())

            # 3. html 가운데 부분을 받아와서, episode_list를 순회하며 나머지 코드 작성
            for e in self.episode_list:
                f.write(open('html/list_html_tr.html', 'rt').read().format(
                    content_images_url=os.path.abspath(f'html/{self.webtoon.title_id}/{e.no}.html'),
                    img_url=e.url_thumbnail,
                    title=e.title,
                    rating=e.rating,
                    created_date=e.created_date

                ))
            # 4. html 뒷부분을 받아와서 오픈한 파일에 작성
            f.write(open('html/list_html_tail.html', 'rt').read())
        return filename

    @staticmethod
    def make_index_html():
        """
        - index.html 생성
        0. 만약에 현재 로컬에, 크롤링 된 웹툰 파일이 있다면,(ex){self.webtoon.title_id}_images)
        1. 크롤링 된 모든 웹툰 리스트(제목, 썸네일) 출력 (self.webtoon -> title, img_url)
        2. 웹툰을 클릭하면 각 웹툰의 episode list 페이지 출력 ({self.webtoon.title_id}.html 로 <a href>태그 걸어주기)
        3. episode list 페이지는 각 episode의 detail 페이지로 이동가능한 링크를 가짐
        4. detail page는 자신의 img들을 출력
        해당 내용을 할 수 있는만큼 작성하고 Github에 Push, 과제제출 시트에 기록하기
        :return:
        """
        # 0. 만약에 현재 로컬에, 크롤링 된 웹툰 파일이 있다면,(ex){self.webtoon.title_id}_images)
        if glob.glob('webtoon/*_images'):
            images_folders = glob.glob('webtoon/*_images')
            webtoon_title_ids = [

                images_folder.split('_')[0].split('/')[1]
                for images_folder in images_folders

            ]

            # 1. 크롤링 된 모든 웹툰 리스트(제목, 썸네일) 출력 (self.webtoon -> title, img_url) # index.html

            with open('webtoon/index.html', 'wt') as f:
                # head 작성
                f.write(open('html/index_html_head.html', 'rt').read())
                # tr 작성
                for webtoon_title_id in webtoon_title_ids:
                    # 해당 웹툰을 객체화시키기
                    webtoon_instance = NaverWebtoonCrawler(webtoon_title_id=webtoon_title_id)
                    # print(webtoon_instance)
                    f.write(open('html/index_html_tr.html', 'rt').read().format(
                        episode_list_url=os.path.abspath(f'webtoon/{webtoon_title_id}.html'),
                        img_url=webtoon_instance.webtoon.img_url,
                        title=webtoon_instance.webtoon.title,
                    ))

                # tail 작성
                f.write(open('html/index_html_tail.html', 'rt').read())

        else:
            print('수집한 웹툰 목록이 존재하지 않습니다.')

        # from naver_crawler import NaverWebtoonCrawler
        # a = NaverWebtoonCralwer('694807')
        # NaverWebtoonCrawler.make_index_html()
        # Webtoon = namedtuple('Webtoon', ['title_id', 'img_url', 'title']) >> self.episode_list(thumbnail) >> {self.webtoon.title_id}_images




        if __name__ == '__main__':
            pass
