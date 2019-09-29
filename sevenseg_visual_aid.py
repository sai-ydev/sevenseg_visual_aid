#!/usr/bin/python3
"""
    Visual aid to track personal fitness
"""

import datetime
import fitbit
import logging
import serial
import time
import configparser

# config is loaded from config file
# alternatively you may store them as constants in your program
CONFIG_FILE = '/home/pi/config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

CONSUMER_KEY = config.get("APP", "CONSUMER_KEY")
CONSUMER_SECRET = config.get("APP", "CONSUMER_SECRET")
REFRESH_TOKEN = config.get("USER", "REFRESH_TOKEN")
ACCESS_TOKEN = config.get("USER", "ACCESS_TOKEN")


def update_tokens(token):

    if (
        token['access_token'] != ACCESS_TOKEN or
        token['refresh_token'] != REFRESH_TOKEN
    ):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        config.set("USER", "REFRESH_TOKEN", token['refresh_token'])
        config.set("USER", "ACCESS_TOKEN", token['access_token'])

        with open(CONFIG_FILE, "w") as config_file:
            config.write(config_file)


def get_steps(client):
    """
        Return the steps logged
    """
    num_steps = 0

    try:
        now = datetime.datetime.now()
        end_time = now.strftime("%H:%M")
        response = client.intraday_time_series(
            'activities/steps',
            detail_level='15min',
            start_time="00:00",
            end_time=end_time
        )
    except Exception as error:
        print(error)
    else:
        str_steps = response['activities-steps'][0]['value']
        print(str_steps)
        try:
            num_steps = int(str_steps)
        except ValueError:
            return -1
    return num_steps


def get_goal(client):
    """
        Determine Daily step goal
    """
    goal_steps = 0

    try:
        response = client.activities_daily_goal()
    except Exception as error:
        print(error)
    else:
        str_goal = response['goals']['steps']
        try:
            goal_steps = int(str_goal)
        except ValueError:
            return -1

    return goal_steps


def serial_write(serial_client, goal, steps):
    """
        Write steps to serial port
    """
    if steps >= 0:
        display_value = goal - steps
        message = 'S' + str(display_value)
        serial_client.write(bytes(message, encoding='utf-8'))

if __name__ == "__main__":
    logging.basicConfig(
        filename='/home/pi/sevenseg_visualaid.log',
        level=logging.DEBUG,
        format='%(asctime)s %(message)s'
    )
    logging.info("File created")
    client = fitbit.Fitbit(
        CONSUMER_KEY,
        CONSUMER_SECRET,
        access_token=ACCESS_TOKEN,
        refresh_token=REFRESH_TOKEN,
        refresh_cb=update_tokens
    )

    current_time = time.time()

    with serial.Serial("/dev/ttyACM0", 9600, timeout=0.5) as serial_port:
        # retrieve steps
        steps = get_steps(client)
        goal = get_goal(client)
        serial_write(serial_port, goal, steps)

        logging.info("Goal: " + str(goal) + "Steps: " + str(steps))

        while True:
            # update steps every 15 minutes
            if (time.time() - current_time) > 900:
                steps = get_steps(client)
                # refresh LEDs only if step check was successful
                if steps >= 0:
                    current_time = time.time()
                    serial_write(serial_port, goal, steps)
                    logging.info("Steps: " + str(steps))
                else:
                    continue

            serial_write(serial_port, goal, steps)
            time.sleep(1)
