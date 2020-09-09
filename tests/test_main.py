from uuid import uuid4

import pytest
from selene import Config, Browser, have
from selene.support import webdriver
from selenium import webdriver


@pytest.fixture(scope="session")
def browser():
    options = webdriver.ChromeOptions()
    # options = webdriver.FirefoxOptions()

    options.set_capability("version", "83.0")
    options.set_capability("venv", "QA")
    options.set_capability("vnc", True)
    options.set_capability("junit_report", "test_report")
    options.set_capability("report_uid", str(uuid4()))
    # options.set_capability("report_uid", "12345")

    options.set_capability("galloper_url", "http://localhost")
    options.set_capability("galloper_token", "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIxNjQ5ODY1Ny04OTYyLTRiZmUtYjY2OS0yZDQyYjEyMzQ0ODQifQ.eyJqdGkiOiI5ZjVjYzRlOS1kMzFlLTQwZGYtYTZlMy03ZDBmY2VjNWRkMjciLCJleHAiOjAsIm5iZiI6MCwiaWF0IjoxNTk5NjQ4NTg3LCJpc3MiOiJodHRwOi8vMTkyLjE2OC4wLjExNi9hdXRoL3JlYWxtcy9jYXJyaWVyIiwiYXVkIjoiaHR0cDovLzE5Mi4xNjguMC4xMTYvYXV0aC9yZWFsbXMvY2FycmllciIsInN1YiI6IjhhOWEzY2VjLTVlMTMtNDJjZC04NzM2LWEwZTk3NTk4ZDg2ZSIsInR5cCI6Ik9mZmxpbmUiLCJhenAiOiJjYXJyaWVyLW9pZGMiLCJub25jZSI6IlRvTEFZZk9LM2F1YjNWdFQiLCJhdXRoX3RpbWUiOjAsInNlc3Npb25fc3RhdGUiOiI3MzAzZWJkNC00MmYwLTRiMDktYTFmZS0wMjk5MWFlYThmZmMiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIG9mZmxpbmVfYWNjZXNzIGVtYWlsIHByb2ZpbGUifQ.GfY1HS0YyrB1EjCkl9B8vDu7m6meT_DAq-ya0GT1UP4")
    options.set_capability('galloper_project_id', 1)
    options.set_capability('tz', 'Europe/Kiev')

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
    browser.element("#tree li.e-level-2[data-uid='21']").click()

    browser.element("li.e-level-1[data-uid='SF10205']").click()
    browser.element("#sub").should(have.exact_text('Fletcher Beck'))

    browser.element("li.e-level-1[data-uid='SF10202']").click()
    browser.element("#sub").should(have.exact_text('Oscar Mcconnell'))
