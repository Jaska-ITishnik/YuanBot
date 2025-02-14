import requests
from bs4 import BeautifulSoup

from bot.handlers.message_handler import database


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
        database['usd_yuan'] = round(float(full_rate), 2) * n
    else:
        database['usd_yuan'] = 0
