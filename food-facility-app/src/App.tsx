import { useState } from 'react';
import axios from 'axios';
import Select from 'react-select';

type FoodTruck = {
  applicant: string;
  status: string;
  address: string;
  latitude: number;
  longitude: number;
  zipcodes: string;
};

type StatusOption = { value: string; label: string };

const statusOptions = [
  { value: 'APPROVED', label: 'APPROVED' },
  { value: 'EXPIRED', label: 'EXPIRED' },
  { value: 'REQUESTED', label: 'REQUESTED' },
  { value: 'SUSPENDED', label: 'SUSPENDED' },
];

function App() {
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [applicant, setApplicant] = useState('');
  const [address, setAddress] = useState('');
  const [nearbyStatuses, setNearbyStatuses] = useState<StatusOption[]>([]);
  const [applicantStatuses, setApplicantStatuses] = useState<StatusOption[]>([]);


  const [results, setResults] = useState<FoodTruck[]>([]);


  const getNearByStatusList = () => nearbyStatuses.map(s => s.value);

  const handleSearchNearby = async () => {
    console.log(getNearByStatusList());
    try {
      const res = await axios.post<FoodTruck[]>('https://my-flask-app-688153142575.us-central1.run.app/search_nearby', {
        latitude,
        longitude,
        statuses: getNearByStatusList(),
      });
      setResults(res.data);
    } catch (err) {
      console.error('Nearby search failed', err);
    }
  };

  const getApplicantStatusList = () => applicantStatuses.map(s => s.value);

  const handleSearchApplicant = async () => {
    console.log(getApplicantStatusList());
    try {
      const res = await axios.post<FoodTruck[]>('https://my-flask-app-688153142575.us-central1.run.app/search_applicant', {
        applicant,
        address,
        statuses: getApplicantStatusList(),
      });
      setResults(res.data);
    } catch (err) {
      console.error('Applicant search failed', err);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Food Facility Search</h1>

      {/* --- Search Nearby Section --- */}
      <section style={{ marginBottom: '30px' }}>
        <h2>🔍 Search Nearby</h2>
        <input
          placeholder="Latitude"
          value={latitude}
          onChange={e => setLatitude(e.target.value)}
          style={{ marginRight: '10px' }}
        />
        <input
          placeholder="Longitude"
          value={longitude}
          onChange={e => setLongitude(e.target.value)}
        />
        <div style={{ marginTop: '10px', width: '300px' }}>
          <label>Status:</label>
          <Select
            isMulti
            options={statusOptions}
            value={nearbyStatuses}
            onChange={(newValue: readonly StatusOption[] | null) =>
    setNearbyStatuses(newValue ? [...newValue] : [])}
          />
        </div>
        <button onClick={handleSearchNearby} style={{ marginTop: '10px' }}>
          Search Nearby
        </button>
      </section>

      {/* --- Search by Applicant/Address Section --- */}
      <section>
        <h2>🔎 Search by Applicant/Address</h2>
        <input
          placeholder="Applicant Name"
          value={applicant}
          onChange={e => setApplicant(e.target.value)}
          style={{ marginRight: '10px' }}
        />
        <input
          placeholder="Address"
          value={address}
          onChange={e => setAddress(e.target.value)}
        />
        <div style={{ marginTop: '10px', width: '300px' }}>
          <label>Status:</label>
          <Select
            isMulti
            options={statusOptions}
            value={applicantStatuses}
            onChange={(newValue: readonly StatusOption[] | null) =>
    setApplicantStatuses(newValue ? [...newValue] : [])}
          />
        </div>
        <button onClick={handleSearchApplicant} style={{ marginTop: '10px' }}>
          Search Applicant/Address
        </button>
      </section>

      {/* --- Results --- */}
      <section style={{ marginTop: '30px' }}>
        <h2>📋 Results</h2>
        {results.length === 0 && <p>No results found.</p>}
        <ul>
          {results.map((truck, i) => (
            <li key={i}>
              <strong>{truck.applicant}</strong> — {truck.address} ({truck.status})
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export default App;
