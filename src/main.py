from lamp import Lamp

# Pins on ESP8266 are d2(4) and d1(5)
lamp = Lamp(pixels_pin=4, pixels_len=30, button_pin=5)
lamp.run()
