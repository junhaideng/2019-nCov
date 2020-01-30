# coding:utf-8
# Author: Edgar

import requests
import os
import time
import re
from bs4 import BeautifulSoup
import pymysql
import json


class Virus(object):
    def __init__(self):
        super().__init__()
        self.url = "https://3g.dxy.cn/newh5/view/pneumonia"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36"}
        self._html = None
        self.home_html()

    def get_html(self, url) -> str:
        """获取网站的html"""
        with requests.session() as s:
            response = s.get(url, headers=self.header, timeout=5)
            response.encoding = response.apparent_encoding
            if response:
                return response.text

    def home_html(self):
        """将网页的内容存储起来，方便之后引用"""
        self._html = self.get_html(self.url)

    def get_picture(self):
        """获取网页中的部分疫情图"""
        flag = True
        print(self._html)
        pattern = re.compile(r'<img class="mapImg___3LuBG" src="(.*?)">', re.S)
        src = re.findall(pattern, self._html)

        if not src:  # 如果没有找到
            print("未查找到相关内容，请联系作者更新")
            return

        if not os.path.exists('疫情趋势图.png'):
            with open("疫情趋势图.png", "wb") as png:
                png.write(requests.get(src[0]).content)
        else:
            while flag:
                choice = input("原疫情趋势图已存在，是否覆盖: (y/n)  ")
                if choice in ["Y", "y"]:
                    with open("疫情趋势图.png", "wb") as png:
                        png.write(requests.get(src[0]).content)
                        flag = False
                elif choice in ["N", 'n']:
                    return
                else:
                    print("输入错误，请重新输入")

    def get_des(self) -> dict:
        """获取网页最开始的描述信息"""
        pattern = re.compile(r'<div class="mapTop___2VZCl">(.*?)</div>')
        des_div = re.findall(pattern, self._html)
        # print(des_div[0])
        soup = BeautifulSoup(des_div[0], 'lxml')
        p_list = soup.findAll('p')
        des_text_list = []
        for p in p_list:
            des_text_list.append(p.get_text())
        return {"description": des_text_list}

    def get_area_stat(self):
        """获取不同城市的状态"""
        pattern = re.compile(r'window.getAreaStat = (.*?)}catch')
        json_text = re.findall(pattern, self._html)[0]
        return json.loads(json_text)

    def upload_area_stat(self) -> None:
        """"将获取到的省份城市的信息存储在数据库中"""
        state = self.get_area_stat()
        for info in state:
            cities = info.popitem()
            self.insert_to_province(info)
            for city in cities[1]:
                city["provinceShortName"] = info.get("provinceShortName")
                self.insert_to_city(city)

    def get_broadcast(self) -> list:
        """"获取实时播报"""
        url = "https://assets.dxycdn.com/gitrepo/bbs-mobile/dist/p__Pneumonia__timeline.async.4363ba04.js"
        html = self.get_html(url)
        pattern = re.compile(r"JSON.parse\('(.*?)'\)}", re.M)
        json_text = re.findall(pattern, html)[0].encode('utf-8').decode(
            "unicode_escape")
        return json.loads(json_text)

    def get_left_broadcast(self) -> list:
        """获取首页中的播报内容"""
        pattern = re.compile(r"window.getTimelineService =(.*?)}catch")
        json_text = re.findall(pattern, self._html)[0]
        return json.loads(json_text)

    @staticmethod
    def get_all_id():
        """"获取之前存在数据库中所有的时间数据"""
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'edgar')
        cursor = connect.cursor()
        sql = "SELECT id FROM broadcast"
        cursor.execute(sql)
        result = cursor.fetchall()
        connect.commit()
        cursor.close()
        connect.close()
        return [i[0] for i in result]

    def check_latest(self) -> None:
        """"判断是否存在最新的消息,在这里假设的是处于不断的运行之中，
        所以只需要每次判断第一个便可以了"""
        new = [i for i in self.get_left_broadcast()][0]
        new_time = new.get("id")
        if new_time not in self.get_all_id():
            print("有新的实时播报")
            print("title: {}".format(new.get("title")))
            print("summary: {}".format(new.get("summary")))
            self.insert(new)

            print("\n目前 湖南，上海的情况如下：")
            hunan = self.get_city_detail("湖南")
            shanghai = self.get_city_detail("上海")
            print(hunan, shanghai, sep="\n")
        else:
            print("暂无最新消息")

    @staticmethod
    def create_database() -> None:
        """创建需要的数据库对象，使用的时候需要指定数据库，并且要先行创建"""
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'edgar')
        cursor = connect.cursor()
        sql = "CREATE TABLE IF NOT EXISTS broadcast(id INTEGER NOT NULL , " \
              "pubDate varchar(20) , title TEXT, summary TEXT, infoSource " \
              "varchar(40), sourceUrl TEXT, provinceId varchar(20), " \
              "provinceName varchar(20), createTime varchar(20), modifyTime " \
              "varchar(20)); "
        cursor.execute(sql)

        sql = "create table province(provinceName varchar(20)," \
              "provinceShortName varchar(20),confirmedCount INT," \
              "suspectedCount INTEGER, curedCount INTEGER," \
              "deadCount INTEGER,comment TEXT);"
        cursor.execute(sql)

        sql = "create table city(provinceShortName varchar(20),cityName " \
              "varchar(20),confirmedCount INTEGER,suspectedCount INT," \
              "curedCount INT,deadCount INTEGER); "
        cursor.execute(sql)

        connect.commit()
        cursor.close()
        connect.close()

    def insert(self, info) -> None:
        """"
        插入信息内容到数据库
        :info 字典类型
        """
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'edgar')
        cursor = connect.cursor()
        sql = 'INSERT INTO broadcast(id, pubDate, title, summary, infoSource, ' \
              'sourceUrl, provinceId, provinceName, createTime, modifyTime) ' \
              'VALUES("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")' % (
                  info.get("id"), self.convert_timestamp(info.get("pubDate")),
                  info.get("title"),
                  info.get("summary"),
                  info.get("infoSource"), info.get("sourceUrl"),
                  info.get("provinceId"),
                  info.get("provinceName"),
                  self.convert_timestamp(info.get('createTime')),
                  self.convert_timestamp(info.get("modifyTime")))
        # 需要加引号，否则can not通过
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()

    def upload_data(self) -> None:
        """批量上传信息到数据库中"""
        info = self.get_broadcast()
        for data in info[::-1]:
            self.insert(data)

    def upload_left_data(self) -> None:
        """"主页和实时播报页面的并没有同步,另外插入"""
        left_info = self.get_left_broadcast()
        id_list = self.get_all_id()
        for info in left_info[::-1]:
            if info.get("id") not in id_list:
                self.insert(info)

    @staticmethod
    def convert_timestamp(timestamp) -> str:
        """对时间戳进行转化"""
        timestamp = timestamp / 1000  # 这里是因为这个网站中的时间戳后面的三位是可以忽略的
        localtime = time.localtime(timestamp)
        date = time.strftime("%Y-%m-%d %H:%M:%S", localtime)
        return date

    def insert_to_province(self, info) -> None:
        """插入到province table中"""
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'edgar')
        cursor = connect.cursor()
        sql = 'INSERT INTO province(provinceName, provinceShortName, ' \
              'confirmedCount, suspectedCount,curedCount, deadCount, comment) ' \
              'VALUES("%s","%s","%s","%s","%s","%s", "%s")' % (
                  info.get("provinceName"),
                  info.get("provinceShortName"),
                  info.get("confirmedCount"),
                  info.get("suspectedCount"),
                  info.get("curedCount"),
                  info.get("deadCount"),
                  info.get("comment"))
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()

    def get_city_detail(self, city) -> str:
        """
        获取city的信息
        :city 城市名，需要满足一定的条件，需要数据库中的 shortName
        """
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'edgar')
        cursor = connect.cursor()
        sql = 'SELECT * FROM province where provinceShortName="%s"' % city
        cursor.execute(sql)
        result = cursor.fetchone()
        connect.commit()
        cursor.close()
        connect.close()
        result = "在%s 确诊的有 %d 人，疑似 %d 人，死亡 %d 人，成功治愈 %d 人" % (
            result[1], result[2], result[3], result[4], result[6])
        return result

    @staticmethod
    def insert_to_city(info):
        """
        插入信息到city table中
        :param info: 信息字典类型
        :return: None
        """
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'edgar')
        cursor = connect.cursor()
        sql = 'INSERT INTO city(provinceShortName, cityName, confirmedCount, ' \
              'suspectedCount, curedCount, deadCount) ' \
              'VALUES("%s","%s","%s","%s","%s","%s")' % (
                  info.get("provinceShortName"),
                  info.get("cityName"),
                  info.get("confirmedCount"),
                  info.get("suspectedCount"),
                  info.get("curedCount"),
                  info.get("deadCount"))
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()

    def refresh_province_city(self):
        """刷新对应的信息"""
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'edgar')
        cursor = connect.cursor()
        sql = 'truncate table city;'
        cursor.execute(sql)
        sql = 'truncate table province;'
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()
        self.upload_area_stat()

    def refresh_broadcast(self):
        """
        刷新播报的信息
        :return:  None
        """
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'edgar')
        cursor = connect.cursor()
        sql = 'truncate table broadcast'
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()
        self.upload_data()
        self.upload_left_data()


if __name__ == "__main__":
    virus = Virus()

    # virus.get_picture()

    # virus.create_database()

    # print(virus.get_des())

    # print(virus.get_area_stat())

    # virus.upload_area_stat()

    # print(virus.get_broadcast())

    # print(virus.get_left_broadcast())

    # print(virus.get_all_id())

    # virus.check_latest()

    virus.refresh_broadcast()

    # print(virus.get_city_detail("上海"))

    # virus.check_latest()

    virus.refresh_province_city()

    # virus.upload_data()
