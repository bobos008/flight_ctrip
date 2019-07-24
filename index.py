# coding=utf-8


# import json
import os
import time
import tablib
import random
from flask import Flask, request, render_template, jsonify, send_file, make_response
from flightsctrip_class import FlightsCtrip
from citys import all_city_list

app = Flask(__name__)
current_flight_data = None
init_time = 0


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
    xls_header = (u'出发地', u'目的地', u'航空公司', u'型号', u'出发时间', u"出发机场", u"到达时间", u"到达机场", u"价格")
    flight_info = list()
    for flight in tflight_data:
        tr_data = list()
        tr_data.append(flight['flight']['departureAirportInfo']['cityName'])
        tr_data.append(flight['flight']['arrivalAirportInfo']['cityName'])
        tr_data.append(flight['flight']['airlineName'])
        tr_data.append(flight['flight']['flightNumber'])
        tr_data.append(flight['flight']['departureDate'])
        tr_data.append(flight['flight']['departureAirportInfo']['airportName'])
        tr_data.append(flight['flight']['arrivalDate'])
        tr_data.append(flight['flight']['arrivalAirportInfo']['airportName'])
        tr_data.append(flight['lowestPrice'])
        flight_info.append(tr_data)
    xls_obj = tablib.Dataset(*flight_info, headers=xls_header)
    with open(save_path, 'wb') as f:
        f.write(xls_obj.xls)
    return True


@app.route('/get_data')
def get_data():
    global current_flight_data

    # global init_time
    # cinit_time = time.time()
    # if current_flight_data and ((init_time + 15 * 60) <= cinit_time ):
    #     print("没有进行爬虫, 放回的全局数据！")
    #     return jsonify(current_flight_data)
    # init_time = cinit_time

    # city_list = [
    #     ('广州', '北京'),
    #     ('深圳', '北京'),
    #     ('珠海', '北京'),
    #     ('佛山', '北京'),
    #     ('揭阳', '北京'),
    #     ('惠州', '北京'),
    #     ('湛江', '北京'),
    # ]
    setoutdate = request.args.get('setoutdate')
    backdate = request.args.get('backdate')
    province = request.args.get('province')
    flight_way = request.args.get('flight_way')
    to_city = u'北京'
    city_list = list()
    province_citys = all_city_list.get(province)
    for ccity in province_citys:
        one_city = list()
        one_city.append(ccity)
        one_city.append(to_city)
        city_list.append(one_city)

    flight_data_list = list()
    for citys in city_list:
        from_city = citys[0]
        to_city = citys[1]
        from_date = setoutdate
        to_date = backdate
        num = 0
        while 1:
            flight_obj = FlightsCtrip()
            if num > 4:
                break
            flight_data = flight_obj.get_fligth_product(from_city, to_city, from_date, to_date, flight_way)
            if not flight_data['lowestPrice']:
                num += 1
                time.sleep(3)
                continue
            break
        flight_data_list.append(flight_data)
        time.sleep(3)
    # print(json.dumps(flight_data_list))
    sort_flight_data_list = sorted(flight_data_list, key=lambda x: x['lowestPrice'])
    current_flight_data = sort_flight_data_list
    return jsonify(sort_flight_data_list)


if __name__ == '__main__':
    app.run(port=8088, host="0.0.0.0", debug=True)
