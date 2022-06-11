import exifread
import re
import json
import requests
import sys
import os

def latitude_and_longitude_convert_to_decimal_system(*arg):
    """
    """
    return float(arg[0]) + ((float(arg[1]) + (float(arg[2].split('/')[0]) / float(arg[2].split('/')[-1]) / 60)) / 60)

def parse_image(filename):
    fd = open(filename, 'rb')
    tags = exifread.process_file(fd)
    FIELD = 'EXIF DateTimeOriginal'
    fd.close()
    for k,v in tags:
        print("key: %s, value: %s \n" %(str(k) , str(v)) )

def find_GPS_image(pic_path):
    GPS = {}
    date = ''
    with open(pic_path, 'rb') as f:
        tags = exifread.process_file(f)
        for tag, value in tags.items():
            if re.match('Image Make', tag):
                print('[*] band: ' + str(value))
            if re.match('Image Model', tag):
                print('[*] xinghao: ' + str(value))
            if re.match('EXIF LensModel', tag):
                print('[*] shexiangtou: ' + str(value))
            if re.match('GPS GPSLatitudeRef', tag):
                GPS['GPSLatitudeRef'] = str(value)
            elif re.match('GPS GPSLongitudeRef', tag):
                GPS['GPSLongitudeRef'] = str(value)
            elif re.match('GPS GPSAltitudeRef', tag):
                GPS['GPSAltitudeRef'] = str(value)
            elif re.match('GPS GPSLatitude', tag):
                try:
                    match_result = re.match('\[(\w*),(\w*),(\w.*)/(\w.*)\]', str(value)).groups()
                    GPS['GPSLatitude'] = int(match_result[0]), int(match_result[1]), int(match_result[2])
                except:
                    deg, min, sec = [x.replace(' ', '') for x in str(value)[1:-1].split(',')]
                    GPS['GPSLatitude'] = latitude_and_longitude_convert_to_decimal_system(deg, min, sec)
            elif re.match('GPS GPSLongitude', tag):
                try:
                    match_result = re.match('\[(\w*),(\w*),(\w.*)/(\w.*)\]', str(value)).groups()
                    GPS['GPSLongitude'] = int(match_result[0]), int(match_result[1]), int(match_result[2])
                except:
                    deg, min, sec = [x.replace(' ', '') for x in str(value)[1:-1].split(',')]
                    GPS['GPSLongitude'] = latitude_and_longitude_convert_to_decimal_system(deg, min, sec)
            elif re.match('GPS GPSAltitude', tag):
                GPS['GPSAltitude'] = str(value)
            elif re.match('.*Date.*', tag):
                date = str(value)
            else :
                print('tag:'+ str(tag) + ', value:'+str(value))
    #print({'GPS_information':GPS, 'date_information': date})
    print('[*] time: '+ date)
    return {'GPS_information': GPS, 'date_information': date}


def find_address_from_GPS(GPS):
    """
    """
    secret_key = ''
    if not GPS['GPS_information']:
        return 'no gps'
    lat, lng = GPS['GPS_information']['GPSLatitude'], GPS['GPS_information']['GPSLongitude']
    print('[*] jingdu: ' + str(lat) + ', weidu: ' + str(lng))
    baidu_map_api = "http://api.map.baidu.com/geocoder/v2/?ak={0}&callback=renderReverse&location={1},{2}s&output=json&pois=0".format(
        secret_key, lat, lng)
    response = requests.get(baidu_map_api)
    content = response.text.replace("renderReverse&&renderReverse(", "")[:-1]
    #print(content)
    baidu_map_address = json.loads(content)
    formatted_address = baidu_map_address["result"]["formatted_address"]
    # province = baidu_map_address["result"]["addressComponent"]["province"]
    # city = baidu_map_address["result"]["addressComponent"]["city"]
    # district = baidu_map_address["result"]["addressComponent"]["district"]
    return formatted_address


img_path = 'C:\\Work\\3.workspace\\Fearless\\imgs\\6.jpg'
if len(img_path) >= 2:
    print('[*] open file: '+ img_path)
    GPS_info = find_GPS_image(pic_path=img_path)
    address = find_address_from_GPS(GPS=GPS_info)
    print('[*] position: '+address)
    print('---------------------------')
    parse_image(img_path)
else:
    print('python script.py filename')



