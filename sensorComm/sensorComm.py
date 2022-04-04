import urllib.request
import json

#API descr at https://github.com/opendata-stuttgart/meta/wiki/EN-APIs

SC_API_URL    = "https://api.sensor.community/v1/push-sensor-data/"

MAP_TO_SC = {
    "t":    "temperature",
    "h":    "humidity",
    "p":    "pressure",
    "pm1":  "P0",
    "pm2":  "P2",
    "pm4":  "P4",
    "pm10": "P1",
    "nc0":  "N05",
    "nc1":  "N1",
    "nc2":  "N25",
    "nc4":  "N4",
    "nc10": "N10",
    "tps":  "TS"
}



class sensorCommunity:

    def __init__(self, sensor_id:str = "", sampl_rate: int = 60, sw_version: str = '1.0'):
        self.sampling_rate    = sampl_rate
        self.software_version = sw_version
        self.sensor_id        = sensor_id
        self.data             = None

    def create_json(self, data: dict) -> None:
        json_values = {
            "software_version": self.software_version,
            "sampling_rate": self.sampling_rate,
            "sensordatavalues":[]
        }
        listObj = []
        for key in data:
            if key in MAP_TO_SC:
              val = {
                  "value_type": MAP_TO_SC[key],
                  "value": data[key]
              }
              listObj.append(val)
        json_values["sensordatavalues"] = listObj
        self.data = json.dumps(json_values)

    def post(self, Xpin:int = 1) -> str:
        try:
            url = SC_API_URL
            print("POST Data ", url)
            headers = {
                'User-Agent'  : "Python/AirQmonitor",
                'Connection'  : "close",
                'Content-Type': "application/json",
                'X-Pin'       : Xpin,
                'X-Sensor'    : self.sensor_id
            }
            postData = self.data.encode('ascii')
            req = urllib.request.Request(url, postData, headers = headers)
            resp = urllib.request.urlopen(req)
            return resp.read()

        except Exception as e:
            print("Unable to POST for client", headers['User-Agent'])
            print(str(e))
