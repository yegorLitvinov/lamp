from array import array
import uasyncio as asyncio
from machine import Pin
from neopixel import NeoPixel

from button import AsyncButton
from utils import randint


COLOR_BLACK = (0, 0, 0)


class Lamp:
    INTENSIVITY_MIN = 50
    INTENSIVITY_MAX = 1000

    def __init__(self, pixels_pin: int, pixels_len: int, button_pin: int) -> None:
        self._pixels_pin = Pin(pixels_pin, Pin.OUT)
        self.pixels = NeoPixel(self._pixels_pin, pixels_len)
        self._button_pin = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        self.button = AsyncButton(
            pin=self._button_pin,
            click_callback=self.next_effect,
            double_click_callback=self.previous_effect,
            press_callback=self.change_intensivity,
        )

        self.effect_index = 0
        self.intensivity = 100
        self.intensivity_step = 20
        self.loop = asyncio.get_event_loop()
        self.effects = [
            self.random_blink_factory(index=0),
            self.single_color_factory(color=(255, 0, 0), index=1),
            self.single_color_factory(color=(0, 255, 0), index=2),
            self.single_color_factory(color=(0, 0, 255), index=3),
            self.single_color_factory(color=(255, 0, 255), index=4),
            self.single_color_factory(color=(180, 100, 53), index=5),
        ]

    def run(self):
        self.loop.create_task(self.button.run())
        self.add_effect()
        self.loop.run_forever()

    def add_effect(self):
        self.loop.create_task(self.effects[self.effect_index]())

    def _change_effect_index(self):
        self.effect_index = self.effect_index % len(self.effects)

    def change_intensivity(self, finished=False):
        if finished:
            self.intensivity_step *= -1
            return
        intensivity = self.intensivity + self.intensivity_step
        if self.INTENSIVITY_MIN < intensivity < self.INTENSIVITY_MAX:
            self.intensivity = intensivity

    def next_effect(self):
        self.effect_index += 1
        self._change_effect_index()
        self.add_effect()

    def previous_effect(self):
        self.effect_index -= 1
        self._change_effect_index()
        self.add_effect()

    def apply_intensivity(self, color):
        for i in range(3):
            color[i] = color[i] * self.intensivity // self.INTENSIVITY_MAX

    def fill_black(self):
        self.pixels.fill(COLOR_BLACK)
        self.pixels.write()

    def single_color_factory(self, color: tuple, index: int):
        async def single_color():
            prev_intensivity = None
            while True:
                await asyncio.sleep_ms(50)
                if index != self.effect_index:
                    return
                if prev_intensivity != self.intensivity:
                    prev_intensivity = self.intensivity
                    new_color = list(color)
                    self.apply_intensivity(new_color)
                    self.pixels.fill(new_color)
                    self.pixels.write()
        return single_color

    def random_blink_factory(self, index: int):
        FADE_ITER_STEPS = 33
        FACTOR = 100  # Don't use floating point
        lamp = self

        class PixelState:
            def __init__(self):
                self.target_color = array("I", COLOR_BLACK)
                self.current_color = array("I", COLOR_BLACK)
                self.pixel_color = array("I", COLOR_BLACK)
                self.steps = array("I", COLOR_BLACK)
                self.current_step = 0
                self.wait_loops = 0
                self.reset()

            def reset(self):
                for i in range(3):
                    self.target_color[i] = randint(255) * FACTOR
                    self.current_color[i] = 0
                    self.pixel_color[i] = 0
                    self.steps[i] = self.target_color[i] // FADE_ITER_STEPS
                self.current_step = 0
                self.wait_loops = randint(200)

            def next(self):
                if self.wait_loops > 0:
                    self.wait_loops -= 1
                    return
                if self.current_step == FADE_ITER_STEPS:
                    self.steps = [-s for s in self.steps]
                elif self.current_step == 2 * FADE_ITER_STEPS:
                    self.reset()
                    return
                for i in range(3):
                    self.current_color[i] += self.steps[i]
                    self.pixel_color[i] = self.current_color[i] // FACTOR
                lamp.apply_intensivity(self.pixel_color)
                self.current_step += 1

        states = [PixelState() for _ in range(self.pixels.n)]

        async def blink() -> None:
            self.fill_black()
            while True:
                await asyncio.sleep_ms(10)
                if index != self.effect_index:
                    self.fill_black()
                    return
                for i in range(self.pixels.n):
                    states[i].next()
                    self.pixels[i] = states[i].pixel_color
                self.pixels.write()


        return blink
