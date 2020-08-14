import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


class Browser(object):

    def __init__(self):
        # self.driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--window-size=1920,1080')
        options.set_capability("version", "83.0")
        # options = webdriver.FirefoxOptions()
        self.driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def current_url(self):
        return self.driver.current_url

    def open_url(self, url):
        self.driver.get(url)

    def set_window_size(self, width, height):
        self.driver.set_window_size(width, height)

    def set_window_position(self, x, y):
        self.driver.set_window_position(x, y)

    def get(self, css_locator):
        # return self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_locator)))
        return Element(self.driver, css_locator)

    def session_id(self):
        return self.driver.session_id

    def close(self):
        self.driver.quit()


class Element(object):

    def __init__(self, driver, locator):
        self.driver = driver
        self.locator = locator

    def _find(self):
        finish_time = time.time() + 4
        while True:
            try:
                element = self.driver.find_element(by=By.CSS_SELECTOR, value=self.locator)
                if element.is_displayed():
                    return element
                else:
                    raise Exception()
            except Exception as reason:
                if time.time() > finish_time:
                    raise TimeoutError(reason)
                time.sleep(0.4)

    def click(self):
        self._find().click()

    @property
    def text(self):
        return self._find().text
