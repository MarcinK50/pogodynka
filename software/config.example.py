ssid = 'wifi-ssid'
password = 'wifi-password'
wifi_timeout = 10

server_ip = '192.168.10.208'
server_port = '8080' # default port - 9000

# questdb http basic auth user & password
questdb_user = 'marcin' 
questdb_password = '1a2b3c4d5E'

location_id = 0
lat = '50.552494'
lon = '16.689344'

update_rate = 15 # update rate between measurements in seconds
log_status_ok = 10 # send status OK info to server every 10 measures
max_log_filesize = 10000 # if log filesize exceeds 10000 bytes new file will be created
status_led = True # or False to turn LEDs off