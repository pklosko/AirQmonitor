import os
import urllib.request
from urllib.error import HTTPError, URLError
from socket import timeout

TMEP_DOMAIN   = ".tmep.cz/?"

class TMEPcz:

    def __init__(self, interval: int = 3, timeout:int = 5) -> None:
        self.query_string  = ""
        self.push_interval = interval
        self.timeout       = timeout

    def push(self, sensor_domain:str, sensor_guid:str = '') -> str:
        try:
            if (sensor_guid != ''):
              self.query_string = self.query_string.replace(self.query_string[0:self.query_string.find('=')],sensor_guid)

            url = "http://" + sensor_domain + TMEP_DOMAIN + self.query_string
#            print(url)
            headers = {
              'User-Agent' : "Python/AirQmonitor("+ os.uname().nodename + "[" + str(os.getpid()) + "])",
              'Connection' : "close"
            }
#            print(headers)
            req = urllib.request.Request(url, headers = headers)
            try:
              resp = urllib.request.urlopen(req, timeout = self.timeout)
              return resp.read()
            except HTTPError as error:
              print('HTTP Error: %s\nURL: %s', error, url)
            except URLError as error:
              if isinstance(error.reason, timeout):
                print('Timeout Error: %s\nURL: %s', error, url)
              else:
                print('URL Error: %s\nURL: %s', error, url)
        except Exception as e:
            print("Unable to push Info for client", headers['User-Agent'])
            print(str(e))

    def values_to_query_str(self, quantity: list, data: dict, presision: int = 3) -> None:
        self.query_string = ""
        for idx in quantity:
            if (idx == 'p' and data[idx] > 2000):
                data[idx] = data[idx] /100
            self.query_string = self.query_string + idx + '=' + str(round(data[idx],presision)) + '&'
