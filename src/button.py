import uasyncio as asyncio


class AsyncButton:
    CHECK_INTERVAL_MS = 50
    MAX_CHECKS = 10

    def __init__(self, pin, click_callback, double_click_callback=None, press_callback=None):
        self.pin = pin
        self.click_callback = click_callback
        self.double_click_callback = double_click_callback if double_click_callback else lambda: None
        self.press_callback = press_callback if press_callback else lambda _: None
        # press
        # release
        self.history = [0 for i in range(self.MAX_CHECKS)]
        self.successes = 0
        self.checks_count = 0

    def _count_history_clicks(self):
        # first click is always preset, because it initiates the process
        clicks = 1
        for i in range(1, self.MAX_CHECKS):
            if self.history[i] and not self.history[i-1]:
                clicks += 1
        return clicks

    async def run(self):
        self.successes = 0
        self.checks_count = 0
        while True:
            await asyncio.sleep_ms(self.CHECK_INTERVAL_MS)
            self.successes += self.pin.value()
            if self.successes:
                self.history[self.checks_count] = self.pin.value()
                self.checks_count += 1
            if self.checks_count >= self.MAX_CHECKS:
                clicks = self._count_history_clicks()
                if all(self.history):
                    while self.pin.value():
                        self.press_callback(False)
                        await asyncio.sleep_ms(50)
                    self.press_callback(True)
                elif clicks == 1:
                    self.click_callback()
                elif clicks == 2:
                    self.double_click_callback()
                self.successes = 0
                self.checks_count = 0
            # print("Checks: {}, Successes: {}".format(self.checks_count, self.successes))
