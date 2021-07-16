# xiaomi-Bluetooth-thermometer
Xiaomi temperature humidity sensor

This is a little script in order to read temperature and humidity from Xiaomi sensor.

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