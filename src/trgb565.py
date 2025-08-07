from PIL import Image
import io
import pathlib
import sys

# 读取图像文件并转换为RGB565格式
def image_to_rgb565_bytes(file_path, width, height):
	img = Image.open(file_path).convert('RGB').resize((width, height))
	img_bytes = bytearray(width * height * 2) # RGB565每个像素2字节

	for y in range(height):
		for x in range(width):
			r, g, b = img.getpixel((x, y))
			# 将RGB888转换为RGB565
			rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
			img_bytes[(y * width + x) * 2] = rgb565 >> 8 # 高字节
			img_bytes[(y * width + x) * 2 + 1] = rgb565 & 0xFF # 低字节

	return bytes(img_bytes)

# 使用示例
rgb565_data = image_to_rgb565_bytes(sys.argv[1], 32, 16)
pathlib.Path(sys.argv[2]).write_bytes(rgb565_data)