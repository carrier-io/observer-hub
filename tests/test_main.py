import os
from uuid import uuid4

import pytest
from selene import Config, Browser, have
from selene.support import webdriver
from selenium import webdriver


@pytest.fixture(scope="session")
def browser():
    options = webdriver.ChromeOptions()
    # options = webdriver.FirefoxOptions()

    options.set_capability("version", "84.0")
    options.set_capability("venv", "DEV")
    options.set_capability("vnc", True)
    options.set_capability("junit_report", "test_report")
    options.set_capability("report_uid", str(uuid4()))
    # options.set_capability("report_uid", "12345")
    options.set_capability("job_name", "DEMO")
    options.set_capability("galloper_url", "http://localhost")
    options.set_capability("galloper_token", os.environ.get('galloper_token'))
    options.set_capability('galloper_project_id', 1)
    options.set_capability('tz', 'Europe/Kiev')

    options.set_capability("jira_url", "http://localhost:8080")
    options.set_capability("jira_project", "DEMO")
    options.set_capability("jira_user", "")
    options.set_capability("jira_password", "123456")

    driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', options=options)

    browser = Browser(Config(
        driver=driver,
        # driver=webdriver.Chrome(),
        base_url='https://ej2.syncfusion.com',
        timeout=4,
        window_width=1920,
        window_height=1080))
    yield browser
    browser.close_current_tab()


def test_web_mail_selene(browser):
    browser.open('/showcase/typescript/webmail/#/home')
    browser.element("#tree li.e-level-2[data-uid='21']").click()

    browser.element("li.e-level-1[data-uid='SF10205']").click()
    browser.element("#sub").should(have.exact_text('Fletcher Beck'))

    browser.element("li.e-level-1[data-uid='SF10202']").click()
    browser.element("#sub").should(have.exact_text('Oscar Mcconnell'))


def test_web_mail_selene2(browser):
    browser.open('/showcase/typescript/webmail/#/home')
    browser.element("#tree li.e-level-2[data-uid='11']").click()

    browser.element("li.e-level-1[data-uid='SF10095']").click()
    browser.element("#sub").should(have.exact_text('Gemma Roberson'))

    browser.element("#tree li.e-level-2[data-uid='12']").click()
    browser.element("li.e-level-1[data-uid='SF10142']").click()
    browser.element("#sub").should(have.exact_text('Elijah Berry'))


def test_web_mail_selene3(browser):
    browser.open('/showcase/typescript/webmail/#/home')
    browser.element("#tree li.e-level-2[data-uid='21']").click()

    browser.element("li.e-level-1[data-uid='SF10208']").click()
    browser.element("#sub").should(have.exact_text('Zena Osborn'))

    browser.element("li.e-level-1[data-uid='SF10203']").click()
    browser.element("#sub").should(have.exact_text('Quynn Carr'))
