# coding=utf-8

import requests
import json
import random
from useragent import user_agent_list


class FlightsCtrip(object):
    """携程机票获取"""

    def __init__(self):
        self.init_url = 'https://flights.ctrip.com/'
        self.city_data_url = 'https://flights.ctrip.com/domestic/poi'
        # cuser_agent = random.choice(user_agent_list)
        cuser_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
        print(cuser_agent)
        self.user_agent = cuser_agent
        self.ss = requests.session()
        self.is_init_page = self.load_init_page()

    def load_init_page(self):
        """请求初始页面"""
        headers = self.make_headers()
        rp = self.back_reponse(self.init_url, headers=headers)
        if not rp:
            print("load index page error！")
            return False
        return True

    def make_headers(self):
        """制作请求头"""
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent
        }
        return headers

    def back_reponse(self, url, headers, params=None, form_data=None, json_data=None, is_get=True):
        """操作requests模块"""
        try:
            if is_get:
                rp = self.ss.get(url, headers=headers, params=params, timeout=5)
            else:
                rp = self.ss.post(url, headers=headers, params=params, data=form_data, json=json_data, timeout=5)
            if rp.status_code == 200:
                return rp
            else:
                print("back_response_error:", "status_code not 200!")
                return None
        except Exception as error:
            print("back_response_error:", error)
            return None

    def get_city_data(self, city_name):
        """获取城市信息"""
        params = {
            'channel': '1',
            'mode': '1',
            'f': '2',
            'key': city_name,
            'v': '0'
        }
        headers = self.make_headers()
        headers['accept'] = '*/*'
        headers['referer'] = 'https://flights.ctrip.com/'
        rp = self.back_reponse(self.city_data_url, headers=headers, params=params)
        if not rp:
            return None
        city_text = rp.text
        equal_index = city_text.find('=')
        if equal_index == -1:
            return None
        city_json = city_text[equal_index + 1:]
        city_data = json.loads(city_json)
        # print("city_data:", city_data)
        return city_data

    def get_city_code(self, city_name):
        """获取城市的code"""
        if not city_name:
            return None
        back_city_data = self.get_city_data(city_name)
        if not back_city_data:
            print("get city data is none")
            return None
        city_data_list = back_city_data.get('Data', '')
        if (not city_data_list) and isinstance(city_data_list, list):
            return None
        city_data = city_data_list[0]
        city_code = city_data.get('Code', '')
        city_id = city_data.get('CityId', 0)
        back_res = (city_code, city_id)
        return back_res

    def load_flight_page(self, flight_url):
        """加载机票产品页面"""
        headers = self.make_headers()
        rp = self.back_reponse(flight_url, headers=headers)
        if not rp:
            return False
        return True

    @staticmethod
    def get_lowest_legs_data(original_data, ftype):
        """获取最低飞机票数据"""
        legs_data = dict()
        route_kw_data = 'data'
        route_list = 'routeList'
        route_type = 'routeType'
        flight = 'Flight'
        # route_type_val = 'Transit'
        print original_data['data']['error']['msg']
        route_data = original_data.get(route_kw_data, None)
        if not route_data:
            print("get_lowest_legs_data_error:", 'no keyword name "data"')
            return legs_data
        route_list_data = route_data.get(route_list, None)
        if not route_list_data:
            print("get_lowest_legs_data_error:", 'no keyword name "routeList"')
            return legs_data
        new_route_list = list()
        for route_data in route_list_data:
            if route_data.get(route_type, None) == flight:
                new_route_list.append(route_data)
        if ftype == 'Oneway':
            try:
                price_sort_data = sorted(new_route_list, key=lambda x: x['legs'][0]['characteristic']['lowestPrice'])
            except Exception as error:
                print('get_lowest_legs_data_error:', error)
                return None
        else:
            price_sort_data = sorted(new_route_list, key=lambda x: x.get('combinedPrice', 0))
        if not price_sort_data:
            return legs_data
        return price_sort_data[0]

    @staticmethod
    def wash_data(ldata, tmp_data, ftype='Oneway'):
        """清洗机票数"""

        legs = 'legs'
        tflight = 'flight'
        if not isinstance(ldata, dict):
            print("wash_error:", 'ldata not dict!')
            return tmp_data
        legs_list = ldata.get(legs, None)
        if not legs_list:
            print("wash_error:", 'no keyword "legs"!')
            return tmp_data
        if not isinstance(legs_list, list):
            print("wash_error:", 'legs_list not list')
            return tmp_data
        flight_data = legs_list[0].get(tflight, None)
        if not flight_data:
            print("wash_error:", 'no keyword "flight"!')
            return tmp_data
        if ftype != 'Oneway':
            combined_price = 'combinedPrice'
            lowest_price = ldata.get(combined_price, 0)
            tmp_data['lowestPrice'] = lowest_price
        else:
            characteristic = 'characteristic'
            lowest_price = 'lowestPrice'
            characteristic_data = legs_list[0].get(characteristic, None)
            if not characteristic_data and (not isinstance(characteristic_data, dict)):
                print("wash_error:", 'no keyword "characteristic"!')
                return tmp_data
            tmp_data['lowestPrice'] = characteristic_data.get(lowest_price, 0)
        tmp_data_flight = tmp_data[tflight]
        for key in tmp_data_flight.keys():
            if isinstance(tmp_data_flight[key], dict):
                if (key == 'arrivalAirportInfo') or (key == 'departureAirportInfo'):
                    city_name = 'cityName'
                    airport_name = 'airportName'
                    tmp_data_flight[key][city_name] = flight_data[key][city_name]
                    tmp_data_flight[key][airport_name] = flight_data[key][airport_name]
            else:
                tmp_data_flight[key] = flight_data[key]
        tmp_data[tflight] = tmp_data_flight
        return tmp_data

    def get_fligth_product(self, city1_name, city2_name, date1, date2, flight_type='Roundtrip'):
        """获取往返机票产品数据"""
        ctmp_data = {
            'flight': {
                'arrivalAirportInfo': {'cityName': city2_name, 'airportName': ''},
                'departureAirportInfo': {'cityName': city1_name, 'airportName': ''},
                'airlineName': '',
                'departureDate': '',
                'arrivalDate': '',
                'flightNumber': ''
            },
            'lowestPrice': 0,
        }
        if not self.is_init_page:
            if not self.load_init_page():
                return ctmp_data
        if (not date1) or (not date2) or (not city1_name) or (not city2_name):
            return ctmp_data
        city1_info_set = self.get_city_code(city1_name)
        city2_info_set = self.get_city_code(city2_name)
        if (not city1_info_set) or (not city2_info_set):
            return ctmp_data
        city1_code = city1_info_set[0]
        city2_code = city2_info_set[0]
        city1_id = city1_info_set[1]
        city2_id = city2_info_set[1]
        payload_data = {
            "flightWay": flight_type,
            "classType": "ALL",
            "hasChild": False,
            "hasBaby": False,
            "searchIndex": 1,
            "airportParams": [
                {
                    "dcity": city1_code,
                    "acity": city2_code,
                    "dcityname": city1_name,
                    "acityname": city2_name,
                    "date": date1,
                    "dcityid": city1_id,
                    "acityid": city2_id
                },
                {
                    "dcity": city2_code,
                    "acity": city1_code,
                    "dcityname": city2_name,
                    "acityname": city1_name,
                    "date": date2,
                    "dcityid": city2_id,
                    "acityid": city1_id
                }
            ]
        }
        flight_page_url = 'https://flights.ctrip.com/itinerary/roundtrip/%s-%s?date=%s,%s' % (
            city1_code, city2_code, date1, date2)
        if flight_type == 'Oneway':
            # 表示单程
            flight_page_url = 'https://flights.ctrip.com/itinerary/oneway/%s-%s?date=%s' % (
                city1_code, city2_code, date1)
            payload_data['airportParams'].remove(payload_data['airportParams'][0])

        if not self.load_flight_page(flight_page_url):
            print("load flight page error")
            return ctmp_data

        products_url = 'https://flights.ctrip.com/itinerary/api/12808/products'
        headers = self.make_headers()
        headers['accept'] = '*/*'
        # headers['content-length'] = '344'
        headers['content-type'] = 'application/json'
        headers['referer'] = products_url

        rp_data = self.back_reponse(products_url, headers=headers, json_data=payload_data, is_get=False)
        if not rp_data:
            return ctmp_data
        try:
            # print(rp_data.text)
            products_data = json.loads(rp_data.text)
        except Exception as error:
            print("products_error:", error)
            return ctmp_data
        lowest_legs_data = self.get_lowest_legs_data(products_data, flight_type)
        current_wash_data = self.wash_data(lowest_legs_data, ctmp_data, flight_type)
        return current_wash_data


if __name__ == '__main__':
    fc = FlightsCtrip()
    cn1 = '广州'
    cn2 = '北京'
    de1 = '2019-07-26'
    de2 = '2019-07-31'
    cflight_type = 'Oneway'
    print(fc.get_fligth_product(cn1, cn2, de1, de2, cflight_type))
    # print(fc.get_fligth_product(cn1, cn2, de1, de2))
