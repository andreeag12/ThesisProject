import { getStoredToken } from './authService';  // import the token helper
const API_BASE_URL = 'http://192.168.1.7:8000';

export const makeReservation = async (reservationData) => {
  try {
    const { token, tokenType } = await getStoredToken();

    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE_URL}/reservations/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `${tokenType} ${token}`,
      },
      body: JSON.stringify(reservationData),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Reservation failed');
    }

    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const getReservations = async (userEmail) => {
  try {
    const { token, tokenType } = await getStoredToken();

    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${API_BASE_URL}/reservations/?email=${encodeURIComponent(userEmail)}`, {
      method: 'GET',
      headers: {
        'Authorization': `${tokenType} ${token}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to fetch reservations');
    }

    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const deleteReservation = async (reservationId) => {
  try {
    const { token, tokenType } = await getStoredToken();

    if (!token) throw new Error('Not authenticated');

    // Fix: encode reservationId to safely use in URL
    const encodedId = encodeURIComponent(reservationId);

    const response = await fetch(`${API_BASE_URL}/reservations/${encodedId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `${tokenType} ${token}`,
      },
    });

    if (response.status === 204) {
      return { success: true };
    } else {
      const data = await response.json();
      throw new Error(data.detail || 'Failed to delete reservation');
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
};
