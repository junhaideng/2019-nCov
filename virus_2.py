# -*- coding:utf-8 -*-
"""
Author: Edgar
Created time:1/30/2020 10:16 AM
"""
import os
import requests
import re
import json
import pymysql
from virus import Virus


class Virus2(Virus):
    def get_broadcast(self) -> list:
        """"
        获取实时播报的内容，目前URL如下，可自行查找
        注意：部分id并没有完全连续
        """
        url = "http://file1.dxycdn.com/2020/0127/794/3393185296027391740-115.json"
        try:
            response = requests.get(url, self.header)
            response.raise_for_status()
        except:
            print('获取失败，请检查网页链接是否能访问')
            return []
        else:
            response_json = response.json()
            if response_json.get("code") == 'success':
                return response.json().get("data")
            else:
                return []

    def get_left_broadcast(self) -> list:
        """"网页结构改变之后，实时播报和查看更多中的同步，故无需此步"""
        return []

    def get_picture(self):
        """直接由图片链接下载图片"""
        pattern = re.compile(r"window.getStatisticsService = (.*?)}catch")
        statistics = json.loads(re.findall(pattern, self._html)[0])
        url = statistics.get("dailyPic")
        response = requests.get(url, self.header)
        flag = True
        try:
            response.raise_for_status()
        except:
            print("下载失败")
        else:
            if not os.path.exists('疫情趋势图.png'):
                with open("疫情趋势图.png", "wb") as png:
                    png.write(response.content)
            else:
                while flag:
                    choice = input("原疫情趋势图已存在，是否覆盖: (y/n)  ")
                    if choice in ["Y", "y"]:
                        with open("疫情趋势图.png", "wb") as png:
                            png.write(response.content)
                            flag = False
                    elif choice in ["N", 'n']:
                        return
                    else:
                        print("输入错误，请重新输入")

    def get_foreign_city(self):
        """获取其他国家的信息, 但是注意插入的是province table中"""
        pattern = re.compile("window.getListByCountryTypeService2 =(.*?)}catch")
        foreign = json.loads(re.findall(pattern, self._html)[0])
        for info in foreign:
            self.insert_to_province(info)


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
        self.get_foreign_city()

    def get_des(self) -> dict:
        pattern = re.compile("window.getStatisticsService = (.*?)}catch")
        des = json.loads(re.findall(pattern, self._html)[0])
        return des

if __name__ == '__main__':
    virus = Virus2()
    # virus.get_picture()
    # virus.refresh_broadcast()
    # virus.refresh_province_city()
    # virus.get_foreign_city()
    print(virus.get_des())

