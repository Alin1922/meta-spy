from .instagram_base import BaseInstagramScraper
from ..config import Config
from ..logs import Logs
from ..facebook.scroll import scroll_page_callback
from selenium.webdriver.common.by import By
from rich import print as rprint

logs = Logs()


class ProfileScraper(BaseInstagramScraper):
    def __init__(self, user_id: str) -> None:
        super().__init__(user_id, base_url=f"https://www.instagram.com/{user_id}/")
        self.success = False

    def _load_cookies_and_refresh_driver(self) -> None:
        """Load cookies and refresh driver"""
        self._load_cookies()
        self._driver.refresh()

    @property
    def is_pipeline_successful(self) -> bool:
        return self.success

    def extract_images(self):
        extracted_image_urls = []
        try:

            def extract_callback(driver):
                div_element = self._driver.find_elemebt(By.CLASS_NAME, "x1iyjqo2")
                img_elements = div_element.find_elements(
                    By.CSS_SELECTOR,
                    "img.x5yr21d.xu96u03.x10l6tqk.x13vifvy.x87ps6o.xh8yej3",
                )
                for img_element in img_elements:
                    src_attribute = img_element.get_attribute("src")
                    if src_attribute and src_attribute not in extracted_image_urls:
                        rprint(f"Extracted image URL: {src_attribute}")
                        extracted_image_urls.append(src_attribute)

        except Exception as e:
            logs.log_error(f"An  error occurred while extracting images: {e}")

        return extracted_image_urls

    def pipeline_images(self) -> None:
        try:
            rprint(f"[bold]Step 1 of 2 - Load cookies")
            self._load_cookies_and_refresh_driver()

            rprint(f"[bold]Step 2 of 2 - Extract images")
            image_urls = self.extract_images()

        except Exception as e:
            logs.log_error(f"An error occurred: {e}")
            rprint(f"An error occurred {e}")
