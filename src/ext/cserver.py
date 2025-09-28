import usocket
import ujson
import utime

class CServer:
    
    def __init__(self, init=True):
        self._server = usocket.usocket(usocket.AF_INET, usocket.SOCK_STREAM)
        self._server.setsockopt(usocket.SOL_usocket, usocket.SO_REUSEADDR, 1)
        self._pipes = []
        if init:
        	self.config()
        
    def config(self, ip="0.0.0.0", port=7777, listens=4, retry_utimes=4) -> None:
        utimes = 0
        while (utimes := utimes + 1) <= retry_utimes:
            try:
                server = self._server
                server.bind((ip, port, ))     
                server.listen(listens)
                break
            except Exception:
                utime.sleep(2)
        
    def accept(self) -> None:
        pipe, address = self._server.accept()
        self._pipes.append({
            "pipe": pipe,
            "address": address
        })
    
    def send(self, original: str | bytes, number: int, types="ujson", codes="utf-8") -> None:
        pipe = self._pipes[numbet]["pipe"]
        if types == "text":
            original = str(original)
        elif types == "ujson":
            original = ujson.dumps(original)
        elif types == "base64":
            original = ubinascii.b2a_base64(original)
        elif types == "original":
            pipe.sendall(original)
            return
        else:
            raise Exception(f"Unknown type {types}.")
            
        pipe.sendall(original.encode(codes))
    
    def recv(self, size: int, number: int, types="ujson", codes="utf-8") -> str | bytes:
        original = self._pipes[number]["pipe"].recv(size)
        data = original.decode(codes)
        if types == "text":
            return str(data)
        elif types == "ujson":
            return ujson.loads(data)
        elif types == "base64":
            return ubinascii.a2b_base64(data)
        elif types == "original":
            return original
        else:
            raise Exception(f"Unknown type {types}.")
            
    def close_pipe(self, number: int) -> None:
        pipes = self._pipes
        pipes[number]["pipe"].close()
        del pipes[number]
        
    def close_pipes(self) -> None:
        for pipe in self._pipes:
            pipe["pipe"].close()
            
        self._pipes = []
            
    def close_server(self) -> None:
        if self._pipes:
            self.close_pipes()
            
        self._server.close()
        self.config()
    