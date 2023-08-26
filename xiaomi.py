#!/usr/bin/python3
import argparse
import asyncio
import json
import math
import re
import struct
import sys

from bleak import BleakClient, BleakScanner, BLEDevice, AdvertisementData


class Measurement():

    def __init__(self, temperatureC: float, relHumidity: float) -> None:

        self.temperatureC: float = temperatureC
        self.relHumidity: float = relHumidity

        z1 = (7.45 * self.temperatureC) / (235 + self.temperatureC)
        es = 6.1 * math.exp(z1*2.3025851)
        e = es * self.relHumidity / 100.0
        z2 = e / 6.1

        # absolute humidity / g/m3
        self.absHumidity: float = round(
            (216.7 * e) / (273.15 + self.temperatureC) * 10) / 10.0

        z3 = 0.434292289 * math.log(z2)
        self.dewPointC: float = int((235 * z3) / (7.45 - z3) * 10) / 10.0
        self.steamPressure: float = int(e * 10) / 10.0

        self.temperatureF: float = self.temperatureC * 9.0/5.0 + 32
        self.dewPointF: float = self.dewPointC * 9.0/5.0 + 32

    def __str__(self) -> str:

        return "\n".join([
            f"Temperature:    {self.temperatureC:.1f} °C",
            f"Dew point:      {self.dewPointC:.1f} °C",
            "",
            f"Temperature:    {self.temperatureF:.1f} °F",
            f"Dew point:      {self.dewPointF:.1f} °F",
            "",
            f"Rel. humidity:  {self.relHumidity:.1f} %",
            f"Abs. humidity:  {self.absHumidity:.1f} g/m³",
            f"Steam pressure: {self.steamPressure:.1f} mbar"
        ])

    def to_dict(self) -> dict:

        return {
            "temperatureC": self.temperatureC,
            "temperatureF": self.temperatureF,
            "relHumidity": self.relHumidity,
            "absHumidity": self.absHumidity,
            "dewPointC": self.dewPointC,
            "dewPointF": self.dewPointF,
            "steamPressure": self.steamPressure
        }


class DeviceInfo():

    def __init__(self, macAddress: str, name: str, manufacturer: str, model: str, hardware: str, firmware: str) -> None:

        self.macAddress: str = macAddress
        self.name: str = name
        self.manufacturer: str = manufacturer
        self.model: str = model
        self.hardware: str = hardware
        self.firmware: str = firmware

    def __str__(self) -> str:

        return "\n".join([
            f"MAC-Address:    {self.macAddress}",
            f"Devicename:     {self.name}",
            f"Manufacturer:   {self.manufacturer}",
            f"Model:          {self.model}",
            f"Hardware-Rev.:  {self.hardware}",
            f"Firmware-Rev.:  {self.firmware}"
        ])

    def to_dict(self) -> dict:

        return {
            "mac": self.macAddress,
            "name": self.name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "hardware": self.hardware,
            "firmware": self.firmware
        }


class XiaomiThermometerHygrometer():

    _CHARACTERISTIC_MANUFACTURER = '00002a29-0000-1000-8000-00805f9b34fb'
    _CHARACTERISTIC_NAME = '00002a00-0000-1000-8000-00805f9b34fb'
    _CHARACTERISTIC_MODEL = '00002a24-0000-1000-8000-00805f9b34fb'
    _CHARACTERISTIC_HARDWARE = '00002a27-0000-1000-8000-00805f9b34fb'
    _CHARACTERISTIC_FIRMWARE = '00002a26-0000-1000-8000-00805f9b34fb'
    _CHARACTERISTIC_BATTERY_LEVEL = '00002a19-0000-1000-8000-00805f9b34fb'
    _CHARACTERISTIC_MEASURE = '226cbb55-6476-4566-7562-66734470666d'

    def __init__(self, mac: str) -> None:

        self._client = BleakClient(mac)
        self._mac = mac
        self._measurement = None

    async def connect(self) -> None:

        await self._client.connect()

    async def disconnect(self) -> None:

        await self._client.disconnect()

    async def requestMeasurement(self) -> Measurement:

        async def notification_handler(c, bytes: bytearray) -> None:
            response = bytes.decode()
            m = re.match("T=([0-9\.]+) H=([0-9\.]+)", response)
            if m:
                self._measurement = Measurement(temperatureC=float(
                    m.groups()[0]), relHumidity=float(m.groups()[1]))

        if not self._client.is_connected:
            self.connect()

        await self._client.start_notify(0x0d, callback=notification_handler)
        await self._client.write_gatt_char(self._CHARACTERISTIC_MEASURE, bytearray([0x01, 0x00]), response=False)

        i = 0
        while not self._measurement and i < 10:
            await asyncio.sleep(.1)
            i += 1
        try:
            await self._client.stop_notify(0x0d)
        except:
            pass

        return self._measurement

    async def requestDeviceInfo(self) -> DeviceInfo:

        if not self._client.is_connected:
            self.connect()

        name = await self._client.read_gatt_char(XiaomiThermometerHygrometer._CHARACTERISTIC_NAME)
        manufacturer = await self._client.read_gatt_char(XiaomiThermometerHygrometer._CHARACTERISTIC_MANUFACTURER)
        model = await self._client.read_gatt_char(XiaomiThermometerHygrometer._CHARACTERISTIC_MODEL)
        hardware = await self._client.read_gatt_char(XiaomiThermometerHygrometer._CHARACTERISTIC_HARDWARE)
        firmware = await self._client.read_gatt_char(XiaomiThermometerHygrometer._CHARACTERISTIC_FIRMWARE)
        return DeviceInfo(self._mac, name.decode(), manufacturer.decode(), model.decode(), hardware.decode(), firmware.decode())

    async def requestBatteryLevel(self) -> int:

        if not self._client.is_connected:
            self.connect()

        batteryLevel = await self._client.read_gatt_char(XiaomiThermometerHygrometer._CHARACTERISTIC_BATTERY_LEVEL)
        return struct.unpack('>B', batteryLevel)[0]


async def scan():

    found_devices = list()

    def callback(device: BLEDevice, advertising_data: AdvertisementData):
        if device.address not in found_devices:
            found_devices.append(device.address)
            if device.name and device.address.lower().startswith("4c:65:a8:"):
                print(
                    f"{device.address}    {device.name}")
            elif device.name:
                print(' %i bluetooth devices seen' %
                      len(found_devices), end='\r', file=sys.stderr)

    async with BleakScanner(callback) as scanner:
        await asyncio.sleep(20)


async def main(args):

    device = XiaomiThermometerHygrometer(args.mac)
    data = dict()
    output = list()
    try:
        await device.connect()
        if args.info:
            deviceInfo = await device.requestDeviceInfo()
            data["info"] = deviceInfo.to_dict()
            output.append(f"{str(deviceInfo)}\n")

        if args.battery:
            batteryLevel = await device.requestBatteryLevel()
            data["battery"] = batteryLevel
            output.append(f"Battery-Level:  {batteryLevel}%\n")

        if args.measure:

            measurement = await device.requestMeasurement()
            data["measurement"] = measurement.to_dict()
            output.append(f"{str(measurement)}")

    except Exception as e:
        print(e)
    finally:
        await device.disconnect()

    if args.json and data:
        print(json.dumps(data, indent=2))
    elif output:
        print("\n".join(output))


def arg_parse(args: 'list[str]') -> dict:

    parser = argparse.ArgumentParser(
        'Shell script in order to request Xiaomi temperature humidity sensor')
    parser.add_argument('mac', type=str)
    parser.add_argument('-m', '--measure',
                        help='take a measurement', action='store_true')
    parser.add_argument('-b', '--battery',
                        help='request battery level', action='store_true')
    parser.add_argument(
        '-i', '--info', help='request device information', action='store_true')
    parser.add_argument(
        '-j', '--json', help='print in JSON format', action='store_true')
    parser.add_argument(
        '-s', '--scan', help='scan for devices for 20 seconds', action='store_true')

    return parser.parse_args(args)


if __name__ == '__main__':

    try:
        if '-s' in sys.argv or '--scan' in sys.argv:
            asyncio.run(scan())

        else:
            args = arg_parse(sys.argv[1:])
            asyncio.run(main(args))

    except KeyboardInterrupt:
        pass
