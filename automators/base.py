from abc import ABC, abstractmethod
from selenium.webdriver.remote.webdriver import WebDriver
from bs4 import BeautifulSoup
import time

class BaseAutomator(ABC):
    def __init__(self, driver: WebDriver):
        self.driver = driver

    @abstractmethod
    def navigate(self):
        """Navigate to the target website."""
        pass

    @abstractmethod
    def query(self, text: str):
        """Input the query and submit."""
        pass

    @abstractmethod
    def extract_response(self) -> str:
        """Extract the latest response text."""
        pass
    
    def wait_for_element(self, selector, timeout=10):
        # Basic wait implementation
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def get_soup(self):
        return BeautifulSoup(self.driver.page_source, 'html.parser')
