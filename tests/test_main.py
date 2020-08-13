from tests.browser.browser import Browser


def test_web_mail():
    browser = Browser()
    browser.open_url("https://ej2.syncfusion.com/showcase/typescript/webmail/#/home")
    browser.set_window_size(1920, 1080)
    browser.set_window_position(0, 0)

    browser.get("#tree li.e-level-2[data-uid='21']").click()

    browser.get("li.e-level-1[data-uid='SF10205']").click()
    assert browser.get("#sub").text == 'Fletcher Beck'

    browser.get("li.e-level-1[data-uid='SF10202']").click()
    assert browser.get("#sub").text == 'Oscar Mcconnell'

    browser.close()
