import logging
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep

from src.settings import Settings

settings = Settings()

logger = logging.getLogger(__name__)


class Authenticator:
    """Class that handles the authentication to the CROUS website and returns a WebDriver object that is authenticated."""

    def __init__(self, email: str, password: str, delay: int = 2):
        self.email = email
        self.password = password
        self.delay = delay

    def authenticate_driver(self, driver: WebDriver) -> None:
        """Authenticates the given WebDriver object to the CROUS website."""

        logger.info("Authenticating to the CROUS website...")

        sleep(self.delay)

        # Step 1: Go to the login page.
        # We go through the "trouverunlogement" discovery/connect endpoint (as a
        # real user would, by clicking "Connexion" on the housing site) instead
        # of hitting the bare MesServices login URL directly: the bare URL now
        # redirects straight back to the MesServices homepage without the
        # correct session/redirect parameters attached.
        discovery_url = "https://trouverunlogement.lescrous.fr/mse/discovery/connect"
        logger.info(f"Going to the login page via: {discovery_url}")
        driver.get(discovery_url)
        sleep(self.delay)

        # Step 2: choose the correct authentication method
        logger.info("Choosing the correct authentication method")
        mse_connect_button = self._find_mse_login_button(driver)
        # mse_connect_button.click() # somehow doesn't work. We simulate a click instead :
        driver.execute_script("arguments[0].click();", mse_connect_button)
        sleep(self.delay)

        # Step 3: Input credentials and submit
        logger.info("Inputting credentials")
        username_input = self._find_element(
            driver,
            [
                (By.NAME, "j_username"),
                (By.NAME, "username"),
                (By.NAME, "email"),
                (By.NAME, "login"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[type='text']"),
            ],
            "username field",
        )
        password_input = self._find_element(
            driver,
            [
                (By.NAME, "j_password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ],
            "password field",
        )

        username_input.send_keys(self.email)
        password_input.send_keys(self.password)

        logger.info("Submitting the form")
        password_input.send_keys(Keys.RETURN)

        sleep(self.delay)

        # Step 4: Validate the rules
        self._validate_rules(driver)

        # Step 5: Force update the auth status
        driver.get("https://trouverunlogement.lescrous.fr/mse/discovery/connect")

        # Done
        logger.info("Successfully authenticated to the CROUS website")

    def _find_element(self, driver: WebDriver, strategies: list, description: str):
        """Tries several (By, value) strategies in order and returns the first
        VISIBLE match (ignoring hidden decoy/autofill fields that share the
        same name/type as the real, visible field).
        Logs a snippet of the page source if none match, to help diagnose site changes.
        """
        last_error: Exception | None = None
        for by, value in strategies:
            try:
                candidates = driver.find_elements(by, value)
                for candidate in candidates:
                    try:
                        if candidate.is_displayed():
                            logger.info(
                                f"Found {description} using strategy: {by}={value!r}"
                            )
                            return candidate
                    except Exception:  # noqa: BLE001
                        continue
                if not candidates:
                    continue
                # None of the matches were visible; try the next strategy.
                last_error = Exception(
                    f"Found {len(candidates)} element(s) for {by}={value!r} "
                    "but none were visible/interactable."
                )
            except Exception as e:  # noqa: BLE001
                last_error = e
                continue

        logger.error(
            f"Could not find the {description} with any known strategy. "
            "The website's structure may have changed. Dumping page source snippet below:"
        )
        try:
            logger.error(driver.page_source[:3000])
        except Exception:  # noqa: BLE001
            pass
        raise last_error  # type: ignore[misc]

    def _find_mse_login_button(self, driver: WebDriver):
        """Finds the 'MesServices' login button (NOT the FranceConnect one),
        trying several strategies in case the site's markup changed.

        Scoped to #content (the main page area) to avoid accidentally matching
        the site's header/logo link, which also contains the word "MesServices"
        but just links back to the homepage.
        """
        translate_lower = "translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÉ', 'abcdefghijklmnopqrstuvwxyzàé')"
        strategies = [
            (By.CLASS_NAME, "loginapp-button"),
            (By.XPATH, "//*[@id='content']//*[contains(@class, 'loginapp')]"),
            (
                By.XPATH,
                f"//*[@id='content']//button[contains({translate_lower}, 'messervices')]",
            ),
            (
                By.XPATH,
                f"//*[@id='content']//a[contains({translate_lower}, 'messervices')]",
            ),
            # Fallback: find the "Identification avec MesServices" text, then the
            # nearest clickable element (link or button) that follows it.
            (
                By.XPATH,
                f"//*[contains({translate_lower}, 'identification avec messervices')]/following::a[1]",
            ),
            (
                By.XPATH,
                f"//*[contains({translate_lower}, 'identification avec messervices')]/following::button[1]",
            ),
        ]
        return self._find_element(driver, strategies, "MesServices login button")

    def _validate_rules(self, driver: WebDriver) -> None:
        """Validates the rules of the CROUS website."""
        logger.info("Validating the rules of the CROUS website")

        driver.get("https://trouverunlogement.lescrous.fr/tools/36/rules")

        sleep(self.delay)

        # <button class="fr-btn" type="submit" name="searchSubmit">Passer à la recherche de logements</button>

        validate_button = self._find_element(
            driver,
            [
                (By.NAME, "searchSubmit"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (
                    By.XPATH,
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÉ', 'abcdefghijklmnopqrstuvwxyzàé'), 'recherche de logements')]",
                ),
            ],
            "rules validation button",
        )

        validate_button.click()

        sleep(self.delay)
