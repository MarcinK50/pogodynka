import utime, network, dht, mrequests as requests
from machine import Pin, UART
from pms5003 import PMS5003
import config
import ubinascii
import os
import ntptime, time
import gc
from sys import exit

LOG_LEVEL = config.log_level
LOG_STATUS_OK = config.log_status_ok
LOG_DESTINATION = config.log_destination
MAX_LOG_FILESIZE = config.max_log_filesize

SSID = config.ssid
PASSWORD = config.password
QUESTDB_USER = config.questdb_user
QUESTDB_PASSWORD = config.questdb_password

ID = config.location_id
IP, PORT = config.server_ip, config.server_port
UPDATE_RATE = config.update_rate
url = f"http://{IP}:{PORT}/exec"

power_led = Pin(10, Pin.OUT)
wifi_led = Pin(11, Pin.OUT)
data_led = Pin(12, Pin.OUT)
power_led.value(0)
wifi_led.value(0)
data_led.value(0)

sensor = dht.DHT22(Pin(16))
pms5003 = PMS5003(
    uart=UART(1, tx=Pin(8), rx=Pin(9), baudrate=9600),
    pin_enable=Pin(3),
    pin_reset=Pin(2),
    mode="active"
)

if config.status_led: power_led.value(1)

def connect_to_wifi(ssid,password):
    if LOG_LEVEL <= 0:
        print('[INF] SSID: ', ssid)
        print('[INF] Pass: ', password)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if LOG_LEVEL <= 0:    
        mac = ubinascii.hexlify(wlan.config('mac'),':').decode()
        print('[INF] MAC: ', mac)
    
    wlan.connect(SSID, PASSWORD)
    connection_timeout = config.wifi_timeout
    while connection_timeout > 0:
        if wlan.status() >= 3:
            break
        connection_timeout -= 1
        utime.sleep(1)
    
    if wlan.status() != 3:
        log(2, 'Wi-Fi Connection error!')
        raise RuntimeError('Connection error')
    else:
        try:
            ntptime.host = "0.pool.ntp.org"
            ntptime.settime()
        except:
            ntptime.host = "1.pool.ntp.org"
            ntptime.settime()
        log(0, 'Wi-Fi Connection successful!')
        if config.status_led: wifi_led.value(1)
        network_info = wlan.ifconfig()
        if LOG_LEVEL <= 0:
            print('[INF] IP:', network_info[0])
            log(0, f'IP: {network_info[0]}')
       
def get_temperature():
    try:
        data = sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        if LOG_LEVEL <= 0:
            log(0, f'Reading DHT22 succes! Temperature: {temp} Humidity: {hum}')
        return [temp, hum]
    except:
        log(2, 'No data from DHT22')
        return ['NULL', 'NULL']

def get_pollution():
    try:
        pms = pms5003.read()
        pm1 = pms.data[0]
        pm25 = pms.data[1]
        pm10 = pms.data[2]
        if LOG_LEVEL <= 0:
            log(0, f'Reading PMS5003 succes! PM1: {pm1} PM2.5: {pm25} PM10: {pm10}')
        return [pm1, pm25, pm10]
    except:
        log(2, 'No data from PMS5003')
        return ['NULL', 'NULL', 'NULL']
    
### Logging codes:
### 0 - [INF]   
### 1 - [WARN]
### 2 - [ERR]
def log(code, message):
    timestamp = int(f'{time.time()}000000') # TODO: to convert timestamp from NTP to nanoseconds format, this is very sketchy, make it better
    
    log_filename = 'log-0.txt'
    log_files = []
    directory = os.listdir(LOG_DESTINATION)
    for f in directory:
        if f.startswith('log'):
            if os.stat(f)[6] > MAX_LOG_FILESIZE:
                log_number = 0
                while True:
                    if f'log-{log_number}.txt' in directory and os.stat(f'log-{log_number}.txt')[6] > MAX_LOG_FILESIZE:
                        log_files.append(log_number)
                        log_number += 1
                    else: 
                        log_filename = f'log-{log_number}.txt'
                        break
            else: log_filename = f
    log_files = list(set(log_files))
    
    stat = os.statvfs("/")
    size = stat[1] * stat[2]
    free = stat[0] * stat[3]
    used = size - free
    
    if used/size*100 > 80:
        for log_number in log_files:
            os.remove(f'log-{log_number}.txt')
            if LOG_LEVEL <= 1:
                log(1, 'Memory usage exceeded, cleaning up old logs')
    
    try:
        file = open(f'{LOG_DESTINATION}/{log_filename}', "a")
    except:
        print('[ERR] Configuration error - log location is unreachable - create directory!')
        exit()
    tm = time.localtime()
    st = f'{tm[0]:04d}-{tm[1]:02d}-{tm[2]:02d} {tm[3]:02d}-{tm[4]:02d}-{tm[5]:02d}'    
    file.write(f'{st}, {code}, {message}\n')
    file.close()
       
    query = f"INSERT INTO log (id,timestamp,code,message) VALUES ({ID},{timestamp},{str(code)},'{str(message)}')"
    log_url = url+"?query="+url_encode(query)
    try:
        requests.get(url=log_url, auth=(QUESTDB_USER, QUESTDB_PASSWORD))
        return 0
    except Exception as error:
        if str(error) == "Unsupported types for __add__: 'str', 'bytes'": return 0
        else:
            print("[LOG] General error: ",str(error))
            return 1

def url_encode(string):
    encoded_string = ''
    for char in string:
        if char.isalpha() or char.isdigit() or char in '-._~':
            encoded_string += char
        else:
            encoded_string += '%' + '{:02X}'.format(ord(char))
    return encoded_string

def send_results(ID,temperature, humidity, pm1, pm25, pm10):
    gc.collect()
    query = f"INSERT INTO sensors(id,temperature,humidity,pm1,pm25,pm10,timestamp) VALUES('{ID}',{str(temperature)},{str(humidity)},{str(pm1)},{str(pm25)},{str(pm10)},{time.time()}000000)"
    full_url = url+"?query="+url_encode(query)    
    
    if LOG_LEVEL <= 0:
        log(0, f"Executing query: {full_url}")
    
    try:
        requests.get(url=full_url, auth=(QUESTDB_USER, QUESTDB_PASSWORD))
        return 0
    except Exception as error:
        if str(error) == "Unsupported types for __add__: 'str', 'bytes'": return 0
        else:
            print("General error: ",str(error))
            return 1

def main():
    connect_to_wifi(SSID,PASSWORD)
    status_timer = 0
    while True:
        temperature, humidity = get_temperature()
        pm1, pm25, pm10 = get_pollution()
        response = send_results(ID,temperature, humidity, pm1, pm25, pm10)
        while response != 0:
            response = send_results(ID,temperature, humidity, pm1, pm25, pm10)
            utime.sleep(1)
        if config.status_led:
            data_led.value(1)
            utime.sleep(1)
            data_led.value(0)
        
        if status_timer == LOG_STATUS_OK:
            log(0, 'OK')
            status_timer = 0
        else: status_timer += 1
        utime.sleep(UPDATE_RATE)

main()

