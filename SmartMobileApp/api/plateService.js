import AsyncStorage from '@react-native-async-storage/async-storage';
import { getStoredToken } from './authService'; 

const API_BASE_URL = 'http://192.168.1.7:8000';
const carPlateKey = (email) => `userCarPlates_${email.toLowerCase()}`;

export const getCarPlates = async (email) => {
  try {
    const response = await fetch(`${API_BASE_URL}/car-plates/${email}`);
    if (!response.ok) throw new Error('Failed to fetch car plates');
    const data = await response.json();
    await AsyncStorage.setItem(carPlateKey(email), JSON.stringify(data.car_plate_ids || []));
    return data.car_plate_ids || [];
  } catch {
    // fallback to local storage
    const local = await AsyncStorage.getItem(carPlateKey(email));
    return local ? JSON.parse(local) : [];
  }
};

export const addCarPlate = async (email, plate) => {
  const { token, tokenType } = await getStoredToken();
  if (!token) throw new Error('Not authenticated');

  const response = await fetch(`${API_BASE_URL}/car-plates/${email}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `${tokenType} ${token}`,
    },
    body: JSON.stringify({ new_plate: plate }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Add plate failed');
  }

  // update local storage
  const plates = await getCarPlates(email);
  plates.push(plate);
  await AsyncStorage.setItem(carPlateKey(email), JSON.stringify(plates));
  return plates;
};

export const deleteCarPlate = async (email, plate) => {
  const { token, tokenType } = await getStoredToken();
  if (!token) throw new Error('Not authenticated');

  const response = await fetch(`${API_BASE_URL}/car-plates/${email}/${plate}`, {
    method: 'DELETE',
    headers: { 'Authorization': `${tokenType} ${token}` },
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Delete plate failed');
  }

  // update local storage
  let plates = await getCarPlates(email);
  plates = plates.filter(p => p !== plate);
  await AsyncStorage.setItem(carPlateKey(email), JSON.stringify(plates));
  return plates;
};
