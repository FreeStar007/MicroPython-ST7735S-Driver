from machine import Pin, SPI, PWM
import time
import framebuf
from micropython import const
from time import sleep_ms

# ST7735S命令定义
_SWRESET = const(0x01)
_SLPOUT = const(0x11)
_DISPON = const(0x29)
_CASET = const(0x2A)
_RASET = const(0x2B)
_RAMWR = const(0x2C)
_MADCTL = const(0x36)
_COLMOD = const(0x3A)

# 颜色模式（RGB565）
COLOR_MODE_16BIT = const(0x05)
RED = 0xF800      # 红色
GREEN = 0x07E0    # 绿色
BLUE = 0x001F     # 蓝色
WHITE = 0xFFFF    # 白色
BLACK = 0x0000    # 黑色

class ST7735S(framebuf.FrameBuffer):
    def __init__(self, spi, width, height, dc, rst, cs, bl, rotate=0, xo=0, yo=0):
        # 初始化引脚
        self.dc = Pin(dc, Pin.OUT)
        self.rst = Pin(rst, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)
        self.bl = PWM(Pin(bl), freq=1000, duty=512)  # 背光PWM初始化（50%亮度）
        
        # 屏幕参数
        self.width = width
        self.height = height
        self.rotate = rotate  # 旋转方向：0-3
        self.spi = spi
        self.xo = xo
        self.yo = yo
        
        # 初始化显示缓冲区（RGB565格式）
        self.buffer = bytearray(width * height * 2)
        super().__init__(self.buffer, width, height, framebuf.RGB565)
        
        # 硬件复位
        self.reset()
        self.init_display()
    
    def reset(self):
        """硬件复位"""
        self.rst(0)
        time.sleep_ms(10)
        self.rst(1)
        time.sleep_ms(100)
    
    def init_display(self):
        """初始化屏幕配置"""
        self._write_command(_SWRESET)  # 软件复位
        time.sleep_ms(150)
        self._write_command(_SLPOUT)   # 唤醒屏幕
        time.sleep_ms(100)
        
        # 设置颜色模式（16位RGB565）
        self._write_command(_COLMOD, bytearray([COLOR_MODE_16BIT]))
        
        # 设置显示方向（根据rotate参数调整）
        madctl = 0x00
        if self.rotate == 1:
            madctl = 0x60  # 90度旋转
        elif self.rotate == 2:
            madctl = 0xC0  # 180度旋转
        elif self.rotate == 3:
            madctl = 0xA0  # 270度旋转
        self._write_command(_MADCTL, bytearray([madctl]))
        
        self._write_command(_DISPON)  # 开启显示
        time.sleep_ms(100)
    
    def _write_command(self, cmd, data=None):
        """发送命令或数据到屏幕"""
        self.cs(0)
        self.dc(0)  # 命令模式
        self.spi.write(bytearray([cmd]))
        if data is not None:
            self.dc(1)  # 数据模式
            self.spi.write(data)
        self.cs(1)
    
    def set_window(self, x0, y0, x1, y1):
        """设置显示窗口区域"""
        x0 = x0 + self.xo
        x1 = x1 + self.xo
        y0 = y0 + self.yo
        y1 = y1 + self.yo
        self._write_command(_CASET, bytearray([0x00, x0, 0x00, x1]))  # 水平偏移补偿
        self._write_command(_RASET, bytearray([0x00, y0, 0x00, y1]))  # 垂直偏移补偿
        self._write_command(_RAMWR)
    
    def show(self):
        """将缓冲区内容刷新到屏幕"""
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.cs(0)
        self.dc(1)
        self.spi.write(self.buffer)
        self.cs(1)
    
    def backlight(self, brightness):
        """调节背光亮度（0-255）"""
        self.bl.duty(brightness * 1023 // 255)
    
    def draw_image(self, img, imgw, imgh, x=0, y=0, format=framebuf.RGB565):
        '''在framebuf上,从(x,y)处绘制字节数据组成的图像，每个像素为1字节的灰度值或2个字节rgb565,
        超出屏幕范围的图像被忽略'''
        fbuf = framebuf.FrameBuffer(bytearray(img), imgw, imgh, format) #定义img对应的framebuf
        if format == framebuf.GS8:
            pbuf = bytearray(256 * 2)
            for i in range(256):
                t = i >> 3  #灰度值除8，变成5位数
                pbuf[i * 2], pbuf[i * 2 + 1] = ((t << 3) | (t >> 3)), ((t << 5) | t)       #灰度转为rgb565格式
            palette = framebuf.FrameBuffer(pbuf, 256, 1, framebuf.RGB565) #定义灰度值的调色板
            self.blit(fbuf, x, y, -1, palette) #在framebuf上绘制img
        elif format == framebuf.RGB565:
            self.blit(fbuf, x, y)
        else:
            print('Only GRAYSCALE/GS8 and RGB565 are supported!')

    def draw_pixel(self, x, y, color):
        """绘制单个像素点"""
        self.pixel(x, y, color)

    def draw_line(self, x1, y1, x2, y2, color):
        """绘制直线"""
        self.line(x1, y1, x2, y2, color)

    def draw_rect(self, x, y, w, h, color, fill=False):
        """绘制矩形（可选填充）"""
        self.rect(x, y, w, h, color, fill)

    def draw_circle(self, x, y, r, color, fill=False):
        """绘制圆形（可选填充）"""
        for dy in range(-r, r + 1):
            dx = int((r ** 2 - dy ** 2) ** 0.5)
            if fill:
                self.hline(x - dx, y + dy, 2 * dx + 1, color)
            else:
                self.pixel(x + dx, y + dy, color)
                self.pixel(x - dx, y + dy, color)
                
    def draw_text(self, text, x, y, fontDB, c=BLACK, bc=WHITE, alpha=True):
        """在framebuf上,从左上角(x,y)处不换行绘制汉字或因为字符,需要调用show()显示。
        fontDB:模块gbk中定义的获取字模数据的对象，gbk.font16x16()
        c:字体颜色
        bc: 背景色
        alpha:背景是否透明""" 
        #定义汉字RGB565格式的背景、前景色调色板
        palette = framebuf.FrameBuffer(bytearray([bc & 0xFF,(bc >> 8) & 0xFF, c & 0xFF,(c >> 8) & 0xFF]), 2, 1, framebuf.RGB565)     
        for ch in text:
            w, h, fbm = fontDB.get(ch) #取得字模的宽、高、位图信息bytearray                      
#             if w == 0 or x + w > self.width or y + h > self.height:
#                 break  #超出屏幕不绘制            
            fbuf=framebuf.FrameBuffer(fbm, w, h, framebuf.MONO_HLSB)#定义字体的framebuffer
            self.blit(fbuf, x, y, bc if alpha else -1, palette) #在framebuf上绘制汉字                 
            x += w
            
    def sleep(self):
        """进入睡眠模式"""
        self._write(0x28)  # 关闭显示
        self._write(0x10)  # 进入睡眠
        if self.bl is not None:
            self.backlight(0)

    def wakeup(self):
        """唤醒屏幕"""
        self._write(0x11)  # 退出睡眠
        sleep_ms(120)
        self._write(0x29)  # 开启显示
        if self.bl is not None:
            self.backlight(128)
            