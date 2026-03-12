import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
fcade_url = "https://www.fightcade.com/api/"
body = '{"req": "getuser", "username": "gureepufu"}'
headers = {'content-type' : 'application/json'}

class CustomUCWebDriver(uc.Chrome):
    def post(self, url, data):
        return self.execute_script(f"""
            return fetch("{url}", {{
                method: "POST",
                body: '{data}',
                headers: {{
                    "Content-Type": "application/json;charset=UTF-8"
                }}
            }})
            .then(response => response.text());
        """)


# Create an instance of CustomUCWebDriver
options = uc.ChromeOptions()
options.add_argument("--headless=new")  # for hidden mode
options.add_argument("--use_subprocess=False") 

driver = CustomUCWebDriver(options=options)

# Make a POST request and capture the response
response_data = driver.post(fcade_url, body)

# Print the response data
print(response_data)