# coding=utf-8

import sqlite3

"""
注意： 一定要先手动创建数据库,然后执行该文件
在终端中输入命令： sqlite3 CTRIPDB
退出sqlite3命令：.quit
"""
_db_name = 'CTRIPDB'
conn = sqlite3.connect(_db_name)
table_name = 'ctrip'


def create_flight_table():
    """生成机票数据表"""
    try:
        # sql = 'create table if not exists "%s" (id INTEGER PRIMARY KEY AUTOINCREMENT, toCity VARCHAR(30),\
        #     fromCity VARCHAR(30), tairportName VARCHAR(100), tairlineName VARCHAR(100), tflightNumber VARCHAR(30),\
        #     tdepartureDate VARCHAR(30), bairportName VARCHAR(100), bairlineName VARCHAR(100), bflightNumber\
        #     VARCHAR(30), bdepartureDate VARCHAR(30), lowestPrice VARCHAR(100));' % table_name
        sql = 'create table if not exists "%s" (id INTEGER PRIMARY KEY AUTOINCREMENT, flightInfo TEXT, \
            province VARCHAR(30), dateTime VARCHAR(100));' % table_name
        cursor_obj = conn.cursor()
        cursor_obj.execute(sql)
        cursor_obj.close()
    except Exception as error:
        print("error:", error)
        return False
    return True


if __name__ == "__main__":
    create_flight_table()
    print("create table successful!")
    conn.close()
