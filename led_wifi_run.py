import network
import time
from machine import Pin

# Wi-Fi設定
ssid='Wi-Fi SSDID'
password='Wi-Fi Password'

# 内蔵LEDの設定(Pico2W除く）
#led=Pin(25, Pin.OUT)#内蔵LEDは25番

# 内蔵LEDの設定(Pico2W）
led= machine.Pin('LED', machine.Pin.OUT)

# Wi-Fiに接続
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# 接続が確立されるまで待機
while not wlan.isconnected():
    print('Connecting...')
    time.sleep(1)

print('Connected, IP address:', wlan.ifconfig()[0])

# Wi-Fi接続が成功したらLEDを点滅させる
while True:
    led.value(1)  # LEDをオンにする
    time.sleep(1)  # 1秒待機
    led.value(0)  # LEDをオフにする
    time.sleep(1)  # 1秒待機
