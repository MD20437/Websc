from flask import Flask, render_template, request, jsonify, redirect, url_for
from multiprocessing import Manager
from pymongo import MongoClient
import os
import requests

app = Flask(__name__)

# Połączenie z MongoDB
mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
client = MongoClient(mongo_uri)
db = client['webscraper']
collection = db['scraped_data']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    num_threads = 4
    response = requests.post('http://engine:8000/scrape', json={'num_threads': num_threads})
    if response.status_code == 200:
        shared_dict = response.json()

        if 'volvo' in shared_dict and shared_dict['volvo']:
            collection.insert_many(shared_dict['volvo'])
        if 'dostawcze' in shared_dict and shared_dict['dostawcze']:
            collection.insert_many(shared_dict['dostawcze'])
        if 'ciezarowe' in shared_dict and shared_dict['ciezarowe']:
            collection.insert_many(shared_dict['ciezarowe'])

        return render_template('success.html') if any(shared_dict.values()) else jsonify({"status": "error", "message": "Nie znaleziono"})
    else:
        return jsonify({"status": "error", "message": "Błąd połączenia z silnikiem"})

@app.route('/scrape_dostawcze', methods=['POST'])
def scrape_dostawcze():
    num_threads = 4
    response = requests.post('http://engine:8000/scrape', json={'num_threads': num_threads})
    if response.status_code == 200:
        shared_dict = response.json()

        if 'dostawcze' in shared_dict and shared_dict['dostawcze']:
            collection.insert_many(shared_dict['dostawcze'])
            return render_template('success.html')
        else:
            return jsonify({"status": "error", "message": "Nie znaleziono"})
    else:
        return jsonify({"status": "error", "message": "Błąd połączenia z silnikiem"})

@app.route('/scrape_ciezarowe', methods=['POST'])
def scrape_ciezarowe():
    num_threads = 4
    response = requests.post('http://engine:8000/scrape', json={'num_threads': num_threads})
    if response.status_code == 200:
        shared_dict = response.json()

        if 'ciezarowe' in shared_dict and shared_dict['ciezarowe']:
            collection.insert_many(shared_dict['ciezarowe'])
            return render_template('success.html')
        else:
            return jsonify({"status": "error", "message": "Nie znaleziono"})
    else:
        return jsonify({"status": "error", "message": "Błąd połączenia z silnikiem"})

@app.route('/results', methods=['GET'])
def results():
    sort_by = request.args.get('sort_by', 'cena')
    order = request.args.get('order', 'asc')
    category = request.args.get('category', None)

    results = list(collection.find({}, {"_id": 0}))

    if category:
        results = [result for result in results if result.get('category') == category]

    if sort_by == 'cena':
        results.sort(key=lambda x: parse_price(x['cena']), reverse=(order == 'desc'))
    elif sort_by == 'model':
        results.sort(key=lambda x: x['model'], reverse=(order == 'desc'))

    return render_template('results.html', results=results, sort_by=sort_by, order=order)

def parse_price(price_str):
    try:
        return float(price_str.replace(' ', '').replace('PLN', '').replace('zł', '').replace(',', '').replace('złdo negocjacji', ''))
    except ValueError:
        return float('inf') 

@app.route('/save_to_mongo', methods=['POST'])
def save_to_mongo():
    data = request.get_json()
    if data and 'results' in data:
        collection.insert_many(data['results'])
        return jsonify({"status": "success", "message": "Dane zapisane"})
    else:
        return jsonify({"status": "error", "message": "Dane nie zapisane"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
