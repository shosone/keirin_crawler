import time
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup


class Crawler:
    def __init__(self, grade, interval=2):
        """
        Parameters
        ----------
        grade: str
            収集するグレード
        interval: float
            urlを遷移する時にsleepする秒数
        """
        self.grade = grade
        self.interval = interval

        # chromeをGUIで開かずに動かすためのオプション
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')

        self.__driver = webdriver.Chrome(options=options)
        self.__haraimodoshi_records = []
        self.__chaku_records = []

    def gather(self):
        """
        収集を実施する.

        Return
        ------
        (dict, dict).
        収集結果.
        添字0番目の値は払い戻しデータ.
        添字1番目の値は着順データ.
        """
        # 検索・資料質に移動
        self.__driver.get("http://keirin.jp/pc/search")

        # データ収集
        page_idx = 1
        while self.__go_race_list(self.grade, page_idx):
            record_idx = 0
            while self.__go_program_list(record_idx):
                program_idx = 0
                while self.__go_program(program_idx):
                    soup = BeautifulSoup(self.__driver.page_source, "html5lib")
                    self.__parse_soup(soup)
                    self.__back()
                    program_idx += 1
                self.__back()
                record_idx += 1
            self.__back()
            page_idx += 1

        # driverを終了する
        self.__driver.quit()

        return (self.__haraimodoshi_records, self.__chaku_records)

    def __parse_soup(self, soup):
        """
        htmlからレコードを取り出す.

        Parameters
        ----------
        soup: bs4.BeautifulSoup
            Live&投票ページのスープ
        """
        # このページで収集する全レコードに共通の情報を収集
        race_name = soup.find(id="hhLblRaceName").text
        place = soup.find(id="hhLblJo").text
        date = soup.find("li", class_="active").text
        r = soup.find("button", {"class": "active", "name": "hhRaceBtn"}).text

        # 払い戻し情報を取得
        soup_harai1 = soup.find(id="rrDispHaraiGaku")
        soup_harai2 = soup.find(id="rrDispHaraiGaku2")
        soup_harai1_nbls = soup_harai1.find_all(class_="nb-l")
        soup_harai2_nbls = soup_harai2.find_all(class_="nb-l")
        haraimodoshi_record = {}
        haraimodoshi_record["レース名"] = race_name
        haraimodoshi_record["払戻金_2枠複"] = soup_harai1_nbls[0].text
        haraimodoshi_record["払戻金_3連複"] = soup_harai1_nbls[1].text
        haraimodoshi_record["払戻金_2枠単"] = soup_harai1_nbls[2].text
        haraimodoshi_record["払戻金_3連単"] = soup_harai1_nbls[3].text
        haraimodoshi_record["払戻金_2車複"] = soup_harai2_nbls[0].text
        haraimodoshi_record["払戻金_ワイド"] = soup_harai2_nbls[1].text
        haraimodoshi_record["払戻金_2車単"] = soup_harai2_nbls[2].text
        self.__haraimodoshi_records.append(haraimodoshi_record)

        # 着順情報を取得
        soup_ht_32s = soup.find_all(class_=" ht_32")
        for soup_ht_32 in soup_ht_32s:
            chaku_record = {}
            chaku_record["レース名"] = race_name
            chaku_record["競輪場"] = place
            chaku_record["開催日"] = date
            chaku_record["r"] = r
            chaku_record["着"] = soup_ht_32.find(class_="wakuban").text
            chaku_record["車番"] = soup_ht_32.find(class_="al-c").text
            chaku_record["選手名"] = soup_ht_32.find(class_="al-l pd_l5").text
            # chaku_record["年齢"] = soup_ht_32.find_all(class_="al-c")[1].text
            # chaku_record["府県"] = soup_ht_32.find_all(class_="al-c")[2].text
            # chaku_record["期別"] = soup_ht_32.find_all(class_="al-c")[3].text
            # chaku_record["級班"] = soup_ht_32.find_all(class_="al-c")[4].text
            # chaku_record["着差"] = soup_ht_32.find_all(class_="al-c")[5].text
            # chaku_record["上り"] = soup_ht_32.find_all(class_="al-c")[6].text
            chaku_record["決まり手"] = soup_ht_32.find_all(class_="al-c")[7].text
            # chaku_record["HB"] = soup_ht_32.find_all(class_="al-c")[8].text
            # chaku_record["個人状況"] = soup_ht_32.find_all(class_="al-l")[9].text
            self.__chaku_records.append(chaku_record)

    def __go_race_list(self, grade, idx):
        """
        レース検索結果のページにジャンプする.

        Parameters
        ----------
        grade: str
            収集対象のグレード
        idx: int
            ページ番号
        """
        # ページ番号が1の時は初めてレース検索結果にジャンプする時なので、検索/資料室からのジャンプになる. 
        # それ以外の場合はレース検索結果から次のページへボタンを押してのジャンプになる.
        if idx == 1:
            value = self.__grade_key2value(grade)
            elem_drop_down = Select(self.__driver.find_element_by_id("UNQ_select_7"))
            # グレードを選択
            elem_drop_down.select_by_value(value)
            elem_search = self.__driver.find_element_by_name("btnSearchRace")
            # ブラウザ上にボタンが見えていないとクリックできないのでスクロールする
            self.__driver.execute_script("scroll(0, 0);")
            self.__driver.execute_script('arguments[0].scrollIntoView(true);', elem_search)
            # 検索ボタンを押す
            elem_search.click()
        else:
            try:
                next_page_idx = 1 if idx == 2 else 2
                a_elem = self.__driver\
                    .find_element_by_class_name("al-l")\
                    .find_elements_by_tag_name("a")[next_page_idx]
                # ブラウザ上にボタンが見えていないとクリックできないのでスクロールする
                self.__driver.execute_script("scroll(0, 0);")
                self.__driver.execute_script('arguments[0].scrollIntoView(true);', a_elem)
                # 次のページへをクリックする
                a_elem.click()
            except:
                # ページの上限に達した場合はここにくる
                return False

        print(self.__driver.title + " ({})".format(idx))
        time.sleep(self.interval)
        return True

    def __go_program_list(self, idx):
        """
        idxで指定されたレースプログラム一覧のページにジャンプする.

        Parameters
        ----------
        idx: int
            開いているレース検索結果ページに表示されているテーブルの行番号
        """
        try:
            tr_elems = self.__driver\
                .find_element_by_class_name("altertable")\
                .find_elements_by_tag_name("tr")
            target_tr_elem = tr_elems[idx]
            a_elem = target_tr_elem.find_element_by_tag_name("a")
            # ブラウザ上にボタンが見えていないとクリックできないのでスクロールする
            self.__driver.execute_script("scroll(0, 0);")
            self.__driver.execute_script('arguments[0].scrollIntoView(true);', a_elem)
            # 遷移先のレース名をクリックする
            a_elem.click()
        except:
            # テーブルの行番号の上限に達した場合はここにくる
            return False

        print(self.__driver.title + " ({})".format(idx))
        time.sleep(self.interval)
        return True

    def __go_program(self, idx):
        """
        idxで指定されたLive&投票のページにジャンプする

        Parameters
        ----------
        idx: int
            開いているレースプログラム一覧ページに表示されいているレースの番号.
            n日目のレース番号にはn-1日目のレース数が加算される.
        """
        tmp_idx = idx
        mardiv_elems = self.__driver.find_elements_by_class_name("mardivtop")[1:]
        for mardiv_elem in mardiv_elems:
            a_elems = mardiv_elem\
                .find_element_by_class_name("tbl_header")\
                .find_elements_by_tag_name("a")
            if tmp_idx < len(a_elems):
                # ブラウザ上にボタンが見えていないとクリックできないのでスクロールする
                self.__driver.execute_script("scroll(0, 0);")
                self.__driver.execute_script('arguments[0].scrollIntoView(true);', a_elems[tmp_idx])
                # ?Rとなっている部分をクリックする
                a_elems[tmp_idx].click()
                print(self.__driver.title + " ({})".format(idx))
                time.sleep(self.interval)
                return True
            else:
                # 例えば初日が11Rまであったとして、idxに11が指定されたのなら、idxは0になるので2日目の1Rが選択される
                tmp_idx -= len(a_elems)

        # 未収集のレースがあるならここに来ることはない
        return False

    def __back(self):
        """
        ブラウザの戻るボタンを押す
        """
        self.__driver.back()
        time.sleep(self.interval)

    def __grade_key2value(self, key):
        """
        グレード名をhtml上のプルダウンボタンの値に変換する

        Parameters
        ----------
        key: str
            グレード名

        Return
        ------
        str. html上のプルダウンボタンの値
        """
        return {
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
        }[key]


if __name__ == "__main__":
    import pandas as pd

    crawler = Crawler("G1")
    haraimodoshi, chakujun = crawler.gather()

    pd.DataFrame(haraimodoshi).to_csv("./G1_haraimodoshi.csv")
    pd.DataFrame(chakujun).to_csv("./G1_chakujun.csv")
