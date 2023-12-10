import requests
import json, time
import math, statistics

from boltiot import Bolt
import conf

# alert
def send_alert(sensor_value):
    message = ''
    if sensor_value <= min_temp:
        message = "Alert! \nSensor value is low 🥶 \nCurrent sensor value is " + str(sensor_value)
    elif sensor_value >= max_temp:
        message = "Alert! \nSensor value is high 🥵 \nCurrent sensor value is " + str(sensor_value)
    resp = send_telegram_msg(message)

# Z - score analysis
def compute_bounds(history_data,frame_size,factor):
    
    if len(history_data) < frame_size :
        return None

    if len(history_data) > frame_size :
        del history_data[0:len(history_data)-frame_size]
        
    Mn = statistics.mean(history_data)
    Variance = 0

    for data in history_data :
        Variance += math.pow((data-Mn),2)
    
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size-1]+Zn
    Low_bound = history_data[frame_size-1]-Zn
    
    return [High_bound,Low_bound]

# message
def send_telegram_msg(message):
    url = "https://api.telegram.org/" + conf.TELEGRAM_BOT_ID + "/sendMessage"
    data = { 
        "chat_id": conf.TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.request(
            "POST",
            url,
            params=data
        )
        telegram_data = json.loads(response.text)
        return telegram_data["ok"]
    except Exception as e:
        print("An error occurred in sending the alert message via Telegram")
        print(e)
        return False

# values
mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
history_data = []

min_temp = conf.MIN_TEMP
max_temp = conf.MAX_TEMP

# code
while True:
    response = mybolt.analogRead('A0')
    data = json.loads(response)

    if data['success'] != 1:
        print("Error retriving data:" + data['value'])
        time.sleep(10)
        continue

    sensor_value=0
    # temperature threshold
    try:
        sensor_value = int(data['value'])
        print('Sensor value is', sensor_value)
    
    except Exception as e:
        print ("Error",e)

    # if sensor_value <= min_temp or sensor_value >= max_temp:
        # send_alert(sensor_value)

    # z-score analysis
    bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR)

    if not bound:
        required_data_count=conf.FRAME_SIZE-len(history_data)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue

    try:
        average = (bound[0] + bound[1]) / 2
        
        if sensor_value > average :
            print("Sudden rise in temperature.")
            send_telegram_msg("Alert! ⚠️ \nSomeone has opened the fridge door")

        history_data.append(sensor_value)

    except Exception as e:
        print ("Error",e)

    time.sleep(10)