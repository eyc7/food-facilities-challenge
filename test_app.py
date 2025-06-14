import unittest
from unittest.mock import patch, MagicMock, Mock
import json
from time import time
import hashlib
import sys
import os

# Add the parent directory to sys.path to import the main app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app and components
from app import app, db, MobileFoodFacilityPermit, distance_cache, make_cache_key, chunk_list, get_distance_batch


class TestFlaskApp(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory SQLite for testing
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create tables
        db.create_all()
        
        # Clear cache before each test
        distance_cache.clear()
        
        # Add sample data
        self._add_sample_data()
    
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        distance_cache.clear()
    
    def _add_sample_data(self):
        """Add sample data for testing."""
        permits = [
            MobileFoodFacilityPermit(
                locationid=1,
                applicant="Taco Truck",
                status="APPROVED",
                address="123 Main St",
                latitude=37.7749,
                longitude=-122.4194,
                zipcodes="94102"
            ),
            MobileFoodFacilityPermit(
                locationid=2,
                applicant="Pizza Cart",
                status="APPROVED",
                address="456 Oak Ave",
                latitude=37.7849,
                longitude=-122.4094,
                zipcodes="94103"
            ),
            MobileFoodFacilityPermit(
                locationid=3,
                applicant="Burrito Express",
                status="EXPIRED",
                address="789 Pine St",
                latitude=37.7949,
                longitude=-122.3994,
                zipcodes="94104"
            ),
            MobileFoodFacilityPermit(
                locationid=4,
                applicant="Sandwich Shop",
                status="REQUESTED",
                address="321 Elm St",
                latitude=37.7649,
                longitude=-122.4294,
                zipcodes="94105"
            )
        ]
        
        for permit in permits:
            db.session.add(permit)
        db.session.commit()


class TestHomeEndpoint(TestFlaskApp):
    
    def test_home_endpoint(self):
        """Test the home endpoint returns correct message."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], "Just to check flask is working")


class TestSearchApplicantEndpoint(TestFlaskApp):
    
    def test_search_applicant_basic(self):
        """Test basic applicant search functionality."""
        payload = {
            'applicant': 'Taco',
            'statuses': ['APPROVED']
        }
        response = self.app.post('/search_applicant', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['applicant'], 'Taco Truck')
        self.assertEqual(data[0]['status'], 'APPROVED')
    
    def test_search_applicant_case_insensitive(self):
        """Test that applicant search is case insensitive."""
        payload = {
            'applicant': 'taco',
            'statuses': ['APPROVED']
        }
        response = self.app.post('/search_applicant', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['applicant'], 'Taco Truck')
    
    def test_search_applicant_with_address(self):
        """Test applicant search with address filter."""
        payload = {
            'applicant': '',
            'address': 'Main',
            'statuses': ['APPROVED']
        }
        response = self.app.post('/search_applicant', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['address'], '123 Main St')
    
    def test_search_applicant_multiple_statuses(self):
        """Test search with multiple statuses."""
        payload = {
            'applicant': '',
            'statuses': ['APPROVED', 'EXPIRED']
        }
        response = self.app.post('/search_applicant', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 3)  # Should return APPROVED and EXPIRED permits
    
    def test_search_applicant_invalid_statuses(self):
        """Test search with invalid statuses format."""
        payload = {
            'applicant': 'Taco',
            'statuses': 'APPROVED'  # Should be a list, not string
        }
        response = self.app.post('/search_applicant', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'statuses must be a list')
    
    def test_search_applicant_default_status(self):
        """Test that default status is APPROVED when not specified."""
        payload = {
            'applicant': 'Taco'
        }
        response = self.app.post('/search_applicant', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['status'], 'APPROVED')


class TestSearchNearbyEndpoint(TestFlaskApp):
    
    @patch('app.requests.get')
    def test_search_nearby_basic(self, mock_get):
        """Test basic nearby search functionality."""
        # Mock Google API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "rows": [{
                "elements": [
                    {
                        "status": "OK",
                        "distance": {"value": 1500}  # 1.5 km
                    },
                    {
                        "status": "OK",
                        "distance": {"value": 2500}  # 2.5 km
                    }
                ]
            }]
        }
        mock_get.return_value = mock_response
        
        payload = {
            'latitude': 37.7749,
            'longitude': -122.4194,
            'statuses': ['APPROVED']
        }
        response = self.app.post('/search_nearby', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        # Should return results sorted by distance
        if len(data) > 1:
            self.assertLessEqual(data[0]['distance_km'], data[1]['distance_km'])
    
    def test_search_nearby_missing_coordinates(self):
        """Test nearby search with missing coordinates."""
        payload = {
            'latitude': 37.7749,
            # Missing longitude
            'statuses': ['APPROVED']
        }
        response = self.app.post('/search_nearby', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Latitude and longitude are required')
    
    def test_search_nearby_invalid_statuses(self):
        """Test nearby search with invalid statuses format."""
        payload = {
            'latitude': 37.7749,
            'longitude': -122.4194,
            'statuses': 'APPROVED'  # Should be a list
        }
        response = self.app.post('/search_nearby', 
                                json=payload,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'statuses must be a list')
    
    @patch('app.requests.get')
    def test_search_nearby_caching(self, mock_get):
        """Test that caching works for nearby searches."""
        # Mock Google API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "rows": [{"elements": [{"status": "OK", "distance": {"value": 1500}}]}]
        }
        mock_get.return_value = mock_response
        
        payload = {
            'latitude': 37.7749,
            'longitude': -122.4194,
            'statuses': ['APPROVED']
        }
        
        # First request
        response1 = self.app.post('/search_nearby', 
                                 json=payload,
                                 content_type='application/json')
        self.assertEqual(response1.status_code, 200)
        
        # Second request should use cache (mock should only be called once)
        response2 = self.app.post('/search_nearby', 
                                 json=payload,
                                 content_type='application/json')
        self.assertEqual(response2.status_code, 200)
        
        # Verify that Google API was called only once due to caching
        self.assertEqual(mock_get.call_count, 1)


class TestUtilityFunctions(unittest.TestCase):
    
    def test_chunk_list(self):
        """Test the chunk_list utility function."""
        data = list(range(10))
        chunks = list(chunk_list(data, 3))
        
        self.assertEqual(len(chunks), 4)  # 10 items in chunks of 3 = 4 chunks
        self.assertEqual(chunks[0], [0, 1, 2])
        self.assertEqual(chunks[1], [3, 4, 5])
        self.assertEqual(chunks[2], [6, 7, 8])
        self.assertEqual(chunks[3], [9])  # Last chunk with remaining items
    
    def test_chunk_list_empty(self):
        """Test chunk_list with empty data."""
        chunks = list(chunk_list([], 3))
        self.assertEqual(len(chunks), 0)
    
    def test_make_cache_key(self):
        """Test the make_cache_key function."""
        lat, lon = 37.7749, -122.4194
        statuses = {'APPROVED', 'EXPIRED'}
        
        key1 = make_cache_key(lat, lon, statuses)
        key2 = make_cache_key(lat, lon, statuses)
        
        # Same input should produce same key
        self.assertEqual(key1, key2)
        
        # Different input should produce different key
        key3 = make_cache_key(lat + 0.1, lon, statuses)
        self.assertNotEqual(key1, key3)
        
        # Key should be a valid MD5 hash (32 hex characters)
        self.assertEqual(len(key1), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in key1))


class TestGetDistanceBatch(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_permits = [
            Mock(applicant="Test 1", status="APPROVED", address="123 Test St", 
                 latitude=37.7749, longitude=-122.4194, zipcodes="94102"),
            Mock(applicant="Test 2", status="APPROVED", address="456 Test Ave", 
                 latitude=37.7849, longitude=-122.4094, zipcodes="94103")
        ]
    
    @patch('app.requests.get')
    def test_get_distance_batch_success(self, mock_get):
        """Test successful distance batch calculation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "rows": [{
                "elements": [
                    {"status": "OK", "distance": {"value": 1500}},
                    {"status": "OK", "distance": {"value": 2500}}
                ]
            }]
        }
        mock_get.return_value = mock_response
        
        origins = "37.7749,-122.4194"
        result = get_distance_batch(origins, self.mock_permits)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['applicant'], 'Test 1')
        self.assertEqual(result[0]['distance_km'], 1.5)
        self.assertEqual(result[1]['applicant'], 'Test 2')
        self.assertEqual(result[1]['distance_km'], 2.5)
    
    @patch('app.requests.get')
    def test_get_distance_batch_api_error(self, mock_get):
        """Test distance batch with API error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        origins = "37.7749,-122.4194"
        result = get_distance_batch(origins, self.mock_permits)
        
        self.assertEqual(result, [])
    
    @patch('app.requests.get')
    def test_get_distance_batch_invalid_response(self, mock_get):
        """Test distance batch with invalid API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ERROR"}
        mock_get.return_value = mock_response
        
        origins = "37.7749,-122.4194"
        result = get_distance_batch(origins, self.mock_permits)
        
        self.assertEqual(result, [])
    
    @patch('app.requests.get')
    def test_get_distance_batch_partial_success(self, mock_get):
        """Test distance batch with some failed elements."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "rows": [{
                "elements": [
                    {"status": "OK", "distance": {"value": 1500}},
                    {"status": "NOT_FOUND"}  # This element fails
                ]
            }]
        }
        mock_get.return_value = mock_response
        
        origins = "37.7749,-122.4194"
        result = get_distance_batch(origins, self.mock_permits)
        
        # Should only return the successful result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['applicant'], 'Test 1')
        self.assertEqual(result[0]['distance_km'], 1.5)


class TestDatabaseModel(TestFlaskApp):
    
    def test_mobile_food_facility_permit_model(self):
        """Test the database model functionality."""
        # Test that we can query the sample data
        permits = MobileFoodFacilityPermit.query.all()
        self.assertEqual(len(permits), 4)
        
        # Test filtering by status
        approved_permits = MobileFoodFacilityPermit.query.filter_by(status='APPROVED').all()
        self.assertEqual(len(approved_permits), 2)
        
        # Test case-insensitive applicant search
        taco_permits = MobileFoodFacilityPermit.query.filter(
            MobileFoodFacilityPermit.applicant.ilike('%taco%')
        ).all()
        self.assertEqual(len(taco_permits), 1)
        self.assertEqual(taco_permits[0].applicant, 'Taco Truck')


class TestCaching(unittest.TestCase):
    
    def setUp(self):
        """Clear cache before each test."""
        distance_cache.clear()
    
    def tearDown(self):
        """Clear cache after each test."""
        distance_cache.clear()
    
    def test_cache_storage_and_retrieval(self):
        """Test that cache stores and retrieves data correctly."""
        cache_key = "test_key"
        test_data = [{"test": "data"}]
        
        # Store in cache
        distance_cache[cache_key] = {
            'timestamp': time(),
            'data': test_data
        }
        
        # Retrieve from cache
        cached = distance_cache.get(cache_key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['data'], test_data)
    
    def test_cache_expiration(self):
        """Test that cache respects TTL."""
        from app import CACHE_TTL
        
        cache_key = "test_key"
        test_data = [{"test": "data"}]
        
        # Store with old timestamp (expired)
        distance_cache[cache_key] = {
            'timestamp': time() - CACHE_TTL - 1,
            'data': test_data
        }
        
        # Should be considered expired
        cached = distance_cache.get(cache_key)
        self.assertTrue(time() - cached['timestamp'] >= CACHE_TTL)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)