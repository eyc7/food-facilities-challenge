import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import '@testing-library/jest-dom';
import axios from 'axios';
import App from './App';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios as typeof axios, true);


// Mock react-select to simplify testing
vi.mock('react-select', () => {
  return {
    default: function MockSelect({
      isMulti,
      options,
      value,
      onChange,
      ...props
    }: {
      isMulti?: boolean;
      options: { value: string; label: string }[];
      value:
        | { value: string; label: string }
        | { value: string; label: string }[]
        | null
        | undefined;
      onChange: (value: any) => void;
      [key: string]: any;
    }) {
      const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const selectedValues = Array.from(e.target.selectedOptions, (option) =>
          options.find((opt) => opt.value === option.value)
        ).filter(Boolean); // remove undefineds

        onChange(isMulti ? selectedValues : selectedValues[0]);
      };

      return (
        <select
          {...props}
          multiple={isMulti}
          value={
            isMulti
              ? Array.isArray(value)
                ? value.map((v) => v.value)
                : []
              : (value as { value: string })?.value || ''
          }
          onChange={handleChange}
          data-testid="status-select"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    },
  };
});

describe('Food Facility Search App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    test('renders main heading', () => {
      render(<App />);
      expect(screen.getByText('Food Facility Search')).toBeInTheDocument();
    });

    test('renders search nearby section', () => {
      render(<App />);
      expect(screen.getByText('🔍 Search Nearby')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Latitude')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Longitude')).toBeInTheDocument();
      expect(screen.getByText('Search Nearby')).toBeInTheDocument();
    });

    test('renders search by applicant section', () => {
      render(<App />);
      expect(screen.getByText('🔎 Search by Applicant/Address')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Applicant Name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Address')).toBeInTheDocument();
      expect(screen.getByText('Search Applicant/Address')).toBeInTheDocument();
    });

    test('renders results section with no results message', () => {
      render(<App />);
      expect(screen.getByText('📋 Results')).toBeInTheDocument();
      expect(screen.getByText('No results found.')).toBeInTheDocument();
    });
  });

  describe('Form Input Handling', () => {
    test('updates latitude input value', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      const latitudeInput = screen.getByPlaceholderText('Latitude');
      await user.type(latitudeInput, '37.7749');
      
      expect(latitudeInput).toHaveValue('37.7749');
    });

    test('updates longitude input value', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      const longitudeInput = screen.getByPlaceholderText('Longitude');
      await user.type(longitudeInput, '-122.4194');
      
      expect(longitudeInput).toHaveValue('-122.4194');
    });

    test('updates applicant name input value', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      const applicantInput = screen.getByPlaceholderText('Applicant Name');
      await user.type(applicantInput, 'Test Food Truck');
      
      expect(applicantInput).toHaveValue('Test Food Truck');
    });

    test('updates address input value', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      const addressInput = screen.getByPlaceholderText('Address');
      await user.type(addressInput, '123 Main St');
      
      expect(addressInput).toHaveValue('123 Main St');
    });
  });

  describe('Search Nearby Functionality', () => {
    test('calls API with correct parameters for nearby search', async () => {
      const mockResponse = {
        data: [
          {
            applicant: 'Test Truck',
            status: 'APPROVED',
            address: '123 Test St',
            latitude: 37.7749,
            longitude: -122.4194,
            zipcodes: '94102'
          }
        ]
      };
      
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      const user = userEvent.setup();
      render(<App />);
      
      // Fill in form data
      await user.type(screen.getByPlaceholderText('Latitude'), '37.7749');
      await user.type(screen.getByPlaceholderText('Longitude'), '-122.4194');
      
      // Click search button
      const searchButton = screen.getByText('Search Nearby');
      await user.click(searchButton);
      
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'https://my-flask-app-688153142575.us-central1.run.app/search_nearby',
          {
            latitude: '37.7749',
            longitude: '-122.4194',
            statuses: []
          }
        );
      });
    });

    test('displays results after successful nearby search', async () => {
      const mockResponse = {
        data: [
          {
            applicant: 'Test Food Truck',
            status: 'APPROVED',
            address: '123 Test Street',
            latitude: 37.7749,
            longitude: -122.4194,
            zipcodes: '94102'
          }
        ]
      };
      
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      const user = userEvent.setup();
      render(<App />);
      
      await user.type(screen.getByPlaceholderText('Latitude'), '37.7749');
      await user.type(screen.getByPlaceholderText('Longitude'), '-122.4194');
      
      const searchButton = screen.getByText('Search Nearby');
      await user.click(searchButton);

      await waitFor(() => {
        expect(screen.getByText('Test Food Truck')).toBeInTheDocument();

        const matchingItems = screen.getAllByText((_, element) =>
            element?.textContent === 'Test Food Truck — 123 Test Street (APPROVED)'
        );
        
        expect(matchingItems.length).toBeGreaterThan(0);
        expect(matchingItems[0]).toBeInTheDocument();
      });

    
      // Should no longer show "No results found"
      expect(screen.queryByText('No results found.')).not.toBeInTheDocument();
    });

    test('handles nearby search API error gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockedAxios.post.mockRejectedValueOnce(new Error('Network error'));
      
      const user = userEvent.setup();
      render(<App />);
      
      await user.type(screen.getByPlaceholderText('Latitude'), '37.7749');
      await user.type(screen.getByPlaceholderText('Longitude'), '-122.4194');
      
      const searchButton = screen.getByText('Search Nearby');
      await user.click(searchButton);
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Nearby search failed', expect.any(Error));
      });
      
      consoleSpy.mockRestore();
    });
  });

  describe('Search Applicant Functionality', () => {
    test('calls API with correct parameters for applicant search', async () => {
      const mockResponse = { data: [] };
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      const user = userEvent.setup();
      render(<App />);
      
      await user.type(screen.getByPlaceholderText('Applicant Name'), 'Test Applicant');
      await user.type(screen.getByPlaceholderText('Address'), '456 Test Ave');
      
      const searchButton = screen.getByText('Search Applicant/Address');
      await user.click(searchButton);
      
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'https://my-flask-app-688153142575.us-central1.run.app/search_applicant',
          {
            applicant: 'Test Applicant',
            address: '456 Test Ave',
            statuses: []
          }
        );
      });
    });

    test('displays results after successful applicant search', async () => {
      const mockResponse = {
        data: [
          {
            applicant: 'Amazing Food Cart',
            status: 'EXPIRED',
            address: '789 Food Lane',
            latitude: 37.7849,
            longitude: -122.4094,
            zipcodes: '94103'
          }
        ]
      };
      
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      const user = userEvent.setup();
      render(<App />);
      
      await user.type(screen.getByPlaceholderText('Applicant Name'), 'Amazing');
      
      const searchButton = screen.getByText('Search Applicant/Address');
      await user.click(searchButton);
      
      await waitFor(() => {
        expect(screen.getByText('Amazing Food Cart')).toBeInTheDocument();

        const items = screen.getAllByText((_, element) => {
            return element?.textContent === 'Amazing Food Cart — 789 Food Lane (EXPIRED)';
        });

        expect(items.length).toBeGreaterThan(0);
        expect(items[0]).toBeInTheDocument();
      });
      
      // Should no longer show "No results found"
      expect(screen.queryByText('No results found.')).not.toBeInTheDocument();
    });

    test('handles applicant search API error gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      mockedAxios.post.mockRejectedValueOnce(new Error('Server error'));
      
      const user = userEvent.setup();
      render(<App />);
      
      const searchButton = screen.getByText('Search Applicant/Address');
      await user.click(searchButton);
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Applicant search failed', expect.any(Error));
      });
      
      consoleSpy.mockRestore();
    });
  });

  describe('Results Display', () => {
    test('displays multiple results correctly', async () => {
      const mockResponse = {
        data: [
          {
            applicant: 'First Truck',
            status: 'APPROVED',
            address: '111 First St',
            latitude: 37.7749,
            longitude: -122.4194,
            zipcodes: '94102'
          },
          {
            applicant: 'Second Truck',
            status: 'REQUESTED',
            address: '222 Second St',
            latitude: 37.7849,
            longitude: -122.4094,
            zipcodes: '94103'
          }
        ]
      };
      
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      const user = userEvent.setup();
      render(<App />);
      
      const searchButton = screen.getByText('Search Nearby');
      await user.click(searchButton);
      
      await waitFor(() => {
        expect(screen.getByText('First Truck')).toBeInTheDocument();
        expect(screen.getByText('Second Truck')).toBeInTheDocument();
        expect(screen.getByText(/111 First St/)).toBeInTheDocument();
        expect(screen.getByText(/222 Second St/)).toBeInTheDocument();
      });
    });

    test('clears previous results on new search', async () => {
      // First search
      const firstResponse = {
        data: [{ applicant: 'First Result', status: 'APPROVED', address: '123 St', latitude: 0, longitude: 0, zipcodes: '' }]
      };
      mockedAxios.post.mockResolvedValueOnce(firstResponse);
      
      const user = userEvent.setup();
      render(<App />);
      
      await user.click(screen.getByText('Search Nearby'));
      
      await waitFor(() => {
        expect(screen.getByText('First Result')).toBeInTheDocument();
      });
      
      // Second search
      const secondResponse = {
        data: [{ applicant: 'Second Result', status: 'EXPIRED', address: '456 Ave', latitude: 0, longitude: 0, zipcodes: '' }]
      };
      mockedAxios.post.mockResolvedValueOnce(secondResponse);
      
      await user.click(screen.getByText('Search Applicant/Address'));
      
      await waitFor(() => {
        expect(screen.getByText('Second Result')).toBeInTheDocument();
        expect(screen.queryByText('First Result')).not.toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    test('handles empty search results', async () => {
      const mockResponse = { data: [] };
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      const user = userEvent.setup();
      render(<App />);
      
      await user.click(screen.getByText('Search Nearby'));
      
      await waitFor(() => {
        expect(screen.getByText('No results found.')).toBeInTheDocument();
      });
    });

    test('can perform search with empty input fields', async () => {
      const mockResponse = { data: [] };
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      const user = userEvent.setup();
      render(<App />);
      
      // Don't fill any inputs, just click search
      await user.click(screen.getByText('Search Nearby'));
      
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'https://my-flask-app-688153142575.us-central1.run.app/search_nearby',
          {
            latitude: '',
            longitude: '',
            statuses: []
          }
        );
      });
    });
  });
});