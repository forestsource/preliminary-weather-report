#!/usr/bin/env python
# -*- coding:utf-8 -*-

import urllib3
import datetime
import locale
import re
import json
import sqlite3
import time
from requests_oauthlib import OAuth1Session
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit


''' 
	Table 1
    CREATE TABLE Area (idx INTEGER auto_increment PRIMARY KEY,
        AreaCode INTEGER NOT NULL UNIQUE,
        AreaName TEXT NOT NULL UNIQUE,
        enable Bool default 0);
'''
''' 
	Table 2
    CREATE TABLE Rainfall (AreaCode INTEGER PRIMARY KEY,
    	Date TEXT NOT NULL,
        Now REAL NOT NULL,
        after5 REAL NOT NULL,
        after10 REAL NOT NULL,
        after15 REAL NOT NULL,
        after20 REAL NOT NULL,
        after25 REAL NOT NULL,
        after30 REAL NOT NULL,
        after35 REAL NOT NULL,
        after40 REAL NOT NULL,
        after45 REAL NOT NULL,
        after50 REAL NOT NULL,
        after55 REAL NOT NULL,
        after60 REAL NOT NULL);
'''
''' 
	Table 3
    CREATE TABLE Weather (AreaCode INTEGER PRIMARY KEY,
    	Date TEXT NOT NULL,
    	hour0 TEXT NOT NULL,
    	hour1 TEXT NOT NULL,
    	hour6 TEXT NOT NULL,
    	hour9 TEXT NOT NULL,
        hour12 TEXT NOT NULL,
        hour15 TEXT NOT NULL,
        hour18 TEXT NOT NULL,
        hour21 TEXT NOT NULL);
'''
def rainfall_json_parseDate(str):
	year = str[:4]
	month = str[4:6]
	day = str[6:8]
	hour = str[8:10]
	minutes = str[10:14]
	return (year + "年" + month + "月" + day + "日" + hour + "時" + minutes + "分")

def weather_url_parse(weatherurl):
	urls = weatherurl.split("/")
	return urls[6]

def weather_cmp(db_wethers,web_wethers):
	#weatherは switchで 今の時間>ポイントとなる時間の配列　を評価する。　そのポイント時間から後の天気を比較する
	#変更があったら変更後を返す
	#なかったら -1をかえす。
	nowtime = datetime.datetime.today().strftime("%H")
	hours = ["0","01","06","09","12","15","18","21"]
	for i,hour in enumerate(hours):
		if(nowtime < hours):
			break
	if(i>0):
		#リストの0,1番目は areacode,dataなので除外する
		print db_wethers
		del db_wethers[0:i+2] 
		del web_wethers[0:i+2]
		for i in len(db_wethers-1):
			if(db_wethers != web_wethers):
				return web_wethers[i]
		return -1

def rainfall_cmp(db_raingall,web_rainfall):
	#変更があったら変更後を返す
	#なかったら -1をかえす。
	del db_raingall[0] #nowは比べない
	for i in len(db_raingall):
		if(db_raingall[i] != web_wethers[i] ):
			return web_wethers[i]
	return -1

class DB:
	def __init__(self):
		self.Rainfall_old=[]
		self.DB = None
		self.AreaCode = 0
		self.Rainfall_exit = False
		self.weathers_exit = False
		dbfile = "/Users/HMT/sqlite3/wether_db"

	def connect(self):
		con = sqlite3.connect(dbfile)
		self.DB = con
		print "connect DB OK"

	def read_Area(self):
		c = self.DB.cursor()
		select_sql = "select * from Area where AreaCode=?"
		fact=[weather_url_parse()]
		c.execute(select_sql,fact)
		if(c):
			return c
		else:
			return -1
		print "read AreaDB OK"

	def read_Rainfall(self):
		c = self.DB.cursor()
		select_sql = "select * from Rainfall where AreaCode=? order by Date asc"
		fact=[weather_url_parse()]
		c.execute(select_sql,fact)
		data = c.fetchone()
		if(data):
			return data
		else:
			return -1
		print "read RainfallDB OK"

	def read_Weather(self):
		c = self.DB.cursor()
		select_sql = "select * from Weather where AreaCode=? order by Date asc"
		fact=[weather_url_parse(weatherurl)]
		c.execute(select_sql,fact)
		data = c.fetchone()
		print data  #None???????
		if(data):
			return data
		else:
			return -1
		print "read RainfallDB OK"

	def insert_weathers(self,weathers):
		c = self.DB.cursor()
		insert_sql = "insert into Weather values(?,?,?,?,?,?,?,?,?,?,?)"
		fact=[weathers[0],weathers[1],weathers[2],
			    weathers[3],weathers[4],weathers[5],weathers[6],weathers[7],weathers[8],weathers[9]]
		c.execute(insert_sql,fact)
		self.DB.commit()
		print "insert Weather"

	def update_weathers(self,weathers):
		c = self.DB.cursor()
		insert_sql = "update Weather set Date=?,hour0=?,hour1=?,hour6=?,hour9=?,hour12=?,hour15=?,hour18=?,hour21=?;"
		fact=[weathers[1],weathers[2],
			    weathers[3],weathers[4],weathers[5],weathers[6],weathers[7],weathers[8],weathers[9]]
		c.execute(insert_sql,fact)
		self.DB.commit()
		print "update Weather"

	def update_rainfall(self,rainfall):
		c = self.DB.cursor()
		insert_sql = "update Weather set Date=?,now=?,after5=?,after10=?,\
			after15=?,after20=?,after25=?,after30=?,after35=?,after40=?,\
			after45=?,after50=?,after55=?,after60=?;"
		fact=[rainfall[1],rainfall[2],rainfall[3],rainfall[4],rainfall[5],rainfall[6],rainfall[7],
			rainfall[8],rainfall[9],rainfall[10],rainfall[11],rainfall[12],rainfall[13],rainfall[14]]
		c.execute(insert_sql,fact)
		self.DB.commit()
		print "update Rainfall"

	def close(self):
		self.DB.close()
		print "close DB OK"



class Web:
	def __init__(self):
		self.weather_soup = BeautifulSoup(urllib3.PoolManager().request('GET',weatherurl).data)

	def get_rainfall(self):
		http = urllib3.PoolManager()
		r = http.request('GET', rainurl)
		jsonData = json.loads(r.data)
		rainfall = []
		if(200 == jsonData["ResultInfo"]["Status"]):
			rainfall.append( jsonData["Feature"][0]["Property"]["WeatherAreaCode"])
			rainfall.append( jsonData["Feature"][0]["Property"]["WeatherList"]["Weather"][0]["Date"])
			for i in xrange(0,13):
				rainfall.append( jsonData["Feature"][0]["Property"]["WeatherList"]["Weather"][i]["Rainfall"])
		return rainfall

	def get_weathers(self):
		weathers = []
		weathers.append(weather_url_parse(weatherurl))
		date = self.weather_soup.find("p",class_="yjSt yjw_note_h2")
		weathers.append(date.get_text())
		weather = self.weather_soup.find("table",class_="yjw_table2")#今日の天気のテーブルだけを取る
		weather = weather.find_all("small")#時間ごとの天気をすべて取る
		for i in xrange(10,18):
			weathers.append(weather[i].get_text())
		return weathers

	def get_causion(self):
		causion = self.weather_soup.find("dl",class_="warnAdv")
		causion = causion.find("dd")
		return causion.get_text()

		



if __name__ == "__main__":
	#######values#####
	weatherurl = "http://weather.yahoo.co.jp/weather/jp/14/4610/14135.html"
	jsonfile = "./json"
	dbfile = "./wether_db"
	
	r = open(apikey,"r")
	rainurl = r
	r.close()

	r = open(jsonfile,"r")
	jsonData = json.load(r)
	r.close()
	##################

	web = Web()
	db = DB()
	db.connect()
	w = weather_cmp(db.read_Weather(),web.get_weathers())
	r = rainfall_cmp(db.read_Rainfall(),web.get_rainfall())
	if(w != -1):
		db.update_weathers(w)
	if(r != -1):
		db.update_rainfall(r)

	db.close()

	'''
	db = DB()
	web = Web()
	db.connect()
	db.update_weathers(web.get_weathers())
	db.close()
	'''


	


'''
コマンドの結果を取る方法
import commands
myname = commands.getoutput('whoami')
print myname
'''

'''
terminal-notifier
-message "VALUE" 本文
-title "VALUE" 通知のタイトル デフォは Terminal
-group ID 消す時に使うidをつけれる
-remove ID  該当IDを消す。 ID=ALL だと全部消える
'''