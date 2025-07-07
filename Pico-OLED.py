from machine import Pin, SPI
import framebuf
import time
import ustruct

DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

class OLED_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 128
        self.height = 64

        self.rotate = 180  # only 0 and 180

        self.cs = Pin(CS, Pin.OUT)
        self.rst = Pin(RST, Pin.OUT)

        self.cs(1)
        self.spi = SPI(1)
        self.spi = SPI(1, 2000_000)
        self.spi = SPI(1, 20000_000, polarity=0, phase=0,
                       sck=Pin(SCK), mosi=Pin(MOSI), miso=None)
        self.dc = Pin(DC, Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer,
                         self.width,
                         self.height,
                         framebuf.MONO_HMSB)
        self.init_display()

        self.white = 0xffff
        self.balck = 0x0000

    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        """Initialize dispaly"""
        self.rst(1)
        time.sleep(0.001)
        self.rst(0)
        time.sleep(0.01)
        self.rst(1)

        self.write_cmd(0xAE)  # turn off OLED display

        self.write_cmd(0x00)  # set lower column address
        self.write_cmd(0x10)  # set higher column address

        self.write_cmd(0xB0)  # set page address

        self.write_cmd(0xdc)  # et display start line
        self.write_cmd(0x00)
        self.write_cmd(0x81)  # contract control
        self.write_cmd(0x6f)  # 128
        self.write_cmd(0x21)  # Set Memory addressing mode (0x20/0x21) #
        if self.rotate == 0:
            self.write_cmd(0xa0)  # set segment remap
        elif self.rotate == 180:
            self.write_cmd(0xa1)
        self.write_cmd(0xc0)  # Com scan direction
        self.write_cmd(0xa4)  # Disable Entire Display On (0xA4/0xA5)

        self.write_cmd(0xa6)  # normal / reverse
        self.write_cmd(0xa8)  # multiplex ratio
        self.write_cmd(0x3f)  # duty = 1/64

        self.write_cmd(0xd3)  # set display offset
        self.write_cmd(0x60)

        self.write_cmd(0xd5)  # set osc division
        self.write_cmd(0x41)

        self.write_cmd(0xd9)  # set pre-charge period
        self.write_cmd(0x22)

        self.write_cmd(0xdb)  # set vcomh
        self.write_cmd(0x35)

        self.write_cmd(0xad)  # set charge pump enable
        self.write_cmd(0x8a)  # Set DC-DC enable (a=0:disable; a=1:enable)
        self.write_cmd(0XAF)

    def show(self):
        self.write_cmd(0xb0)
        for page in range(0, 64):
            if self.rotate == 0:
                self.column = 63 - page  # set segment remap
            elif self.rotate == 180:
                self.column = page

            self.write_cmd(0x00 + (self.column & 0x0f))
            self.write_cmd(0x10 + (self.column >> 4))
            for num in range(0, 16):
                self.write_data(self.buffer[page*16+num])

if __name__=='__main__':

    OLED = OLED_1inch3()

    OLED.fill(0x0000)
    keyA = Pin(15, Pin.IN, Pin.PULL_UP)
    keyB = Pin(17, Pin.IN, Pin.PULL_UP)

    # BMP画像の読み込み関数（1bit BMP専用）
    def load_bmp(filename):
        with open(filename, 'rb') as f:
            if f.read(2) != b'BM':
                raise ValueError("Not a BMP file")

            f.seek(10)
            offset = ustruct.unpack('<I', f.read(4))[0]
            print(f'offset={offset}')
            f.seek(18)
            width = ustruct.unpack('<I', f.read(4))[0]
            height = ustruct.unpack('<I', f.read(4))[0]
            print(f'width={width}, height={height}')

            f.seek(28)
            bpp = ustruct.unpack('<H', f.read(2))[0]
            if bpp != 1:
                raise ValueError("Only 1-bit BMP supported")

            f.seek(offset)
            row_size = ((width + 31) // 32) * 4  # 1bit BMPの1行のバイト数（4バイト境界）
            print(f'row_size={row_size}')
            buf = bytearray(width * height // 8)

            for y in range(height):
                row = f.read(row_size)
                for x in range(width // 8):
                    buf[(height - 1 - y) * (width // 8) + x] = row[x]

            return framebuf.FrameBuffer(buf, width, height, framebuf.MONO_HLSB)

    # QRコード読み込み
    bmp = load_bmp("QR.bmp")

    # 8x8ドット絵の読み込み
    apple = load_bmp("apple.bmp")
    onigiri = load_bmp("onigiri.bmp")
    pine = load_bmp("pineapple.bmp")

    showQR = False
    
    while (1):
        if keyA.value() == 0:
            showQR = 1
            print("A")

        if (keyB.value() == 0):
            showQR ^= 1
            print("B")

        OLED.fill(0x0000)

        if showQR:
            OLED.text("Go to", 0, 10, OLED.white)
            OLED.text("HomePage", 0, 20, OLED.white)
            OLED.blit(apple, 0, 56)
            OLED.blit(onigiri, 8, 56)
            OLED.blit(pine, 16, 56)
            OLED.blit(bmp, 64, 0)
        else:
            OLED.text("X@tsu_kunn", 1, 10, OLED.white)
            OLED.text("Mixi2@tsu_kunn", 1, 27, OLED.white)
            OLED.text("Key1 to View QR", 1, 44, OLED.white)

        OLED.show()

    time.sleep(1)
    OLED.fill(0xFFFF)
