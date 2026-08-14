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

        # Step 1: Go to the login page

        logger.info(f"Going to the login page: {settings.MSE_LOGIN_URL}")
        driver.get(settings.MSE_LOGIN_URL)
        sleep(self.delay)

        # Step 2: choose the correct authentication method
        logger.info("Choosing the correct authentication method")
        mse_connect_button = self._find_mse_login_button(driver)
        # mse_connect_button.click() # somehow doesn't work. We simulate a click instead :
        driver.execute_script("arguments[0].click();", mse_connect_button)
        sleep(self.delay)

        # Step 3: Input credentials and submit
        logger.info("Inputting credentials")
        username_input = driver.find_element(By.NAME, "j_username")
        password_input = driver.find_element(By.NAME, "j_password")

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

    def _find_mse_login_button(self, driver: WebDriver):
        """Finds the 'MesServices' login button (NOT the FranceConnect one),
        trying several strategies in case the site's markup changed.
        """
        strategies = [
            (By.CLASS_NAME, "loginapp-button"),
            (
                By.XPATH,
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÉ', 'abcdefghijklmnopqrstuvwxyzàé'), 'messervices')]",
            ),
            (
                By.XPATH,
                "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÉ', 'abcdefghijklmnopqrstuvwxyzàé'), 'messervices')]",
            ),
            (By.XPATH, "//*[contains(@class, 'loginapp')]"),
            (
                By.XPATH,
                "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÉ', 'abcdefghijklmnopqrstuvwxyzàé'), 'identification avec messervices')]",
            ),
        ]

        last_error: Exception | None = None
        for by, value in strategies:
            try:
                element = driver.find_element(by, value)
                logger.info(f"Found login button using strategy: {by}={value!r}")
                return element
            except Exception as e:  # noqa: BLE001
                last_error = e
                continue

        logger.error(
            "Could not find the MesServices login button with any known strategy. "
            "The website's structure may have changed."
        )
        raise last_error  # type: ignore[misc]

    def _validate_rules(self, driver: WebDriver) -> None:
        """Validates the rules of the CROUS website."""
        logger.info("Validating the rules of the CROUS website")

        driver.get("https://trouverunlogement.lescrous.fr/tools/36/rules")

        sleep(self.delay)

        # <button class="fr-btn" type="submit" name="searchSubmit">Passer à la recherche de logements</button>

        validate_button = driver.find_element(By.NAME, "searchSubmit")

        validate_button.click()

        sleep(self.delay)
