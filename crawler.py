import time
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import math


class Crawler:
    def __init__(self, grades=["G1"]):
        self.__home_url = "http://keirin.jp/pc/search"
        self.__grades = grades
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        self.__driver = webdriver.Chrome(options=options)
        self.__records = []
        self.__record = {}

    def gather(self, interval=2., timeout=math.inf, msg_flag=True):
        """
        Parameter
        ---------
        interval: float
            単位は秒. webページを切り替える際の間隔.
        timeout: float
            単位は秒. 関数実行時からtimeout秒経過すると、
            全てのコンテンツの回収が終わっていなくても終了する.
        """
        # START: 全グレードのデータ収集
        for grade in self.__grades:
            # 収集
            self.__record["grade"] = grade

            # 検索, 資料室へ遷移
            self.__driver.get(self.__home_url)
            self.__msg(msg_flag)
            time.sleep(interval)

            # レース検索結果へ遷移
            self.__go_list_of_races(grade)
            self.__msg(msg_flag)
            time.sleep(interval)

            # START: 1グレード分のデータを収集
            page_max = 10
            for page_idx in range(page_max):

                # START: ページに記載されている全レースのデータ収集
                tmp_refine = self.__driver.find_element_by_class_name("altertable")
                elem_trs = tmp_refine.find_elements_by_tag_name("tr")
                for elem_tr in elem_trs:
                    # START: 1レース分のデータを収集
                    # 収集
                    elem_tds = elem_tr.find_elements_by_tag_name("td")
                    self.__record["race_name"] = elem_tds[0].text
                    self.__record["region"] = elem_tds[1].text
                    self.__record["place"] = elem_tds[2].text
                    self.__record["start_date"] = elem_tds[3].text

                    # Live & 投票へ遷移

                    # 収集

                    # DONE: 1レース分のデータを収集

                # レース検索結果へ戻る
                # self.__driver.back()
                # self.__driver.back()

                # DONE: ページに記載されている全レースのデータ収集
                # 次ページへ遷移

            # DONE: 1グレード分のデータを収集
        # DONE: 全グレードのデータ収集

        self.__driver.quit()

    def __gather_all_grade_data(self):
        pass

    def __gather_one_grade_data(self):
        pass

    def __gather_all_race_data(self):
        pass

    def __gather_one_race_data(self):
        pass

    def __go_list_of_races(self, grade):
        value = self.__grade_key2value(grade)
        elem_drop_down = Select(self.__driver.find_element_by_id("UNQ_select_7"))
        elem_drop_down.select_by_value(value)
        elem_search = self.__driver.find_element_by_name("btnSearchRace")
        elem_search.click()

    def __go_live_and_vote(self):
        pass

    def __grade_key2value(self, key):
        mapping = {
            "GP": "6",
            "G1": "5",
            "G2": "4",
            "G3": "3",
            "F1": "2",
            "F2": "1",
            "レインボー": "AD1",
            "ルーキー": "AD2",
            "国際": "AD3",
            "F2(S級戦)": "AD4"
        }
        return mapping[key]

    def __msg(self, msg_flag):
        if msg_flag:
            print(self.__driver.title)


if __name__ == "__main__":
    crawler = Crawler(grade=["G1"])
    df_g1 = crawler.gather()
    df_g1.to_csv("./G1.csv")
