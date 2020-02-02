# -*- coding:utf-8 -*-
"""
Author: Edgar
Created time:2/1/2020 12:06 PM
爬取新浪微博中的相关信息
"""
import os
import json
import requests
import pymysql


class Virus(object):
    def __init__(self):
        super(Virus, self).__init__()
        self.url = "https://interface.sina.cn/news/wap/fymap2020_data.d.json"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36"}

    def get_json(self):
        """获取加载出来的json"""
        response = requests.get(self.url, self.header)
        try:
            response.raise_for_status()
        except:
            print("获取json文件失败")
        else:
            return response.json()

    def download_json(self, filename='data.json'):
        """下载json文件"""
        flag = True
        json_ = self.get_json()
        print(json_)

        if not os.path.exists(filename):
            with open(filename, "w") as file:
                json.dump(json_, file)
        else:
            while flag:
                answer = input("该目录已经存在文件 %s，是否删除该文件(y/n):  " % filename)
                if answer in ['y', 'Y']:
                    with open(filename, 'w') as file:
                        json.dump(json_, file)
                    flag = False
                elif answer in ['n', 'N']:
                    return
                else:
                    print("输入错误，请重新输入: ")

    @staticmethod
    def create_table():
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'virus')
        cursor = connect.cursor()
        # 创建一个表来保存每个省市的信息
        sql = "CREATE TABLE IF NOT EXISTS Virus_province(name VARCHAR(60) NOT NULL, ename varchar(20), value varchar(20), susNum varchar(20), deathNum varchar(20), cureNum varchar(20), city TEXT)"
        cursor.execute(sql)
        # 创建一个表来保存所有相关城市的相关信息
        sql = "CREATE TABLE IF NOT EXISTS Virus_city(province VARCHAR(20),name VARCHAR(20) NOT NULL ,conNum VARCHAR(20), susNum VARCHAR(20), cureNum VARCHAR(20), deathNum VARCHAR(20))"
        cursor.execute(sql)
        # 保存全球疫情信息
        sql = "CREATE TABLE IF NOT EXISTS Virus_world(name VARCHAR(20), value VARCHAR(20), susNum VARCHAR(20), deathNum VARCHAR(20), cureNum VARCHAR(20))"
        cursor.execute(sql)
        sql = "CREATE TABLE IF NOT EXISTS Virus_timeline(url varchar(100), title varchar(200), media varchar(40), date varchar(30));"
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()

    @staticmethod
    def insert_city(city):
        connect = pymysql.connect("localhost", 'root', "Edgar", 'virus')
        cursor = connect.cursor()
        sql = 'INSERT INTO virus_city(province,name, conNum, susNum, cureNum, deathNum) VALUES ("%s", "%s", "%s","%s","%s", "%s")' % (
            city.get("province"),
            city.get("name"),
            city.get("conNum"),
            city.get("susNum"),
            city.get("cureNum"),
            city.get("deathNum"))
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()

    @staticmethod
    def insert_province(province):
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'virus')
        cursor = connect.cursor()
        sql = 'INSERT INTO virus_province(name, ename, value, susNum, deathNum, cureNum, city) VALUES("%s","%s","%s","%s","%s","%s","%s")' % (
            province.get("name"),
            province.get("ename"),
            province.get("value"),
            province.get("susNum"),
            province.get("deathNum"),
            province.get("cureNum"),
            ",".join([i.get("name") for i in province.get("city")])
        )
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()

    @staticmethod
    def insert_world(world):
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'virus')
        cursor = connect.cursor()
        sql = 'INSERT INTO virus_world(name, value, susNum, deathNum, cureNum) VALUES ("%s","%s","%s","%s","%s")' % (
            world.get("name"), world.get("value"), world.get("susNum"),
            world.get("deathNum"), world.get("cureNum"))
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()

    @staticmethod
    def insert_timeline(data):
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'virus')
        cursor = connect.cursor()
        sql = "INSERT INTO virus_timeline(url, title, media, date) VALUES('%s','%s','%s','%s')" % (
            data.get("url"), data.get("title"), data.get("media"),
            data.get("date"))
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()

    def upload_data(self):
        data_json = self.get_json()
        data = data_json.get("data").get("list")
        for i in data:
            self.insert_province(i)
            for city in i.get("city"):
                city["province"] = i.get("name")
                self.insert_city(city)

        for world in data_json.get("data").get("worldlist"):
            self.insert_world(world)
        self.get_timeline()

    def refresh_data(self):
        connect = pymysql.connect("localhost", 'root', 'Edgar', 'virus')
        cursor = connect.cursor()
        sql = 'TRUNCATE TABLE virus_province;'
        cursor.execute(sql)
        sql = "TRUNCATE TABLE virus_city;"
        cursor.execute(sql)
        sql = "TRUNCATE TABLE virus_world;"
        cursor.execute(sql)
        sql = "TRUNCATE TABLE virus_timeline;"
        cursor.execute(sql)
        connect.commit()
        cursor.close()
        connect.close()
        self.upload_data()

    def get_timeline(self):
        """获取timeline中的信息"""
        url = "https://interface.sina.cn/wap_api/wap_std_subject_feed_list.d.json?component_id=_conf_13|wap_zt_std_theme_timeline|http://news.sina.cn/zt_d/yiqing0121&page={}"
        count = 0
        while True:
            response = requests.get(url.format(count), headers=self.header)
            try:
                response.raise_for_status()
            except:
                return
            else:
                data = response.json().get("result").get("data").get("data")
                if data:
                    count += 1
                    for i in data:
                        self.insert_timeline(i)
                else:
                    return


if __name__ == '__main__':
    virus = Virus()
    # virus.create_table()
    # virus.download_json()

    # virus.upload_data()
    virus.refresh_data()
    # virus.get_timeline()
