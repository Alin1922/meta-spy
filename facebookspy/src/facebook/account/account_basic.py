from typing import List, Dict
from ...config import Config
from selenium.webdriver.common.by import By
from ..facebook_base import BaseFacebookScraper
from ...repository import (
    person_repository,
    work_education_repository,
    family_member_repository,
    place_repository,
)

from ...logs import Logs
from rich import print as rprint
import re
from dateutil.parser import parse

logs = Logs()


class AccountBasic(BaseFacebookScraper):
    """
    Scrape user's personal information
    """

    def __init__(self, user_id) -> None:
        super().__init__(user_id, base_url=f"https://www.facebook.com/{user_id}")
        self.success = False

    def extract_full_name(self) -> str | None:
        """Extract full name from homepage"""
        data = None
        try:
            self._driver.get(self._base_url)
            fullname_element = self._driver.find_element(
                By.CSS_SELECTOR, "h1.x1heor9g.x1qlqyl8.x1pd3egz.x1a2a7pz"
            )
            data = fullname_element.text.strip()

        except Exception as e:
            logs.log_error(f"Error occurred while extracting full name: {e}")

        return data

    def extract_work_and_education(self) -> List[Dict[str, str]]:
        """Return employment and education history"""

        extracted_work_data = []
        try:
            self._driver.get(f"{self._base_url}/{Config.WORK_AND_EDUCATION_URL}")

            work_entries = self._driver.find_elements(
                By.CSS_SELECTOR,
                "div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.x1nhvcw1.x1qjc9v5.xozqiw3.x1q0g3np.xexx8yu.xykv574.xbmpl8g.x4cne27.xifccgj.xs83m0k",
            )
            for entry in work_entries:
                owner_element = entry.find_element(By.XPATH, ".//span[@dir='auto']")
                owner = owner_element.text.strip()

                if owner.startswith("http") or owner.startswith("www"):
                    work_entry_data = {"name": owner}
                else:
                    work_entry_data = {"name": owner}

                extracted_work_data.append(work_entry_data)

        except Exception as e:
            logs.log_error(f"Error extracting work data: {e}")

        return extracted_work_data

    def extract_places(self) -> List[Dict[str, str]]:
        """Return history of places"""
        places = []
        try:
            self._driver.get(f"{self._base_url}/{Config.PLACES_URL}")

            div_elements = self._driver.find_elements(
                By.CSS_SELECTOR, "div.x13faqbe.x78zum5"
            )

            for div_element in div_elements:
                name_element = div_element.find_element(
                    By.CSS_SELECTOR, "a[class*='x1i10hfl']"
                )
                name = name_element.text.strip()

                date_element = div_element.find_element(
                    By.CSS_SELECTOR, "div span[class*='xi81zsa']"
                )
                date = date_element.text.strip()

                places.append({"name": name, "date": date})

        except Exception as e:
            logs.log_error(f"Error extracting localization data: {e}")

        return places

    def extract_contact_data(self) -> List[Dict[str, str]]:
        """Return phone number and email address"""
        data = []
        try:
            self._driver.get(f"{self._base_url}/{Config.CONTACT_URL}")

            main_div = self._driver.find_element(
                By.CSS_SELECTOR, "div.xyamay9.xqmdsaz.x1gan7if.x1swvt13"
            )
            span_elements = main_div.find_elements(
                By.CSS_SELECTOR,
                "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1lliihq.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.xudqn12.x3x7a5m.x6prxxf.xvq8zen.xo1l8bm.xzsf02u.x1yc453h[dir='auto']",
            )

            scraped_data = {}

            for span_element in span_elements:
                text = span_element.text

                # Checking for phone number
                phone_number_match = re.search(r"\b\d{3} \d{3} \d{3}\b", text)
                if phone_number_match:
                    scraped_data["phone_number"] = phone_number_match.group()

                # Checking for email address
                email_match = re.search(
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
                )
                if email_match:
                    scraped_data["email"] = email_match.group()

            data.append(scraped_data)

        except Exception as e:
            logs.log_error(f"Error while extracting person data: {e}")

        return data

    def extract_family(self) -> List[Dict[str, str]]:
        """Return family members"""
        data = []
        try:
            self._driver.get(f"{self._base_url}/{Config.FAMILY_URL}")

            elements = self._driver.find_elements(By.CSS_SELECTOR, "div.x1hq5gj4")

            for element in elements:
                name_element = element.find_element(
                    By.CSS_SELECTOR,
                    "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1lliihq.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.xudqn12.x3x7a5m.x6prxxf.xvq8zen.xo1l8bm.xzsf02u a",
                )
                name = name_element.text
                profile_url = name_element.get_attribute("href")
                relationship_element = element.find_element(
                    By.CSS_SELECTOR, "span.xi81zsa.x1nxh6w3.x1sibtaa"
                )
                relationship = relationship_element.text

                data.append(
                    {"name": name, "relationship": relationship, "url": profile_url}
                )
        except Exception as e:
            logs.log_error(f"Error extracting family data: {e}")

        return data

    @property
    def is_pipeline_successful(self) -> bool:
        """Check if pipeline is successful"""
        return self.success

    def work_and_education_pipeline(self) -> None:
        """
        Pipeline to run extract work and education data
        """
        try:
            rprint("[bold]Step 1 of 3 - Load cookies[/bold]")
            self._load_cookies()

            rprint("[bold]Step 2 of 3 - Refresh driver[/bold]")
            self._driver.refresh()

            if not person_repository.person_exists(self._user_id):
                person_repository.create_person(self._user_id)

            person_id = person_repository.get_person(self._user_id).id

            rprint("[bold]Step 3 of 3 - Extract work and education data[/bold]")
            scraped_data = self.extract_work_and_education()
            rprint(scraped_data)

            rprint(
                "[bold red]Don't close the app![/bold red] Saving scraped data to database, it can take a while!"
            )

            for data in scraped_data:
                if not work_education_repository.work_and_education_exists(
                    data["name"], person_id
                ):
                    work_education_repository.create_work_and_education(
                        data["name"], person_id
                    )

            self._driver.quit()
            self.success = True

        except Exception as e:
            logs.log_error(f"Error running pipeline: {e}")
            rprint(f"An error occurred {e}")

    def localization_pipeline(self) -> None:
        """
        Pipeline to return localization data
        """
        try:
            rprint("[bold]Step 1 of 4 - Load cookies[/bold]")
            self._load_cookies()

            rprint("[bold]Step 2 of 4 - Refresh driver[/bold]")
            self._driver.refresh()

            rprint("[bold]Step 3 of 4 - Extract full name[/bold]")

            if not person_repository.person_exists(self._user_id):
                person_repository.create_person(self._user_id)

            person_id = person_repository.get_person(self._user_id).id

            rprint("[bold]Step 4 of 4 - Extract localization data[/bold]")
            places = self.extract_places()
            rprint(places)

            rprint(
                "[bold red]Don't close the app![/bold red] Saving scraped data to database, it can take a while!"
            )

            for data in places:
                if not place_repository.places_exists(
                    data["name"], data["date"], person_id
                ):
                    place_repository.create_places(
                        data["name"], data["date"], person_id
                    )

            self._driver.quit()
            self.success = True

        except Exception as e:
            logs.log_error(f"Error running pipeline: {e}")
            rprint(f"An error occurred {e}")

    def family_member_pipeline(self) -> None:
        """
        Pipeline to extract family members data
        """
        try:
            rprint("[bold]Step 1 of 3 - Load cookies[/bold]")
            self._load_cookies()

            rprint("[bold]Step 2 of 3 - Refresh driver[/bold]")
            self._driver.refresh()

            if not person_repository.person_exists(self._user_id):
                person_repository.create_person(self._user_id)

            person_id = person_repository.get_person(self._user_id).id

            rprint("[bold]Step 3 of 3 - Extract family members[/bold]")
            family_members = self.extract_family()
            rprint(family_members)

            rprint(
                "[bold red]Don't close the app![/bold red] Saving scraped data to database, it can take a while!"
            )

            for member in family_members:
                if not family_member_repository.family_member_exists(
                    person_id, member["name"]
                ):
                    family_member_repository.create_family_member(
                        member["name"],
                        member["relationship"],
                        member["url"],
                        person_id,
                    )

            self._driver.quit()
            self.success = True

        except Exception as e:
            logs.log_error(f"Error running pipeline: {e}")
            rprint(f"An Error occurred {e}")

    def contact_pipeline(self) -> None:
        """
        Pipeline to extract phone number and email
        """
        try:
            rprint("[bold]Step 1 of 3 - Load cookies[/bold]")
            self._load_cookies()

            rprint("[bold]Step 2 of 3 - Refresh driver[/bold]")
            self._driver.refresh()

            rprint("[bold]Step 3 of 3 - Extract contact data[/bold]")
            scraped_data = self.extract_contact_data()
            rprint(scraped_data)

            rprint(
                "[bold red]Don't close the app![/bold red] Saving scraped data to database, it can take a while!"
            )

            for data in scraped_data:
                person_repository.create_person(
                    self._user_id,
                    phone_number=data["phone_number"],
                    email=data["email"],
                )

            self._driver.quit()
            self.success = True

        except Exception as e:
            logs.log_error(f"Error running pipeline: {e}")
            rprint(f"An error occurred {e}")

    def full_name_pipeline(self) -> None:
        """
        Pipeline to extract full name data
        """
        try:
            rprint("[bold]Step 1 of 3 - Load cookies[/bold]")
            self._load_cookies()

            rprint("[bold]Step 2 of 3 - Refresh driver[/bold]")
            self._driver.refresh()

            rprint("[bold]Step 3 of 3 - Extract full name[/bold]")
            full_name = self.extract_full_name()
            rprint(full_name)

            rprint(
                "[bold red]Don't close the app![/bold red] Saving scraped data to database, it can take a while!"
            )

            person_repository.create_person(self._user_id, full_name)

            self._driver.quit()
            self.success = True

        except Exception as e:
            logs.log_error(f"Error running pipeline: {e}")
            rprint(f"An error occurred {e}")
