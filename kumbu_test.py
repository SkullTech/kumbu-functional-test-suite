from selenium import webdriver
import time
import pytest
from tkinter import Tk
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

devmode = True
draft = pytest.mark.skip(reason="Completed writing this method") if devmode else pytest.mark.foo


class KumbuTestingBase:
    @pytest.fixture(scope='module')
    def webdriver(self):
        driver = webdriver.Firefox()
        yield driver
        driver.quit()

    @pytest.fixture(scope='function')
    def driver(self, webdriver):
        yield webdriver
        webdriver.delete_all_cookies()
        webdriver.get('https://www.google.com')

    @staticmethod
    def verify_flash_message(driver, message):
        flashes = driver.find_elements_by_id('flash-messages')
        assert len(flashes) != 0 and message in flashes[0].text
        flashes[0].find_element_by_class_name('close-button').click()

    @pytest.fixture(scope='class')
    def sign_in(self, driver):
        driver.get('https://staging.getkumbu.com')
        driver.find_element_by_name('inputEmail').send_keys('kumbutest@mailinator.com')
        driver.find_element_by_name('inputPassword').send_keys('kumbuiscool')
        driver.find_element_by_id('login-submit').click()

    @staticmethod
    def count_tiles(driver):
        prior = 0
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)
            current = len(WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                                                               'div.item.columns'))))
            if current != prior:
                prior = current
            else:
                break
        return current


@draft
class TestLoginExistingUser(KumbuTestingBase):
    def test_l001(self, driver):
        self.sign_in(driver)

        links = driver.find_elements_by_class_name('profile-link')
        assert len(links) != 0 and 'Kumbu Test' in links[0].text
        links[0].click()

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'profile-modal')))

        driver.find_element_by_class_name('profile-tab-signout').click()
        assert 'https://staging.getkumbu.com/login' in driver.current_url

    def test_l002(self, driver):
        driver.get('https://staging.getkumbu.com')
        driver.find_element_by_name('inputEmail').send_keys('kumbutest@mailinator.com')
        driver.find_element_by_name('inputPassword').send_keys('kumbuis​not​cool')
        driver.find_element_by_id('login-submit').click()
        self.verify_flash_message(driver, 'Invalid email or password')

    def test_l003(self, driver):
        driver.get('https://staging.getkumbu.com')
        driver.find_element_by_class_name('password-link').click()
        assert 'https://staging.getkumbu.com/reset' in driver.current_url

        driver.find_element_by_name('inputEmail').send_keys('kumbutest@mailinator.com')
        driver.find_element_by_id('login-submit').click()
        self.verify_flash_message(driver, 'An email to reset your password has been sent')
        time.sleep(5)

        driver.get('https://www.mailinator.com/v2/inbox.jsp?zone=public&query=kumbutest#')
        element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Reset your Kumbu password")]')))
        element.click()

        frame = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'msg_body')))
        driver.switch_to.frame(frame)
        button = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'mcnButton')))
        button.click()

        driver.switch_to.window(driver.window_handles[-1])
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, 'inputPassword')))
        driver.find_element_by_name('inputPassword').send_keys('kumbuiscool')
        driver.find_element_by_name('confirmPassword').send_keys('kumbuiscool')
        driver.find_element_by_id('login-submit').click()

        self.verify_flash_message(driver, 'Your password has been successfully changed')
        self.test_l001(driver)


@draft
class TestWebappSharing(KumbuTestingBase):
    @pytest.fixture(scope='class')
    def shared_collection(self, webdriver):
        self.sign_in(webdriver)
        memories = 'https://staging.getkumbu.com/collection/C03e19a24-23f9-403c-8e96-22b79b23b741/'
        webdriver.get(memories)
        webdriver.find_element_by_id('shareCollection').click()
        WebDriverWait(webdriver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'share-modal')))
        webdriver.find_element_by_class_name('collection-share-link-copy').click()
        webdriver.delete_all_cookies()
        webdriver.get('https://www.google.com')

        return Tk().clipboard_get()

    def test_s001(self, driver, shared_collection):
        self.sign_in(driver)
        memories = 'https://staging.getkumbu.com/collection/C03e19a24-23f9-403c-8e96-22b79b23b741/'
        driver.get(memories)
        number = int(driver.find_element_by_class_name('collection-item-number').text)

        driver.get('https://staging.getkumbu.com/logout')
        driver.get(shared_collection)

        assert number == self.count_tiles(driver)

    def test_s002(self, driver, shared_collection):
        driver.get(shared_collection)
        driver.find_element_by_class_name('item-thumbnail').click()
        back = driver.find_element_by_id('quit-nav')
        assert 'Back to Memories' in back.text and len(driver.find_elements_by_css_selector('div.picture-item > img')) != 0
        back.click()
        self.count_tiles(driver)
        assert len(driver.find_elements_by_css_selector('div.item.columns')) != 0

    def test_s003(self, driver, shared_collection):
        self.sign_in(driver)
        memories = 'https://staging.getkumbu.com/collection/C03e19a24-23f9-403c-8e96-22b79b23b741/'
        driver.get(memories)
        driver.find_element_by_id('shareCollection').click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'share-modal')))
        driver.find_element_by_id('removeShareCollection').click()
        driver.get(shared_collection)
        assert len(driver.find_elements_by_class_name('content-404')) != 0


@draft
class TestWebappMemories(KumbuTestingBase):
    def test_m001(self, driver):
        self.sign_in(driver)

        driver.find_element_by_class_name('souvenirs-menu-link').click()
        count = self.count_tiles(driver)

    def test_m002(self, driver):
        self.sign_in(driver)

        driver.find_element_by_class_name('souvenirs-menu-link').click()
        items = [link.get_attribute('data-kumbu-item-id') for link in driver.find_elements_by_css_selector('div.item.columns > a')]
        elem = driver.find_element_by_css_selector('ul.dropdown.menu > li')
        hover = ActionChains(driver).move_to_element(elem)
        sort = driver.find_element_by_class_name('sort-by-title')
        hover.perform()
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CLASS_NAME, 'sort-by-title')))
        sort.click()
        time.sleep(5)
        sorted_items = [link.get_attribute('data-kumbu-item-id') for link in driver.find_elements_by_css_selector('div.item.columns > a')]
        smaller = len(min(items, sorted_items))
        assert items[:smaller] != sorted_items[:smaller]

    def test_m003(self, driver):
        self.sign_in(driver)
        driver.find_element_by_class_name('souvenirs-menu-link').click()

        overlays = driver.find_elements_by_class_name('item-overlay')[:2]
        for overlay in overlays:
            hover = ActionChains(driver).move_to_element(overlay)
            hover.perform()
            overlay.find_element_by_css_selector('span.item-selector').click()
        driver.find_element_by_class_name('delete-selected-items').click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'delete-modal')))
        driver.find_element_by_class_name('delete-item-list').click()


class TestWebappCollections(KumbuTestingBase):
    @staticmethod
    def upload_memory(driver, path):
        time.sleep(2)

        file_input = driver.find_element_by_css_selector('input.dz-hidden-input')
        driver.execute_script(
            'arguments[0].style = ""; arguments[0].style.display = "block"; arguments[0].style.visibility = "visible";',
            file_input)
        file_input.send_keys('C:\\Users\\Sumit\\Pictures\\geralt.jpg')
        driver.find_element_by_id('confirmUpload').click()
        time.sleep(20)

    @draft
    def test_c001(self, driver):
        self.sign_in(driver)

        driver.find_element_by_css_selector('div.secondary-navigation > div > div > ul > li > a').click()
        title = driver.find_element_by_id('collection-title')
        title.click()
        title.send_keys(Keys.CONTROL + 'a')
        title.send_keys('Collection ​for ​Test ​TEST_NUMBER')
        title.send_keys(Keys.ENTER)
        assert '0' in driver.find_element_by_class_name('collection-item-number').text
        driver.find_element_by_class_name('back-collections').click()
        driver.refresh()
        assert 'Collection for Test TEST_NUMBER' in driver.find_element_by_css_selector('div.collection.columns').text

    @draft
    def test_c002(self, driver):
        self.sign_in(driver)

        driver.find_element_by_class_name('collection-title-wrapper').click()
        driver.find_element_by_id('uploadFilesEmptyCollection').click()
        self.upload_memory(driver, 'C:\\Users\\Sumit\\Pictures\\geralt.jpg')
        thumbnail = driver.find_element_by_css_selector('a.item-thumbnail > img').get_attribute('src')
        assert 'https://staging.getkumbu.com/item/thumbnail/' in thumbnail

    @draft
    def test_c003(self, driver):
        self.sign_in(driver)

        driver.get('https://staging.getkumbu.com/collection/C9c3a5b54-f05f-4c1f-8687-775869820def/')
        driver.find_element_by_id('uploadFiles').click()
        self.upload_memory(driver, 'C:\\Users\\Sumit\\Pictures\\geralt.jpg')
        thumbnails = driver.find_elements_by_css_selector('a.item-thumbnail > img')
        assert len(thumbnails) == 2
        for thumbnail in thumbnails:
            assert 'https://staging.getkumbu.com/item/thumbnail/' in thumbnail.get_attribute('src')

    @draft
    def test_c004(self, driver):
        self.sign_in(driver)

        driver.get('https://staging.getkumbu.com/collection/C9c3a5b54-f05f-4c1f-8687-775869820def/')
        cover = driver.find_element_by_css_selector('div.collection-navigation-wrapper').get_attribute('data-kumbu-background')[18:]
        thumbnails = [thumb.get_attribute('src')[44:-38] for thumb in driver.find_elements_by_css_selector('a.item-thumbnail > img')]
        assert cover in thumbnails


class TestWebappOnboardingNewUsers(KumbuTestingBase):
    def test_n001(self, driver):
        driver.get('https://staging.getkumbu.com/logout')
        driver.find_element_by_css_selector('div.bottom-links > span > a').click()

        driver.find_element_by_name('inputName').send_keys('Kumbu Test 5')
        driver.find_element_by_name('inputEmail').send_keys('kumbutest5@mailinator.com')
        driver.find_element_by_name('inputPassword').send_keys('kumbu kumbu kumbu')
        driver.find_element_by_id('signup-submit').click()