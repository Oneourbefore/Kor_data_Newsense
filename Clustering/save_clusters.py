# -*- coding: utf-8 -*-
"""SaveToDB_clustering.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NOREDQXz_7ctQFgI7ObHmfx7Ihb4KEAv
"""

import pymysql
import pandas as pd
import json
from datetime import datetime
import ast
from database import MysqlConnection

# 클러스터링 결과 DB 저장 함수
def insert_data_to_mysql(data):

    conn = None
    try:
        # MySQL 연결
        db_connection = MysqlConnection()
        conn = db_connection.connection
        cursor = conn.cursor()

        values = []
        for entry in data:
            entry_values = (
                entry['number'],
                entry['datetime'],
                str(entry['nid'])
            )
            values.append(entry_values)

        # MySQL 테이블에 삽입
        query = "INSERT INTO news_cluster (`rank`, `datetime`, `nid`) VALUES (%s, %s, %s)"
        cursor.executemany(query, values)

        # 변경 사항 저장
        conn.commit()

    except pymysql.Error as err:
        print(f"Error: {err}")

    finally:
        if conn:
            cursor.close()
            conn.close()

# 대표기사 제목 DB 저장 함수
def insert_main_title_data_to_mysql(data):
    conn = None
    try:
        # MySQL 연결
        db_connection = MysqlConnection()
        conn = db_connection.connection
        cursor = conn.cursor()

        values = []
        for entry in data:
            entry_values = (
                entry['nc_id'],
                entry['datetime'],
                entry['best_title'],
            )
            values.append(entry_values)

        # MySQL 테이블에 삽입
        query = "INSERT INTO news_main_title (`nc_id`, `datetime`, `title`) VALUES (%s, %s, %s)"
        cursor.executemany(query, values)


        conn.commit()

    except pymysql.Error as err:
        print(f"Error: {err}")

    finally:
        if conn:
            cursor.close()
            conn.close()

# 클러스터 키워드 DB 저장 함수
def insert_cluster_keyword_data_to_mysql(data):
    conn = None
    try:
        # MySQL 연결
        db_connection = MysqlConnection()
        conn = db_connection.connection
        cursor = conn.cursor()

        values = []
        for entry in data:
            entry_values = (
                entry['keyword'],
                entry['nc_id'],
                entry['datetime'],
            )
            values.append(entry_values)

        # MySQL 테이블에 삽입
        query = "INSERT INTO cluster_keyword (`keyword`, `nc_id`, `datetime`) VALUES (%s, %s, %s)"
        cursor.executemany(query, values)


        conn.commit()

    except pymysql.Error as err:
        print(f"Error: {err}")

    finally:
        if conn:
            cursor.close()
            conn.close()

"""## 클러스터 데이터 DB 저장"""

dates = ['2023-08-23']

if __name__ == "__main__":

    for date in dates:

        ## 파일 경로
        path = f"/cluster_{date}.json"
        # JSON 파일 읽기
        with open(path, 'r',encoding='utf-8') as file:
            json_data = json.load(file)
        # MySQL 데이터베이스에 데이터 삽입
        insert_data_to_mysql(json_data)

"""## 대표기사 DB 등록"""

db_connection = MysqlConnection()
conn = db_connection.connection
cursor = conn.cursor()

# SQL 쿼리 실행
query = "SELECT `nc_id`, `rank`, `datetime` FROM news_cluster"
cursor.execute(query)

# 결과 가져오기
result = cursor.fetchall()

df_load = pd.DataFrame(result, columns=['nc_id', 'rank', 'datetime'])

for date in dates:
    # DB에서 가져온 df와 json파일의 df를 rank, datetime을 기준으로 merge
    df_title_load = pd.read_json(f'/cluster_{date}.json',encoding='utf-8')
    df_title_load['datetime'] = df_title_load['datetime'].dt.date
    df_merge = pd.merge(df_load, df_title_load, left_on=['rank','datetime'], right_on=['number','datetime'], how='inner')

    # 필요한 columns 추출
    df_merge_DB = df_merge[['nc_id','best_title','datetime']]

    main_title_list = []
    for index, row in df_merge_DB.iterrows():
        main_title_list.append({
            'nc_id': str(row['nc_id']),
            'datetime': str(row['datetime']),
            'best_title': str(row['best_title'])
        })

    insert_main_title_data_to_mysql(main_title_list)

"""# cluster_keyword 데이터 DB 저장"""

db_connection = MysqlConnection()
conn = db_connection.connection

# 커서 생성
cursor = conn.cursor()

# SQL 쿼리 실행
query = "SELECT `nc_id`, `rank`, `datetime` FROM news_cluster"
cursor.execute(query)

# 결과 가져오기
result = cursor.fetchall()

df_load = pd.DataFrame(result, columns=['nc_id', 'rank', 'datetime'])

for date in dates:

    df_title_load = pd.read_json(f'/cluster_{date}.json',encoding='utf-8')
    df_title_load['datetime'] = df_title_load['datetime'].dt.date
    df_merge = pd.merge(df_load, df_title_load, left_on=['rank','datetime'], right_on=['number','datetime'], how='inner')

    df_merge_DB = df_merge[['nc_id','keyword','datetime']]

    new_rows = []
    # 각 행을 순회하며 keyword를 분할하여 새로운 행 추가
    for index, row in df_merge_DB.iterrows():
        keywords = row['keyword'].split(',')
        for keyword in keywords:
            new_row = [row['nc_id'], keyword, row['datetime']]
            new_rows.append(new_row)
    # 새로운 행들을 DataFrame에 추가
    new_df = pd.DataFrame(new_rows, columns=['nc_id', 'keyword', 'datetime'])

    keyword_list = []
    for index, row in new_df.iterrows():
        keyword_list.append({
            'nc_id': str(row['nc_id']),
            'keyword': str(row['keyword']),
            'datetime': str(row['datetime'])
        })

    insert_cluster_keyword_data_to_mysql(keyword_list)

"""# news 테이블 nc_id update"""

# 기사가 저장된 DB에서 클러스터링된 기사에 대해 클러스터링 번호 update

db_connection = MysqlConnection()
conn = db_connection.connection
cursor = conn.cursor()

try:
    with conn.cursor() as cursor:
        id_dict = {}
        for date in dates:
            # 데이터를 받아올 SQL 쿼리 작성
            query = "SELECT nc_id, nid FROM news_cluster WHERE DATE(datetime) = %s;"
            cursor.execute(query, date)

            # 쿼리 실행 결과 받아오기
            result = list(cursor.fetchall())

            for item in result:
                nc_id = item[0]
                sepa_item = ast.literal_eval(item[1])
                for nid in sepa_item:
                    id_dict[nid] = nc_id

            for nid, nc_id in id_dict.items():
                query = "UPDATE news SET nc_id = %s WHERE nid = %s;"
                value = (nc_id, nid)
                cursor.execute(query, value)

    # 변경 내용을 커밋
    cursor.commit()

except pymysql.Error as err:
    print(f"Error: {err}")

finally:
    # 연결 종료
    cursor.close()
    conn.close()