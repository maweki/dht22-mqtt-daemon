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

temps = deque((), sleep_time)
humids = deque((), sleep_time)

next_pub = 0

while True:

    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    if humidity:
        humids.append(humidity)
    if temperature:
        temps.append(temperature)

    if len(humids) > sleep_time / 2 and len(temps) > sleep_time / 2 and time.time() >= next_pub:
        humidity = sorted(humids)[sleep_time / 2]
        temperature = sorted(temps)[sleep_time / 2]

        entry = {'temperature': round(temperature, decim_digits),
                'humidity': round(humidity, decim_digits)}
        client.publish(topic, json.dumps(entry))
        print('Published.', entry, 'Sleeping ...')
        next_pub = time.time() + sleep_time

    time.sleep(1)
