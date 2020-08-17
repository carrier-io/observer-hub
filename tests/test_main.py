from selene import Config, Browser, have
from selene.support import webdriver
from selenium import webdriver
from tests.browser.browser import Browser as CustomBrowser
from selene.support.shared import browser


def test_web_mail():
    br = CustomBrowser()
    br.open_url("https://ej2.syncfusion.com/showcase/typescript/webmail/#/home")
    br.set_window_size(1920, 1080)
    br.set_window_position(0, 0)

    br.get("#tree li.e-level-2[data-uid='21']").click()

    br.get("li.e-level-1[data-uid='SF10205']").click()
    assert br.get("#sub").text == 'Fletcher Beck'

    br.get("li.e-level-1[data-uid='SF10202']").click()
    assert br.get("#sub").text == 'Oscar Mcconnell'

    br.close()


def test_web_mail_selene():
    options = webdriver.ChromeOptions()
    # options.add_argument('--window-size=1920,1080')
    options.set_capability("version", "83.0")
    options.set_capability("vnc", True)
    driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=options)

    browser = Browser(Config(
        driver=driver,
        # driver=webdriver.Chrome(),
        base_url='https://ej2.syncfusion.com',
        timeout=4,
        window_width=1920,
        window_height=1080))

    browser.open('/showcase/typescript/webmail/#/home')
    browser.element("#tree li.e-level-2[data-uid='21']").click()

    browser.element("li.e-level-1[data-uid='SF10205']").click()
    browser.element("#sub").should(have.exact_text('Fletcher Beck'))

    browser.element("li.e-level-1[data-uid='SF10202']").click()
    browser.element("#sub").should(have.exact_text('Oscar Mcconnell'))

    browser.quit()