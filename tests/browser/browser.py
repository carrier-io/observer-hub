from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class Browser(object):

    def __init__(self):
        # self.driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--window-size=1920,1080')
        # options = webdriver.FirefoxOptions()
        self.driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def current_url(self):
        return self.driver.current_url

    def open_url(self, url):
        self.driver.get(url)

    def set_window_size(self, width, height):
        self.driver.set_window_size(width, height)

    def get(self, css_locator):
        return self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_locator)))

    def session_id(self):
        return self.driver.session_id
