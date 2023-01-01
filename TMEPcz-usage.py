from TMEPcz.TMEPcz import TMEPcz

# TMEP
TMEP_USER_DOMAIN = "YourTMEPdomain OMMIT tmep.cz !!!"  # Example 'testsensor' for http://testsensor.tmep.cz
# values you want to push to TMEP
TMEP_USER_QSV    = ['pm10', 'pm2', 'h']

#Init
tmep = TMEPcz()

... reading values from one or multiple sensors to the sensors_values: dict ...

tmep.values_to_query_str(TMEP_USER_QSV, sensors_values)
try:
  tmep.push(TMEP_USER_DOMAIN)
except Exception as e:
  print("=== TMEP PUSH ERROR ===")
