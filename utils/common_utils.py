import random
import time
from selenium.webdriver.remote.webelement import WebElement
from typing import Callable, List, Optional, Tuple

class CommonUtils:
    @staticmethod
    def sleep_random_in_range(a: float, b: float) -> float:
        sleep_time = random.uniform(a, b)
        time.sleep(sleep_time)
        return sleep_time
    

class ElementIterator:
    def __init__(self, element_list: List[WebElement]):
        self.element_list = element_list
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.element_list):
            raise StopIteration

        post = self.element_list[self.index]
        self.index += 1
        return post
    def _len(self):
        return len(self.element_list)
    def update(self, element_list: List[WebElement]):
        self.element_list = element_list