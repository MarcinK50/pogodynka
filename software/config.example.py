ssid = 'wifi-ssid'
password = 'wifi-password'
wifi_timeout = 10

server_ip = '192.168.10.208'
server_port = '8080' # default port - 9000

# questdb http basic auth user & password
questdb_user = 'marcin' 
questdb_password = '1a2b3c4d5E'

location_id = 0

update_rate = 15

log_status_ok = 10 # send status OK info to server every 10 measures
log_level = 0 #   LOG_LEVEL - 0 - [INF], [WARN] & [ERR]
                #  1 - [WARN] & [ERR]
                #  2 - [ERR]
log_destination = '/' # default - /
max_log_filesize = 10000 # if log filesize exceeds 10000 bytes new file will be created

status_led = True # or False to turn LEDs off