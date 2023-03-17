# -*- coding: utf-8 -*-

import sys
import urllib.request
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
from konlpy.tag import Okt
from PIL import Image

import numpy as np
from PyQt5 import uic
import datetime as dt
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
import matplotlib.ticker as ticker
from datetime import datetime
from IPython.display import display
from mplfinance.original_flavor import candlestick2_ohlc

import re
import pymysql
import os.path  

# QT Desinger로 작성한 ui 파일 불러오기
form_mainclass = uic.loadUiType("C:/Users/Mgyu/PL/financial/qt_design/main_window.ui")[0]
form_secondclass = uic.loadUiType("C:/Users/Mgyu/PL/financial/qt_design/second_window.ui")[0]

# 첫화면(메인화면) Class
class WindowClass(QMainWindow, form_mainclass):
    def __init__(self): # 생성자 - 해당 클래스 생성시 실행되는 함수
        super().__init__()
        self.setupUi(self) # QT Designer에서 만든 UI를 불러옴
        
        global today_date # 오늘 날짜 변수를 전역변수(해당 함수 밖에서도 사용가능한 변수)로 지정
        today_date = self.get_today().date() # 오늘 날짜를 구함(연_월_일)
        
        global now_hour #  현재 시간 변수를 전역변수로 지정
        now_hour = self.get_today().hour
        
        # 오늘 만들어진 워드클라우드 파일이 있으면, 다시 크롤링 실행하지 않음
        file = f"news_wordcloud_{today_date}_{now_hour}.png"
        if os.path.exists(file) == False: # 현재 시간에 해당하는 파일이 없으면
            self.wordCloud() # 크롤링하여 워드클라우드 만듬
            
        self.loadImageFromFile() # 워드클라우드 파일을 UI에 보여줌
        
        self.make_top_chart() # top 차트를 UI에 보여줌
        
        # UI 상 글자 관련(폰트, 글씨 크기 등) 함수
        self.label_crawl_day.setFont(QFont("", 9))
        self.label_crawl_day.setText(f"기준 일시 : {today_date}-{now_hour}시 ")
        
    def wordCloud(self): # 워드클라우드 생성 함수
        url = 'https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258' # 크롤링 대상 주소
        page = 0 # 크롤링하는 페이지
        news_titles = [] # 크롤링 한 기사 제목을 담을 리스트
        
        while True: # 오늘 기사 크롤링
            page += 1
            params = { 'page' : page }
            resp = requests.get(url, params)
            html = BeautifulSoup(resp.content, 'lxml')
            # articleSubject의 a 태그에 title이 존재
            titles_html = html.select('.articleSubject > a ')
            
            if len(titles_html) != 0:
                print(page, '페이지 크롤링 시작')
                for i in range(len(titles_html)):
                    # 기사 제목에 대괄호([,])가 포함된 부분을 제거
                    crawled_title = titles_html[i].text
                    pattern = '\[[^)]*\]'
                    crawled_title = re.sub(pattern=pattern, repl='', string= crawled_title)
                    crawled_title = ' '.join(crawled_title.split())
                    news_titles.append(crawled_title)
                    print(i+1, crawled_title)
                print(page, '페이지 크롤링 완료', '\n')
                
            else :
                print('\n \n',page-1, '이 마지막 페이지 입니다.')
                print(len(news_titles))
                break
            
        if len(news_titles) < 150: # 총 기사 개수가 부족하다면 어제 기사 최신순으로 가져옴.(150개는 임의로 설정)
            url = f"https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258&date={str(today_date-dt.timedelta(1)).replace('-', '')}"
            page_yesterday = 0 # 크롤링하는 페이지
            
            while True:
                page_yesterday += 1
                params = { 'page' : page_yesterday }
                resp = requests.get(url, params)
                html = BeautifulSoup(resp.content, 'lxml')
                # articleSubject의 a 태그에 title이 존재
                titles_html = html.select('.articleSubject > a ')
               
                if len(news_titles) < 150:
                    print('어제의', page_yesterday, '페이지 크롤링 시작')
                    for i in range(len(titles_html)):
                        # 기사 제목에 대괄호([,])가 포함된 부분을 제거
                        crawled_title = titles_html[i].text
                        pattern = '\[[^)]*\]'
                        crawled_title = re.sub(pattern=pattern, repl='', string= crawled_title)
                        crawled_title = ' '.join(crawled_title.split())
                        news_titles.append(crawled_title)
                        print(i+1, crawled_title)
                    print('어제의', page_yesterday, '페이지 크롤링 완료', '\n')
                    print('총 크롤링한 기사 개수:', len(news_titles))
                else :
                    print('일정 개수가 채워졌습니다. 크롤링을 중단합니다.')
                    break
            
        with open('news_titles.txt','w',encoding='UTF-8') as f:
            for title in news_titles:
                f.write(title+'\n')
        with open('news_titles.txt', 'r', encoding='utf-8') as f:
            text = f.read()
        
        okt = Okt()
        nouns = okt.nouns(text) # 명사만 추출
        
        # 특정 단어 제거
        words = [n for n in nouns if len(n) > 1] # 단어의 길이가 1개인 것은 제외
        words = [n for n in nouns if len(n) > 1 and n !='코스피' and n != '주간' and n != '코스닥']
        c = Counter(words) # 위에서 얻은 words를 처리하여 단어별 빈도수 형태의 딕셔너리 데이터를 구함
        
        # 워드 클라우드 옵션 설정
        wc = WordCloud(font_path='malgun', background_color='white', colormap = 'copper',
                       width=400, height=200, max_font_size=100)
        # wc = WordCloud(font_path='malgun', background_color='white', colormap = 'Spectral',
        #                width=400, height=200, max_font_size=100)
        gen = wc.generate_from_frequencies(c)
        plt.figure()
        plt.imshow(gen)
        wc.to_file(f"news_wordcloud_{today_date}_{now_hour}.png") # 워드클라우드 파일을 저장

    def loadImageFromFile(self): # 워드클라우드 시각화 함수
        #QPixmap 객체 생성 후 이미지 파일을 이용하여 QPixmap에 사진 데이터 Load하고, Label을 이용하여 화면에 표시
        pixmap_word = QPixmap(f"news_wordcloud_{today_date}_{now_hour}.png")
        self.label_word_cloud.setPixmap(QPixmap(pixmap_word))
        self.show()
        
    def get_today(self): # 오늘 날짜를 반환하는 함수 (연_월_일 형태)
        today = dt.datetime.now()
        return today
    
    def btn_main_to_second(self): # 결과를 보여주는 창으로 넘어가는 함수
    #('검색'버튼을 누르면 실행 - 이는 QT Designer에서 구현함)
        self.search_space.clear()
        # 검색 가능한 종목 리스트 초기화
        stock_list = ['삼성전자', '삼성바이오로직스', '현대차', 'KB금융', 'SK', 'POSCO홀딩스', 'SK이노베이션', '한국전력', 'KT', 'CJ제일제당']
        if search_word not in stock_list:
            print('no')
            self.search_space.setText(' 종목명을 정학하게 입력해주세요.')
        else: 
            self.hide()                     # 메인윈도우 숨김
            self.second = secondWindowClass()    
            self.second.exec()              # 두번째 창을 닫을 때 까지 기다림
            self.search_space.clear()
            self.show()                     # 두번째 창을 닫으면 다시 첫 번째 창이 보여짐
        
    def search_stock(self): # 검색창에 입력한 종목명 반환하는 함수
        global search_word
        search_word = self.search_space.text()
        print(search_word)

        return search_word
    
    def make_top_chart(self): # 상위 탑 종목 얻는 함수 (현재는 5개를 보여줌)

        # 거래량 순위 표 작성    
        URL = f"https://finance.naver.com/sise/sise_quant.naver" # 거래량 순 정렬되어 있는 네이버 금융 주소
        
        r = requests.get(URL) # 해당 주소에서 정보 읽어옴
        vol_df = pd.read_html(r.text,  encoding = 'utf-8')[1] # 거래량 순위 표를 dataFrame으로 만듬
        
        # 거래량 순위 데이터 프레임에서 종목명이 nan 값인 행 삭제
        na_index = vol_df[vol_df['종목명'].isna()].index 
        vol_df.drop(na_index,axis=0, inplace=True) 
        
        # 현재가, 전일비 값을 정수형으로 변경후, UI의 표의 내용으로 들어가기 위해 str형으로 변환
        vol_df['현재가'] = vol_df['현재가'].astype(int)
        vol_df['현재가'] = vol_df['현재가'].apply(lambda x: "{:,}".format(x))
        vol_df['현재가'] = vol_df['현재가'].astype(str)
        vol_df['전일비'] = vol_df['전일비'].astype(int)
        vol_df['전일비'] = vol_df['전일비'].apply(lambda x: "{:,}".format(x))
        vol_df['전일비'] = vol_df['전일비'].astype(str)
        vol_df['거래량'] = vol_df['거래량'].astype(int)
        vol_df['거래량'] = vol_df['거래량'].apply(lambda x: "{:,}".format(x))
        vol_df['거래량'] = vol_df['거래량'].astype(str)
        
        # 전일비에 +, - 표시 추가
        vol_df['전일비'] = vol_df['등락률'].str[0] + vol_df['전일비']
        
        # 현재 내용 길이에 맞춰, 셀 크기 조정
        self.volumnTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.volumnTable.resizeColumnsToContents()
        
        # 표에 셀 별로 내용 삽입
        for i in range(5): # 5개의 행 - 상위 5개 종목
            for j in range(5): # 5개의 열 - 종목명, 현재가, 전일비, 등락률, 거래량
            
                # 전일비가 0인 경우 -로 표시
                if j == 2 and vol_df.iloc[i,j+1] == '00':
                    self.volumnTable.setItem(i, j, QTableWidgetItem('-'))
                else:
                    self.volumnTable.setItem(i, j, QTableWidgetItem(vol_df.iloc[i,j+1]))
                
                # 등락률의 양수면 붉은 색, 음수면 푸른 색으로 전일비, 등락률의 글 색상 변경    
                if j == 3 and vol_df.iloc[i,j+1][0] == '+':
                    self.volumnTable.item(i, j).setForeground(QBrush(Qt.red))
                    self.volumnTable.item(i, j-1).setForeground(QBrush(Qt.red))
                elif j == 3 and vol_df.iloc[i,j+1][0] == '-':
                    self.volumnTable.item(i, j).setForeground(QBrush(Qt.blue))
                    self.volumnTable.item(i, j-1).setForeground(QBrush(Qt.blue))
                    
                # 종목명을 제외한, 나머지 열의 내용을 가운데 정렬로 표현
                if j != 0:    
                    self.volumnTable.item(i, j).setTextAlignment(Qt.AlignCenter)
                    
        # UI 내에서 내용변경등의 조작 불가 설정
        self.volumnTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 상승률 순위 표 작성 (위 거래량 순위 표와 코드 동일)
        URL = f"https://finance.naver.com/sise/sise_rise.naver"
        
        r = requests.get(URL)
        rise_df = pd.read_html(r.text,  encoding = 'utf-8')[1]
        # 거래량 순위 데이터 프레임에서 종목명이 nan 값인 행 삭제
        na_index = rise_df[rise_df['종목명'].isna()].index
        rise_df.drop(na_index,axis=0, inplace=True)
        rise_df['현재가'] = rise_df['현재가'].astype(int)
        rise_df['현재가'] = rise_df['현재가'].apply(lambda x: "{:,}".format(x))
        rise_df['현재가'] = rise_df['현재가'].astype(str)
        rise_df['전일비'] = rise_df['전일비'].astype(int)
        rise_df['전일비'] = rise_df['전일비'].apply(lambda x: "{:,}".format(x))
        rise_df['전일비'] = rise_df['전일비'].astype(str)
        rise_df['전일비'] = rise_df['등락률'].str[0] + rise_df['전일비']
        
        self.upTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.upTable.resizeColumnsToContents()
        
        for i in range(5):
            for j in range(4):
                if j == 2 and rise_df.iloc[i,j+1] == '00':
                    self.upTable.setItem(i, j, QTableWidgetItem('-'))
                else:
                    self.upTable.setItem(i, j, QTableWidgetItem(rise_df.iloc[i,j+1]))
                    
                if j == 3 and rise_df.iloc[i,j+1][0] == '+':
                    self.upTable.item(i, j).setForeground(QBrush(Qt.red))
                    self.upTable.item(i, j-1).setForeground(QBrush(Qt.red))
                elif j == 3 and rise_df.iloc[i,j+1][0] == '-':
                    self.upTable.item(i, j).setForeground(QBrush(Qt.blue))
                    self.upTable.item(i, j-1).setForeground(QBrush(Qt.blue))
                
                if j != 0:    
                    self.upTable.item(i, j).setTextAlignment(Qt.AlignCenter)

        self.upTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 하락률 순위 표 작성 (위 거래량 순위 표와 코드 동일)
        URL = f"https://finance.naver.com/sise/sise_fall.naver"
        
        r = requests.get(URL)
        fall_df = pd.read_html(r.text,  encoding = 'utf-8')[1]


        na_index = fall_df[fall_df['종목명'].isna()].index
        fall_df.drop(na_index,axis=0, inplace=True)
        fall_df['현재가'] = fall_df['현재가'].astype(int)
        fall_df['현재가'] = fall_df['현재가'].apply(lambda x: "{:,}".format(x))
        fall_df['현재가'] = fall_df['현재가'].astype(str)
        fall_df['전일비'] = fall_df['전일비'].astype(int)
        fall_df['전일비'] = fall_df['전일비'].apply(lambda x: "{:,}".format(x))
        fall_df['전일비'] = fall_df['전일비'].astype(str)
        fall_df['전일비'] = fall_df['등락률'].str[0] + fall_df['전일비']
        
        self.downTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.downTable.resizeColumnsToContents()
        
        for i in range(5):
            for j in range(4):
                if j == 2 and fall_df.iloc[i,j+1] == '00':
                    self.downTable.setItem(i, j, QTableWidgetItem('-'))
                else:
                    self.downTable.setItem(i, j, QTableWidgetItem(fall_df.iloc[i,j+1]))
                    
                if j == 3 and fall_df.iloc[i,j+1][0] == '+':
                    self.downTable.item(i, j).setForeground(QBrush(Qt.red))
                    self.downTable.item(i, j-1).setForeground(QBrush(Qt.red))
                elif j == 3 and fall_df.iloc[i,j+1][0] == '-':
                    self.downTable.item(i, j).setForeground(QBrush(Qt.blue))
                    self.downTable.item(i, j-1).setForeground(QBrush(Qt.blue))
                
                if j != 0:    
                    self.downTable.item(i, j).setTextAlignment(Qt.AlignCenter)

        self.downTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 시가총액 순위 표 작성 (위 거래량 순위 표와 코드 동일) 
        URL = f"https://finance.naver.com/sise/sise_market_sum.naver"
        
        r = requests.get(URL)
        total_df = pd.read_html(r.text,  encoding = 'utf-8')[1]

        na_index = total_df[total_df['종목명'].isna()].index
        total_df.drop(na_index,axis=0, inplace=True)
        total_df['현재가'] = total_df['현재가'].astype(int)
        total_df['현재가'] = total_df['현재가'].apply(lambda x: "{:,}".format(x))
        total_df['현재가'] = total_df['현재가'].astype(str)
        total_df['전일비'] = total_df['전일비'].astype(int)
        total_df['전일비'] = total_df['전일비'].apply(lambda x: "{:,}".format(x))
        total_df['전일비'] = total_df['전일비'].astype(str)
        total_df['전일비'] = total_df['등락률'].str[0] + total_df['전일비']
        total_df['시가총액'] = total_df['시가총액'].astype(int)
        total_df['시가총액'] = total_df['시가총액'].apply(lambda x: "{:,}".format(x))
        total_df['시가총액'] = total_df['시가총액'].astype(str)
        total_df = total_df.iloc[:, [0,1,2,3,4,6]]
        self.totalTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.totalTable.resizeColumnsToContents()

        for i in range(5):
            for j in range(5):    
                if j == 2 and total_df.iloc[i,j+1] == '00':
                    self.totalTable.setItem(i, j, QTableWidgetItem('-'))
                else:
                    self.totalTable.setItem(i, j, QTableWidgetItem(total_df.iloc[i,j+1]))

                if j == 3 and total_df.iloc[i,j+1][0] == '+':
                    self.totalTable.item(i, j).setForeground(QBrush(Qt.red))
                    self.totalTable.item(i, j-1).setForeground(QBrush(Qt.red))
                elif j == 3 and total_df.iloc[i,j+1][0] == '-':
                    self.totalTable.item(i, j).setForeground(QBrush(Qt.blue))
                    self.totalTable.item(i, j-1).setForeground(QBrush(Qt.blue))
                
                if j != 0:    
                    self.totalTable.item(i, j).setTextAlignment(Qt.AlignCenter)


        self.totalTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        
        
# 두번째 화면(주가 예측 결과 출력 화면) Class
class secondWindowClass(QDialog,QWidget, form_secondclass):
    def __init__(self): # 생성자 - 해당 클래스 생성시 실행되는 함수
        super(secondWindowClass, self).__init__()
        self.initUi() # 초기 UI 보여줌
        self.show() # 두번째 화면 보여줌
        self.show_graph() # 주가 그래프 보여줌
        self.show_predict_stock() # 주가 예측 결과 보여줌
        

    def initUi(self):
        self.setupUi(self) # QT Designer에서 만든 UI를 불러옴 
        
        # 기본 정보를 제공하는 label 속 내용 및 폰트 크기 설정
        self.label_stock_name.setText(f"{search_word} 주가 예측 결과")
        self.label_stock_name.setFont(QFont("", 13)) 
        self.label_stock_name.setAlignment(Qt.AlignCenter)
        self.label_graph_name.setText(f"{search_word} 주가 그래프 ")
        self.label_graph_name.setFont(QFont("", 9)) 
        self.label_today.setFont(QFont("", 9))
        self.label_today.setText(f"(오늘 : {self.get_today().date()} )")
        
    def get_stock_price(self, search_word):
        host = 'stock-1.c4mrb3hvrzue.ap-northeast-1.rds.amazonaws.com'
        port = 3306
        username = 'admin'
        database = 'stockdb'
        password = 'sis1234!'
        
        sql = f"SELECT * FROM {search_word}"
        conn = pymysql.connect(host = host, user=username, password = password, db = database,
        port = port, use_unicode=True, charset='utf8')
        with conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    result = cur.fetchall()
                    
        df = pd.DataFrame(result, columns = ['date', 'open', 'high', 'low', 'close', 'volume'])
        return df
    
    def show_graph(self): # 현재까지의 주가 그래프 보여주는 함수
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)

        self.stock_graph.addWidget(self.canvas)
        plt.rcParams['font.family'] = 'Malgun Gothic'
        print(search_word)
        df = self.get_stock_price(search_word)
        df_columns = ['Date','Open', 'High', 'Low', 'Close', 'Volume']
        df.columns = df_columns
        df = df.sort_values('Date')
        df['Date'] = df['Date'].astype(str)
        df['Date'] = df['Date'].str[:4] + '-' + df['Date'].str[4:6] + '-' + df['Date'].str[6:] 
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date',inplace=True)
        ma = [5,20,60]
        #ma = [5]
        for days in ma:
          df['ma_'+str(days)] = df['Close'].rolling(window = days).mean()
        
        
        df = df.iloc[-60:,:]
        start_index = df.index[0]
        end_index = df.index[-1]
        df.dropna(inplace=True)
        
        
        ax = self.fig.add_subplot(111)
        index = df.index.astype('str') # 캔들스틱 x축이 str로 들어감
        
        # 이동평균선 그리기
        ax.plot(index, df['ma_5'], label='MA5', linewidth=0.7)
        ax.plot(index, df['ma_20'], label='MA20', linewidth=0.7)
        ax.plot(index, df['ma_60'], label='MA60', linewidth=0.7)
        
        # X, Y축 티커 숫자 제한
        ax.xaxis.set_major_locator(ticker.MaxNLocator(3))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(6))
        
        # x, y 눈금값 글자 크기 조절
        ax.tick_params(axis = 'x', labelsize = 14)
        ax.tick_params(axis = 'y', labelsize = 12)
        # 그래프 title과 축 이름 지정
        ax.set_xlabel('Date')
        
        # 캔들차트 그리기
        candlestick2_ohlc(ax, df['Open'], df['High'], 
                          df['Low'], df['Close'],
                          width=0.5, colorup='r', colordown='b')
        ax.legend()
        plt.grid()
        plt.xlim(start_index, end_index)
        self.canvas.draw()
        
        
    def show_predict_stock(self): # 예측 결과를 보여주는 함수
        host = 'stock-1.c4mrb3hvrzue.ap-northeast-1.rds.amazonaws.com'
        port = 3306
        username = 'admin'
        database = 'stockdb'
        password = 'sis1234!'
        sql = f"SELECT * FROM {search_word}_예측"
        conn = pymysql.connect(host = host, user=username, password = password, db = database,
                port = port, use_unicode=True, charset='utf8')
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                result = cur.fetchall()
                
        predict_days = str(result[-1][0])
        predict_days = predict_days[0:4] + '년 ' + predict_days[4:6] + '월 ' + predict_days[6:] +'일'
        
        predict_results = result[-1][1:]
        current_price = self.get_stock_price(search_word).iloc[-1, -2]
        
        import exchange_calendars as ecals
        from dateutil.relativedelta import relativedelta
        import pandas as pd
        import datetime
        
        today =  datetime.datetime.now()
        end_date = today + relativedelta(days=10)
        
        k = ecals.get_calendar("XKRX")
        df = pd.DataFrame(k.schedule.loc[today:end_date, :])
        date_list = []
        for i in df['open']:
            date_list.append(i.strftime("%Y-%m-%d"))
        max_price_index = predict_results.index(max(predict_results))
        min_price_index = predict_results.index(min(predict_results))
        self.text_result.setFont(QFont("", 10)) 
        #self.text_result.append(f"<{search_word}의 주가 예측 결과>")
        self.text_result.append(f"{search_word}의 최신 종가는 {current_price}원입니다. ")
        self.text_result.append(f"{search_word}의 종가 예측 결과 ")
        self.text_result.append(f"최고가: {predict_results[max_price_index]}원 (일자: {date_list[max_price_index]}) ")
        self.text_result.append(f"최저가: {predict_results[min_price_index]}원 (일자: {date_list[min_price_index]}) ")
        
        
    # def loadImageFromFile(self) :
    #     #QPixmap 객체 생성 후 이미지 파일을 이용하여 QPixmap에 사진 데이터 Load하고, Label을 이용하여 화면에 표시
    #     pixmap_stockGraph = QPixmap("C:/Users/Mgyu/PL/financial/qt_design/005930.png")
    #     self.label_stockGraph.setPixmap(QPixmap(pixmap_stockGraph))
    #     self.show()
        
    def btn_second_to_main(self): # 첫번째 화면으로 돌아가는 함수
        self.close()  

    def get_today(self): # 오늘 날짜를 반환하는 함수
        today = dt.datetime.now()
        return today
    
if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_() 

    


