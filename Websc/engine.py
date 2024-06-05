from flask import Flask, request, jsonify
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Manager

BASE_URL = 'https://www.olx.pl/motoryzacja/samochody/volvo/'
BASE_URL_DOSTAWCZE = 'https://www.olx.pl/motoryzacja/dostawcze/'
BASE_URL_CIEZAROWE = 'https://www.olx.pl/motoryzacja/ciezarowe/'

app = Flask(__name__)

async def fetch(url, session):
    async with session.get(url) as response:
        return await response.text()

async def scrape_data(url, category, shared_dict):
    async with ClientSession() as session:
        html = await fetch(url, session)
        soup = BeautifulSoup(html, 'html.parser')
        cars = soup.find_all('div', {'data-cy': 'l-card'})
        results = []

        for car in cars:
            model_tag = car.find('div', {'data-cy': 'ad-card-title'})
            model = model_tag.find('h6').text.strip() if model_tag and model_tag.find('h6') else None
            cena = car.find('p', {'data-testid': 'ad-price'}).text.strip() if car.find('p', {'data-testid': 'ad-price'}) else None

            # Scrapowanie rok_przebieg
            rok_przebieg_div = car.find('div', {'class': 'css-1kfqt7f'})
            rok_przebieg = rok_przebieg_div.find('span', {'class': 'css-efx9z5'}).text.strip() if rok_przebieg_div and rok_przebieg_div.find('span', {'class': 'css-efx9z5'}) else None
            
            # Scrapowanie lokalizacji
            location_div = car.find('div', {'class': 'css-odp1qd'})
            lokalizacja = location_div.find('p', {'data-testid': 'location-date'}).text.strip() if location_div and location_div.find('p', {'data-testid': 'location-date'}) else None

            # Słownik 
            result = {
                'model': model,
                'cena': cena,
                'rok_przebieg': rok_przebieg,
                'lokalizacja': lokalizacja,
                'category': category
            }

            results.append(result)

        shared_dict[category] = results

async def main(shared_dict, num_threads):
    urls = [
        (BASE_URL, 'volvo'),
        (BASE_URL_DOSTAWCZE, 'dostawcze'),
        (BASE_URL_CIEZAROWE, 'ciezarowe')
    ]

    tasks = []
    for url, category in urls:
        tasks.append(scrape_data(url, category, shared_dict))

    await asyncio.gather(*tasks)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    num_threads = data.get('num_threads', 10)
    
    manager = Manager()
    shared_dict = manager.dict()
    
    asyncio.run(main(shared_dict, num_threads))
    
    shared_dict_regular = dict(shared_dict)
    
    return jsonify(shared_dict_regular)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
