import requests
import datetime
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

API_KEY_SEARCH = os.getenv('KIWI_API_KEY_SEARCH_FLIGHT')
API_KEY_CODE = os.getenv('KIWI_API_KEY_SEARCH_CODE')
SHEET_ENDPOINT = os.getenv('SHEETY_URL')


flight_data = None
return_date = None
complex_url = None


start_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d/%m/%Y")
end_date = (datetime.date.today() + datetime.timedelta(days=180)).strftime("%d/%m/%Y")


kiwi_url = 'https://tequila-api.kiwi.com/'
IATA_CODE = "KRK"

header_search_code = {
    "apikey": API_KEY_CODE,
}

header_search_flight = {
    'apikey': API_KEY_SEARCH
}


sheety_response = requests.get(url=SHEET_ENDPOINT)
sheety_response.raise_for_status()
sheety_data = sheety_response.json()


cities = [sheety_data['flightData'][i]['city'] for i in range(len(sheety_data['flightData']))]
location_endpoint = f'{kiwi_url}locations/query'
for i in range(len(cities)):
    query = {
        "term": cities[i],
        "location_types": "city",
    }
    header = {
        "apikey": API_KEY_SEARCH
    }
    response = requests.get(url=location_endpoint, headers=header, params=query)
    result = response.json()
    code = result['locations'][0]["code"]

    post_city_params = {
        "flightDatum":
            {
                "iataCode": code
            }
        }

    put_data = requests.put(url=f"{SHEET_ENDPOINT}""/"f"{sheety_data['flightData'][i]['id']}", json=post_city_params)
    put_data.raise_for_status()


for i in range(len(sheety_data['flightData'])):
    iata_codes = [sheety_data['flightData'][i]['iataCode'] for i in range(len(sheety_data['flightData']))]
    search_params = {
        "fly_from": IATA_CODE,
        "fly_to": iata_codes[i],
        "date_from": start_date,
        "date_to": end_date,
        "nights_in_dst_from": 6,
        "nights_in_dst_to": 7,
        "curr": "PLN",
        "adults": 2,
        "flight_type": "round",
        "only_weekends": True,
        "max_stopovers": 0,
        "limit": 10
        }

    tequila_response = requests.get(url=f"{kiwi_url}v2/search", headers=header_search_flight, params=search_params)
    tequila_response.raise_for_status()
    flights_data = tequila_response.json()
    price = [sheety_data['flightData'][i]['lowestPrice'] for i in range(len(sheety_data['flightData']))]
    lowest_price = price[i]
    for x in range(len(flights_data["data"])):
        if lowest_price >= flights_data["data"][x]["price"]:
            lowest_price = flights_data["data"][x]["price"]
            flight_date = flights_data["data"][x]['route'][0]["local_departure"].split("T")
            return_date = flights_data["data"][x]['route'][1]["local_departure"].split("T")
            complex_url = flights_data['data'][x]["deep_link"]
    post_params = {
        "flightDatum": {
            "lowestPrice": lowest_price
        }
    }
    response = requests.put(url=f"{SHEET_ENDPOINT}""/"f"{sheety_data['flightData'][i]['id']}", json=post_params)
    response.raise_for_status()
