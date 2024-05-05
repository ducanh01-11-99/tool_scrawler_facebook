from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class SeleniumUtils:

    @staticmethod
    def click_element(driver: WebDriver, element: WebElement):
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        driver.execute_script("arguments[0].click();", element)

    @staticmethod
    def move_to_element(driver: WebDriver, element: WebElement):
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()




