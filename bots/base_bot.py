# bots/base_bot.py

class BaseBot:
    def __init__(self, config: dict):
        self.config = config

    def run(self):
        raise NotImplementedError("Bot must implement run()")
