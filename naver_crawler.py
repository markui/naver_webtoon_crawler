import os
import utils
import pickle


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

    def __init__(self, webtoon_id):
        """
        초기화 메서드
        웹툰 아이디를 저장 / 빈 리스트를 할당
        :param webtoon_id:
        """
        self.webtoon_id = webtoon_id
        self.episode_list = list()
        # 객체 생성 시 'db/{webtoon_id}.txt'파일이 존재하면
        # 바로 load() 해오도록 작성
        self.load(init=True)

    def get_last_page_episode(self, page):
        """
        해당 페이지 에피소드 리스트를 가져오s는, dummy function
        :param page:
        :return:
        """
        self.episode_list = utils.get_page_episode_list(self.webtoon_id, page)

    def get_page_episode_list(self, page=1):
        """
        특정 페이지의 에피소드들을 namedtuple로 정렬된 리스트를 가져온다 (최신화부터 내림차순으로)
        :param page:
        :return: 해당 페이지의 에피소드 리스트
        """
        return utils.get_page_episode_list(self.webtoon_id, page)

    def get_all_episode_list(self, page=1):
        """
        특정 페이지부터 끝까지 모든 에피소드들을 namedtuple로 정렬된 리스트를 가져온다; 인자가 없다면 처음부터~끝 에피소드까지 가져온다 (최신화부터 내림차순으로)
        :param page:
        :return:
        """
        self.episode_list = list()  # 기존에 있던 에피소드들 삭제하고 빈 리스트 할당
        while True:
            page_webtoon_list = utils.get_page_episode_list(self.webtoon_id, page)  # 처음 start 페이지 게시물들 가져오기
            self.episode_list.extend(page_webtoon_list)  # 기존 리스트에 가져온 해당 페이지 에피소드 리스트 추가하기
            if page_webtoon_list[-1].no == '1':  # 만약에 가져왔던 페이지의 에피소드 리스트의 마지막 게시물이 첫번째 게시물이면
                break  # 추출 종료
            page += 1  # 페이지 수 증가시키기

        return self.episode_list

    @property
    def total_episode_count(self):
        """
        webtoon_id에 해당하는 실제 웹툰의 총 episode수를 리턴
        :return: 총 episode수 (int)
        """
        page_1_webtoon_list = utils.get_page_episode_list(self.webtoon_id)  # 1 페이지의 에피소드 리스트를 가져옴
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
            os.mkdirs('db')

        # 2. 저장시
        obj = self.episode_list
        path = 'db/{}.txt'.format(self.webtoon_id)
        pickle.dump(obj, open(path, 'wb')) # open() 참조되는 값이 없어서 (변수) 저절로 닫힘!

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
            path = f'db/{self.webtoon_id}.txt'
            self.episode_list = pickle.load(open(path, 'rb'))
        except FileNotFoundError: # error써주는 게 규약에 맞음
            if not init:
                print('파일이 없습니다.')




if __name__ == '__main__':
    firstmission_crawler = NaverWebtoonCrawler(696617)
    firstmission_crawler.get_all_episode_list()
    print(firstmission_crawler.update_episode_list())
