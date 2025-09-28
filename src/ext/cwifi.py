import network
import utime
import ubinascii
import ujson
import cserver

class CWIFI:
    
    def __init__(self, ap=network.WLAN(network.AP_IF), sta=network.WLAN(network.STA_IF)):
        self._ap = ap
        self._sta = sta
        self._wifis = {}
        self._sta_on()
    
    def ap_mode(self, *args, **kwargs) -> None:
        self._ap_on()
        self._ap.config(*args, **kwargs)
        
    def serve(self, essid="ESP32WIFI", password="", rcache=True, wcache=True) -> bool:
        if rcache and self._cache():
            return True
        
        self.scans()
        self.ap_mode(essid=essid, password=password)
        server = cserver.CServer()
        server.config()
        server.accept()
        server.send(self._wifis, -1)
        data = server.recv(1024 * 8, -1)
        server.close_server()
        if self.connect(data):
            if wcache:
                with open("./wifi_cache.json", "w") as w:
                    ujson.dump(data, w)
                    
            return True
        else:
            return False
    
    def connect(self, configs: dict[str, int], retry_times=32) -> bool:
        self._sta_on()
        sta = self._sta
        times = 0
        while not sta.isconnected() and (times := times + 1) <= retry_times:
            try:
                sta.connect(configs["ssid"], configs["password"])
            except Exception:
                utime.sleep(1)
                
        return True
    
    def scans(self) -> None:
        self._sta_on()
        self._wifis = [{
            "ssid": wifi[0].decode(),
            "bssid": ubinascii.hexlify(wifi[1]).decode(),
            "channel": wifi[2],
            "rssi": wifi[3],
            "authmode": wifi[4],
            "hidden": wifi[5]
        } for wifi in self._sta.scan()]
        
    def _cache(self) -> None:
        try:
            with open("/wifi_cache.json") as r:
                configs = ujson.load(r)
                
        except Exception:
            return False
        
        return self.connect(configs)
            
    def _ap_on(self) -> None:
        self._ap.active(True)
        self._sta.active(False)

    def _sta_on(self) -> None:
        self._sta.active(True)
        self._ap.active(False)
        
    @staticmethod
    def generate_client(ip="192.168.4.1", port=7777, codes="utf-8") -> str:
        client_codes = f"""import socket
import json

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("{ip}", {port}, ))
wifis = json.loads(client.recv(1024 * 64).decode("{codes}"))
for index, wifi in enumerate(wifis):
    print(f"================\\n序号：{{index}}\\n名称：{{wifi["ssid"]}}\\n设备地址：{{wifi["bssid"]}}\\n频段：{{wifi["channel"]}}\\n信号强度：{{wifi["rssi"]}}\\n鉴权模式：{{wifi["authmode"]}}\\n是否隐藏：{{"是" if wifi["hidden"] else "否"}}")
    while True:
        i = int(input("请选择一个网络（序号）："))
        if i < 0 or i > len(wifis):
            print(f"无效序号: {{i}}")
            continue
    
        if not wifis[i]["authmode"] == "open":
            password = input("该网络需要鉴权密码（输入re重选网络）：")
            if password == "re":
                continue
        else:
            password = None
        
        client.send(json.dumps({{
            "ssid": wifis[i]["ssid"],
            "password": password
        }}).encode())
        client.close()
        break
        """
        return client_codes
