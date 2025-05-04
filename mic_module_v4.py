import numpy as np
import time
import smbus
from rpi_ws281x import PixelStrip, Color

LED_ROWS = 8
LED_COLS = 32
LED_COUNT = LED_ROWS * LED_COLS
LED_PIN = 18 #GPIO 18 = PWM

strip = PixelStrip(LED_COUNT, LED_PIN, brightness=40)
strip.begin()

address = 0x48
bus = smbus.SMBus(1)
bus.write_byte(address, 0x42)
time.sleep(0.1)

NUM_SAMPLES = 256
SAMPLE_DELAY = 0.0001  # 10kHz sample rate
FS = 1.0 / SAMPLE_DELAY

def read_pcf8591(channel=2):
    bus.write_byte(address, 0x40 | channel)
    bus.read_byte(address)
    return bus.read_byte(address)

def collect_samples():
    samples = []
    for _ in range(NUM_SAMPLES):
        val = read_pcf8591()
        samples.append(val - 128)
        time.sleep(SAMPLE_DELAY)
    return np.array(samples)

# def frequency_bands(fft_vals, num_bands=LED_COLS):
#     band_size = len(fft_vals) // num_bands
#     bands = []
#     for i in range(num_bands):
#         band_power = np.sum(np.abs(fft_vals[i*band_size:(i+1)*band_size]))
#         bands.append(band_power)
#     return bands

def frequency_to_color(val, max_val):
    if max_val == 0:
        return Color(0, 0, 0)
    
    normalized = map_val(val, 0, max_val, 0, 255)
    
    if normalized < 85:
        # Red to Yellow
        return Color(normalized * 3, 255 - normalized * 3, 0)
    elif normalized < 170:
        # Yellow to Green
        return Color(255 - (normalized - 85) * 3, 255, 0)
    elif normalized < 255:
        # Green to Blue
        return Color(0, 255 - (normalized - 170) * 3, normalized * 3)
    else:
        return Color(0, 0, 0)

def frequency_bands(fft_vals, num_bands=8):
    band_size = len(fft_vals) // num_bands
    bands = []
    for i in range(num_bands):
        band_power = np.sum(np.abs(fft_vals[i*band_size:(i+1)*band_size]))
        bands.append(band_power)
    return bands

def map_val(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def led_index(row, col):
    if col % 2 == 0:
        return col * LED_ROWS + row
    else:
        return col * LED_ROWS + (LED_ROWS - 1 - row)

# def display_spectrum(bands):
#     max_val = max(bands) if max(bands) > 0 else 1
#     for col, val in enumerate(bands):
#         height = map_val(val, 0, max_val, 0, LED_ROWS)
#         for row in range(LED_ROWS):
#             idx = led_index(row, col)
#             if row < height:
#                 color = Color(0, map_val(row, 0, LED_ROWS, 0, 255), 255 - map_val(row, 0, LED_ROWS, 0, 255))
#                 strip.setPixelColor(idx, color)
#             else:
#                 strip.setPixelColor(idx, Color(0, 0, 0)) 
#     strip.show()

def display_spectrum(bands):
    max_val = max(bands) if max(bands) > 0 else 1
    for band, val in enumerate(bands): 
        height = map_val(val, 0, max_val, 0, LED_ROWS)
        
        # spread 8 bands across 32 columns
        start_col = band * 4
        for col_offset in range(4):
            col = start_col + col_offset
            if col >= LED_COLS:
                break
            
            color = frequency_to_color(val, max_val)
            
            for row in range(LED_ROWS):
                idx = led_index(row, col)
                if row < height:
                    strip.setPixelColor(idx, color)
                else:
                    strip.setPixelColor(idx, Color(0, 0, 0))
    strip.show()

def loop():
    while True:
        # samples = collect_samples()
        # fft_vals = np.fft.fft(samples)
        # fft_vals = fft_vals[:NUM_SAMPLES // 2]
        # bands = frequency_bands(fft_vals, LED_COLS)
        # display_spectrum(bands)
        
        # extract frequencies and separate into 8 bands
        samples = collect_samples()
        fft_vals = np.fft.fft(samples)
        fft_vals = fft_vals[:NUM_SAMPLES // 2]
        bands = frequency_bands(fft_vals, num_bands=8)
        display_spectrum(bands)

def clear_matrix():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == "__main__":
    try:
        loop()
    except KeyboardInterrupt:
        clear_matrix()