# xiaomi-Bluetooth-thermometer
Xiaomi temperature humidity sensor

This is a little script in order to read temperature and humidity from Xiaomi sensor.

## Version based on ```gatttool``` and ```expect```

*Note* Make sure that gatttool and expect are installed. 

```
$ ./xiaomi.exp 4C:65:A8:DA:F3:B1
Temperature:    22.9 °C
Dew point:      17.1 °C
Rel. humidity:  70.0 %
Abs. humidity:  14.3 g/m³
Steam pressure: 19.5 mbar

Battery:        11 %
```

## Version based on ```python``` and ```bleak```

*Note* Make sure that Python 3 and the module bleak are installed. 

```
$ ./xiaomi.py --help
usage: Shell script in order to request Xiaomi temperature humidity sensor [-h] [-m] [-b] [-i] [-j] [-s] mac

positional arguments:
  mac

options:
  -h, --help     show this help message and exit
  -m, --measure  take a measurement
  -b, --battery  request battery level
  -i, --info     request device information
  -j, --json     print in JSON format
  -s, --scan     scan for devices for 20 seconds
```

Example:
```
$ ./xiaomi.py 4c:65:a8:da:f3:b1 -b -i -m -j
{
  "info": {
    "mac": "4c:65:a8:da:f3:b1",
    "name": "MJ_HT_V1",
    "manufacturer": "Cleargrass Inc",
    "model": "Duck_Release",
    "hardware": "2.00",
    "firmware": "00.00.66"
  },
  "battery": 52,
  "measurement": {
    "temperatureC": 22.6,
    "temperatureF": 72.68,
    "relHumidity": 61.6,
    "absHumidity": 12.4,
    "dewPointC": 14.8,
    "dewPointF": 58.64,
    "steamPressure": 16.9
  }
}
```