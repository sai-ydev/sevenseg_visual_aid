#!/usr/bin/python3
"""
    Youtube Susbscriber tracker
"""

import requests
import logging
import serial
import time
import configparser

# config is loaded from config file
# alternatively you may store them as constants in your program
CONFIG_FILE = '/home/pi/youtube_config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

API_KEY = config.get("CREDENTIALS", "API_KEY")
CHANNEL = "UCFIjVWFZ__KhtTXHDJ7vgng"
URL = (
    "https://www.googleapis.com/youtube/v3/channels?part=statistics&id=" + 
    CHANNEL +
    "&key=" +
    API_KEY
)


def serial_write(serial_client, count):
    """
        Write steps to serial port
    """
    message = 'S' + count
    serial_client.write(bytes(message, encoding='utf-8'))

def get_subscriber_count():
    data = None
    try:
        response = requests.get(URL)
    except:
        logging.info("Requests error")

    if response.status_code == 200:
        data = response.json()

    return data["items"][0]["statistics"]["subscriberCount"]

if __name__ == "__main__":
    logging.basicConfig(
        filename='/home/pi/youtube_visualaid.log',
        level=logging.DEBUG,
        format='%(asctime)s %(message)s'
    )
    logging.info("File created")



    with serial.Serial("/dev/ttyACM0", 9600, timeout=0.5) as serial_port:
        # retrieve steps

        count = get_subscriber_count()
        serial_write(serial_port, count)

        logging.info("Subscriber info: " + count)
        current_time = time.time()

        while True:
            # update steps every 15 minutes
            if (time.time() - current_time) > 900:
                count = get_subscriber_count()
                if count >= 0:
                    current_time = time.time()
                    serial_write(serial_port, count)
                    logging.info("Steps: " + str(count))
                else:
                    continue

            serial_write(serial_port, count)
            time.sleep(1)
