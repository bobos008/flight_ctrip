# coding=utf-8

import json
import os
import time
import tablib
import sqlite3
import threading
from flask import Flask, request, render_template, jsonify, send_file, make_response
from datetime import datetime
from flightctrip_class import FlightCtrip
from citys import all_city_list

app = Flask(__name__)
current_flight_data = None
init_time = 0
setting_time = {'setoutdate': None, 'backdate': None}
null_data = {
    'flight': {
        'toCity': '',
        'fromCity': '',
        'tripInfo': {'airportName': '', 'airlineName': '', 'flightNumber': '', 'departureDate': ''},
        'backTripInfo': {'airportName': '', 'airlineName': '', 'flightNumber': '', 'departureDate': ''}
    },
    'lowestPrice': '',
}


@app.route('/')
def web_index():
    return render_template('index.html')


@app.route('/downloads/', methods=['GET'])
def download_excel():
    """导出excel文件"""
    global current_flight_data
    if not current_flight_data:
        return render_template('index.html')
    filename = request.args.get('filename')
    save_file_path = './files/%s.xls' % filename
    make_xls(current_flight_data, save_file_path)
    response = make_response(send_file(save_file_path))
    response.headers["Content-Disposition"] = "attachment; filename=%s.xls;" % filename
    try:
        os.remove(save_file_path)
    except Exception as error:
        print("download_excel_error:", error)
        return render_template('index.html')
    return response


def make_xls(tflight_data, save_path):
    """生成xls文件"""
    if not isinstance(tflight_data, list):
        return False
    xls_header = (
        u'出发地',
        u'目的地',
        u'航空公司(去)',
        u'航班号(去)',
        u'出发时间(去)',
        u"出发机场(去)",
        u"航空公司(返)",
        u"航班号(返)",
        u"出发时间(返)",
        u"出发机场(返)",
        u"价格(元)")
    flight_info = list()
    for flight in tflight_data:
        tr_data = list()
        try:
            tr_data.append(flight['flight']['fromCity'])
            tr_data.append(flight['flight']['toCity'])
            tr_data.append(flight['flight']['tripInfo']['airlineName'])
            tr_data.append(flight['flight']['tripInfo']['flightNumber'])
            tr_data.append(flight['flight']['tripInfo']['departureDate'])
            tr_data.append(flight['flight']['tripInfo']['airportName'])
            tr_data.append(flight['flight']['backTripInfo']['airlineName'])
            tr_data.append(flight['flight']['backTripInfo']['flightNumber'])
            tr_data.append(flight['flight']['backTripInfo']['departureDate'])
            tr_data.append(flight['flight']['backTripInfo']['airportName'])
            tr_data.append(flight['lowestPrice'])
        except Exception as error:
            print("make_xls_error:", error)
            continue
        flight_info.append(tr_data)
    xls_obj = tablib.Dataset(*flight_info, headers=xls_header)
    with open(save_path, 'wb') as f:
        f.write(xls_obj.xls)
    return True


@app.route('/get_data')
def get_data():
    global current_flight_data
    setoutdate = request.args.get('setoutdate')
    backdate = request.args.get('backdate')
    cur_province = request.args.get('province')
    flight_way = request.args.get('flight_way')
    cur_to_city = u'北京'

    fc = FlightCtrip()
    flight_data_list = fc.main(cur_province, cur_to_city, setoutdate, backdate, flight_way)
    fc.close()
    # print(json.dumps(flight_data_list))
    sort_flight_data_list = sorted(flight_data_list, key=lambda x: x['lowestPrice'])
    current_flight_data = sort_flight_data_list
    return jsonify(sort_flight_data_list)


@app.route('/downloadsdb/')
def download_all_excel():
    """把数据库中的数据导出为excel文件"""
    cur_table = 'ctrip'
    db_name = "CTRIPDB"
    filename = request.args.get('filename')
    save_file_path = './files/%s.xls' % filename
    conn = sqlite3.connect(db_name)
    sql = "select flightInfo from %s;" % cur_table
    cursor_obj = conn.cursor()
    cursor_obj.execute(sql)
    db_flight_data_list = cursor_obj.fetchall()
    flight_data_list = list()
    for flight_data in db_flight_data_list:
        province_flight_data = json.loads(flight_data[0])
        for city_flight_data in province_flight_data:
            flight_data_list.append(city_flight_data)
    cursor_obj.close()
    conn.close()
    make_xls(flight_data_list, save_file_path)
    response = make_response(send_file(save_file_path))
    response.headers["Content-Disposition"] = "attachment; filename=%s.xls;" % filename
    try:
        os.remove(save_file_path)
    except Exception as error:
        print("download_excel_error:", error)
        return render_template('index.html')
    return response


@app.route('/time_all_data')
def setting_time_get_data():
    global setting_time
    res = True
    setoutdate = request.args.get('setoutdate', None)
    backdate = request.args.get('backdate', None)
    if not setoutdate and not backdate:
        res = False
        return jsonify({"res": res})
    setting_time['setoutdate'] = setoutdate
    setting_time['backdate'] = backdate
    return jsonify({"res": res})


def get_all_city_flight_data():
    """获取所有城市机票数据"""
    global setting_time
    cur_to_city = u'北京'
    db_name = "CTRIPDB"
    cur_table = 'ctrip'
    # setoutdate = '2019-08-10'
    # backdate = '2019-09-01'
    while 1:
        curr_time = datetime.now()
        curr_weekday = curr_time.weekday()
        curr_hour = curr_time.hour
        # curr_min = curr_time.minute
        if curr_weekday != 0:
            # print("weekday:", curr_weekday)
            time.sleep(1)
            continue
        if curr_hour == 1:
            conn = sqlite3.connect(db_name)
            del_cursor = conn.cursor()
            delete_sql = "delete from %s;" % cur_table
            del_cursor.execute(delete_sql)
            del_cursor.close()
            conn.commit()
            conn.close()
            print("删除所有的数据！")
            time.sleep(3600)
        if curr_hour != 5:
            time.sleep(1)
            continue
        setoutdate = setting_time['setoutdate']
        backdate = setting_time['backdate']
        if not setoutdate and not backdate:
            time.sleep(1)
            # print("没有设置出发时间！")
            continue
        print("开始任务")
        conn = sqlite3.connect(db_name)
        for province in all_city_list:
            try:
                fc = FlightCtrip()
                cur_province_flight_data = fc.main(province, cur_to_city, setoutdate, backdate)
                fc.close()
            except Exception as error:
                print("get_all_city_data_error:", error)
                fc = FlightCtrip()
                cur_province_flight_data = fc.main(province, cur_to_city, setoutdate, backdate)
                fc.close()
            if not cur_province_flight_data:
                fc = FlightCtrip()
                cur_province_flight_data = fc.main(province, cur_to_city, setoutdate, backdate)
                fc.close()
            cur_province_flight_data.append(null_data)
            province_json = json.dumps(cur_province_flight_data)
            curr_time_temp = str(int(time.time()))
            insert_sql = "insert into %s (flightInfo, province, dateTime) values('%s', '%s', '%s');" % (
                cur_table, province_json, province, curr_time_temp)
            cursor_obj = conn.cursor()
            cursor_obj.execute(insert_sql)
            if not cursor_obj.rowcount:
                print("没有提交成功！")
                continue
            print("%s添加数据库成功！" % province)
            cursor_obj.close()
            conn.commit()
            time.sleep(3 * 60)
        conn.close()
        time.sleep(3600)


def run_app():
    app.run(port=8088, host="0.0.0.0", debug=True)


if __name__ == '__main__':
    # get_all_city_flight_data()
    # download_all_excel()
    t1 = threading.Thread(target=get_all_city_flight_data)
    t1.start()
    run_app()
