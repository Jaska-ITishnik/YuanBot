import bcrypt
import requests
from bs4 import BeautifulSoup

from bot.handlers.message_handler import database
from config import conf


def usd_uzs(n: float = 1):
    url = "https://bank.uz/uz/currency"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    usd_element = soup.find("a", {"onclick": "init_diag('USD')"})
    if usd_element:
        rate = usd_element.find_all("span", class_="medium-text")[1].text.strip()
        database['usd_uzs'] = float(rate.replace(" ", '')) * n
    else:
        database['usd_uzs'] = 0


def usd_yuan(n: float = 1):
    url = "https://www.xe.com/currencyconverter/convert/?Amount=1&From=USD&To=CNY"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    conversion_element = soup.find("div", {"data-testid": "conversion"})
    if conversion_element:
        full_rate = conversion_element.find_all("p")[1].text.strip().split("=")[-1].strip()
        full_rate = full_rate.replace(" Chinese Yuan Renminbi", "").replace("\n", "")
        database['usd_yuan'] = float(full_rate) * n
    else:
        database['usd_yuan'] = 0

# scheduler = AsyncIOScheduler()

# def _task():
#     scheduler.add_job(usd_uzs, IntervalTrigger(minutes=1))
#     scheduler.add_job(usd_yuan, IntervalTrigger(minutes=1))
#     if not scheduler.running:
#         scheduler.start()

# usd_uzs()
# usd_yuan()

# print(bcrypt.gensalt())

import bcrypt

# password = b"Jasurbek_dev"  # Example password
# stored_hash = conf.web.PASSWD.encode()  # Ensure the stored hash is in bytes

# if bcrypt.checkpw(password, stored_hash):
#     print("Password matches!")
# else:
#     print("Incorrect password.")

import bcrypt

password = "Jasurbek_dev"  # Your plain text password

# Generate a salt and hash the password
hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Convert the hash to a string to store in a database
hashed_password_str = hashed_password.decode()

# print("Hashed Password:", hashed_password_str)
#
# print(bcrypt.checkpw(password.encode(), hashed_password_str.encode()))