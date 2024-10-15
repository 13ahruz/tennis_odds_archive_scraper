import undetected_chromedriver2 as uc
from undetected_chromedriver2.options import ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import os
import logging
from config.os_config import ROOT_DIR

os.chdir(ROOT_DIR)


class Driver:
    def get_options(self) -> ChromeOptions:
        options = ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Headless options
        options.add_argument("--headless=new")  # Preferred for latest Chrome versions
        # options.headless = True  # Alternatively, use this line instead of the above

        # Additional arguments for better headless performance
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--disable-extensions")

        return options

    def install_driver(self) -> str:
        path = ChromeDriverManager().install().replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver")
        logging.info(f"Installed Driver to {path}")

        os.chmod(path, 0o755)
        return path

    def get_driver(self):
        options = self.get_options()
        # self.driver = uc.Chrome(options=options)
        path = self.install_driver()
        self.driver = uc.Chrome(options=options, driver_executable_path=path)

        self.driver.implicitly_wait(3)

        return self.driver