#!/usr/bin/env python2

import paho.mqtt.client as mqtt
import time
import Adafruit_DHT
from configparser import ConfigParser
import json
from collections import deque

config = ConfigParser(delimiters=('=', ))
config.read('config.ini')

sensor_type = config['sensor'].get('type', 'dht22').lower()

if sensor_type == 'dht22':
    sensor = Adafruit_DHT.DHT22
elif sensor_type == 'dht11':
    sensor = Adafruit_DHT.dht11
elif sensor_type == 'am2302':
    sensor = Adafruit_DHT.AM2302
else:
    raise Exception('Supported sensor types: DHT22, DHT11, AM2302')

pin = config['sensor'].get('pin', 10)
topic = config['mqtt'].get('topic', 'temperature/dht22')
decim_digits = config['sensor'].getint('decimal_digits', 2)
sleep_time = config['sensor'].getint('interval', 60)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code {}".format(rc))

client = mqtt.Client()
client.on_connect = on_connect
client.connect(config['mqtt'].get('hostname', 'homeassistant'),
               config['mqtt'].getint('port', 1883),
               config['mqtt'].getint('timeout', 60))
client.loop_start()

temps = deque((), 3)
humids = deque((), 3)

while True:

    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    if humidity:
        humids.append(humidity)
    if temperature:
        temps.append(temperature)
    changes = temperature and humidity
    print('Data: ', temps, humids)
    if len(humids) >= 2 and len(temps) >= 2 and changes:
        humidity = sorted(humids)[1]
        temperature = sorted(temps)[1]

        entry = {'temperature': round(temperature, decim_digits),
                'humidity': round(humidity, decim_digits)}
        client.publish(topic, json.dumps(entry))
        print('Published.', entry, 'Sleeping ...')

    time.sleep(sleep_time)
