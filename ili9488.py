from machine import Pin, SPI

class ili9488():
	def __init__(self, cs=10, dc=14, width=480, height=320):
		self.hspi = SPI(1, 40000000)
		self.cs = Pin(cs, Pin.OUT)
		self.dc = Pin(dc, Pin.OUT)
		self.width = width
		self.height = height

		for command, data in (
			(0xe0, b'\x00\x07\x0C\x05\x13\x09\x36\xAA\x46\x09\x10\x0D\x1A\x1E\x1F'),
			(0xe1, b'\x00\x20\x23\x04\x10\x06\x37\x56\x49\x04\x0C\x0A\x33\x37\x0F'),
			(0xc0, b'\x0E\x0E'),
			(0xc1, b'\x44'),
			(0xc5, b'\x00\x40\x00\x40'),
			(0x36, b'\xE8'), # MADCTL Landscape RGB888
			(0x3a, b'\x66'),
			(0xb0, b'\x00'),
			(0xb1, b'\xA0\x11'),
			(0xb4, b'\x02'),
			(0xb6, b'\x02\x02\x3B'),
			(0xb7, b'\x06'),
			(0xf7, b'\xA9\x51\x2C\x82'),
			(0x11, b'\x80\x78'),  # Exit Sleep then delay 0x78 (120ms)
			(0x29, b'\x80\x78')): # Display on then delay 0x78 (120ms)
			self.send_spi(bytearray([command]), False)
			self.send_spi(data, True) 
	
	def send_spi(self, data, is_data=True):
		self.dc.value(is_data)
		self.cs.value(0)
		self.hspi.write(data)
		self.cs.value(1)
		
	#do be aware this fuction swaps the width and height
	def set_window(self, x0=0, y0=0, width=320, height=240):	      
		x1=x0+width-1
		y1=y0+height-1	
		self.width = width
		self.height = height
		self.send_spi(bytearray([0x2A]),False)            # set Column addr command		
		self.send_spi(ustruct.pack(">HH", x0, x1), True)  # x_end 
		self.send_spi(bytearray([0x2B]),False)            # set Row addr command        
		self.send_spi(ustruct.pack(">HH", y0, y1), True)  # y_end        
		self.send_spi(bytearray([0x2C]),False)            # set to write to RAM		

	#chunk size can be increased for faster wiring to the screen at cost of RAM
	def load_image(self, image_file, chunk_size=1024):
		self.set_window(0,0,320,240)  
		BMP_file = open(image_file , "rb")
		data = BMP_file.read(54)
		data = BMP_file.read(chunk_size)
		while len(data) > 0:
			self.send_spi(data, True)
			data = BMP_file.read(chunk_size)
		BMP_file.close()

	def restore_image(self, box, image_file):     
		chunk_size = box[2] * 2     
		self.set_window(box[0], box[1], box[2], box[3])    
		BMP_file = open(image_file , "rb")     
		self.dc.value(1)     
		self.cs.value(0)

		for looping in range (box[3]): 	  
			BMP_file.seek(54 + box[0] * 2 + (box[1] + looping) * 320*2, 0)      
			data = BMP_file.read(chunk_size)      
			self.hspi.write(data)   

		BMP_file.close()
		self.cs.value(1)

	def fill(self, color, x=0, y=0, width=0, height=0):
		if width == 0: width = self.width
		if height == 0: height = self.height
		
		self.set_window(x, y, width, height)
		self.send_spi(color * width * height, True)

