import pytest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

@pytest.fixture(scope="module")
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

def test_login(driver):
    driver.get("http://localhost:3000/")
    assert "Login" in driver.title
    username_input = driver.find_element_by_name("username")
    password_input = driver.find_element_by_name("password")
    submit_button = driver.find_element_by_tag_name("button")

    username_input.send_keys("johndoe")
    password_input.send_keys("secret")
    submit_button.click()

    assert "Dashboard" in driver.title

def test_register(driver):
    driver.get("http://localhost:3000/register")
    assert "Register" in driver.title
    username_input = driver.find_element_by_name("username")
    password_input = driver.find_element_by_name("password")
    submit_button = driver.find_element_by_tag_name("button")

    username_input.send_keys("newuser")
    password_input.send_keys("newpass")
    submit_button.click()

    assert "Login" in driver.title