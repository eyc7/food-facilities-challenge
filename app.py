from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from time import time
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env only for local dev

distance_cache = {}
CACHE_TTL = 60 * 60  # 1 hour
app = Flask(__name__)
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')
INSTANCE_CONNECTION_NAME = os.getenv('INSTANCE_CONNECTION_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@/{DB_NAME}'
    f'?host=/cloudsql/{INSTANCE_CONNECTION_NAME}'
)

# this line turns off the feature to listen to any changes, which we forsee no data modifications.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)


@app.route('/')
def home():
    return jsonify(message="Just to check flask is working")

db = SQLAlchemy(app)

class MobileFoodFacilityPermit(db.Model):
    __tablename__ = 'mobile_food_facility_permit'
    locationid = db.Column(db.Integer, primary_key=True)
    applicant = db.Column(db.String)
    status = db.Column(db.String)
    address = db.Column(db.String)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    zipcodes = db.Column(db.String)  # Adjust if column name is different

@app.route('/search_applicant', methods=['POST'])
def search_applicant():
    data = request.get_json()
    applicant_query = data.get('applicant', '').strip()
    address_query = data.get('address', '').strip()
    user_statuses = data.get('statuses', ['APPROVED'])

    if not isinstance(user_statuses, list):
        return jsonify({'error': 'statuses must be a list'}), 400

    # Normalize input (e.g., trim & uppercase)
    status_set = set(s.strip().upper() for s in user_statuses)


    # Build the base query filtering by applicant name (case-insensitive)
    query = MobileFoodFacilityPermit.query.filter(
        MobileFoodFacilityPermit.applicant.ilike(f'%{applicant_query}%')
    )

    # Always filter by status; use default "APPROVED" unless overridden
    query = query.filter(MobileFoodFacilityPermit.status.in_(status_set))
    if address_query:
        query = query.filter(MobileFoodFacilityPermit.address.ilike(f'%{address_query}%'))


    results = query.limit(30).all()

    output = [{
        'applicant': p.applicant,
        'status': p.status,
        'address': p.address,
        'latitude': p.latitude,
        'longitude': p.longitude,
        'zipcodes': p.zipcodes
    } for p in results]

    return jsonify(output)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

@app.route('/search_nearby', methods=['POST'])
def search_nearby():
    data = request.get_json()
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')
    user_statuses = data.get('statuses', ['APPROVED'])

    if not isinstance(user_statuses, list):
        return jsonify({'error': 'statuses must be a list'}), 400

    status_set = set(s.strip().upper() for s in user_statuses)

    if not user_lat or not user_lon:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    # Check cache
    cache_key = make_cache_key(user_lat, user_lon, status_set)
    cached = distance_cache.get(cache_key)
    if cached and time() - cached['timestamp'] < CACHE_TTL:
        return jsonify(cached['data'])


    # Query all matching permits (~500)
    permits = MobileFoodFacilityPermit.query.filter(
        MobileFoodFacilityPermit.status.in_(status_set)
    ).all()

    origins = f"{user_lat},{user_lon}"

    results = []
    # Batch permits into chunks of 25 for Google API Free tier
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for chunk in chunk_list(permits, 25):
            futures.append(executor.submit(get_distance_batch, origins, chunk))

        for future in as_completed(futures):
            results.extend(future.result())

    # Sort by closest and return top 5
    results.sort(key=lambda x: x['distance_km'])
    top5 = results[:5]

    # Cache the result
    distance_cache[cache_key] = {
        'timestamp': time(),
        'data': top5
    }

    return jsonify(top5)


def chunk_list(data, size):
    """Yield successive chunks of size `size` from `data`."""
    for i in range(0, len(data), size):
        yield data[i:i + size]

def get_distance_batch(origins, permits_chunk):
    destinations = "|".join([
        f"{p.latitude},{p.longitude}" for p in permits_chunk if p.latitude and p.longitude
    ])
    response = requests.get("https://maps.googleapis.com/maps/api/distancematrix/json", params={
        "origins": origins,
        "destinations": destinations,
        "key": GOOGLE_API_KEY,
        "units": "metric"
    })

    if response.status_code != 200:
        return []

    data = response.json()
    if data.get("status") != "OK":
        return []

    distances = []
    for i, permit in enumerate(permits_chunk):
        try:
            element = data['rows'][0]['elements'][i]
            if element['status'] == 'OK':
                distances.append({
                    'applicant': permit.applicant,
                    'status': permit.status,
                    'address': permit.address,
                    'latitude': permit.latitude,
                    'longitude': permit.longitude,
                    'zipcodes': permit.zipcodes,
                    'distance_km': round(element['distance']['value'] / 1000.0, 2)
                })
        except (IndexError, KeyError):
            continue

    return distances


def make_cache_key(lat, lon, statuses):
    key = f"{lat}:{lon}:" + ",".join(sorted(statuses))
    return hashlib.md5(key.encode()).hexdigest()


port = int(os.environ.get("PORT", 8080))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port)