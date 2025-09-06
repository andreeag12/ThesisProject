import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://192.168.1.7:8000';

// Helper: build profile key from email
const profileKey = (email) => `userProfile_${email.toLowerCase()}`;

// Register user
export const registerUser = async (userData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: userData.name,
        email: userData.email,
        phone: userData.phone,
        car_plate_ids: userData.car_plate_ids || [],
        role: userData.role || 'user',
        password: userData.password
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Registration failed');
    }

    // Save user profile locally keyed by email
    await AsyncStorage.setItem(profileKey(userData.email), JSON.stringify({
      name: userData.name,
      email: userData.email,
      phoneNumber: userData.phone,
      carPlateIds: userData.car_plate_ids || [],
    }));

    return {
      success: true,
      data: data,
      message: data.message
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Login user
export const loginUser = async (email, password) => {
  try {
    const response = await fetch(`${API_BASE_URL}/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    // Store token
    await AsyncStorage.setItem('access_token', data.access_token);
    await AsyncStorage.setItem('token_type', data.token_type);

    // Save user profile locally keyed by email
    if (data.user) {
      await AsyncStorage.setItem(profileKey(data.user.email), JSON.stringify({
        name: data.user.name,
        email: data.user.email,
        phoneNumber: data.user.phone,
        carPlateIds: data.user.car_plate_ids || [],
      }));
    }

    return {
      success: true,
      token: data.access_token,
      tokenType: data.token_type
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

// Update user profile on backend and locally
export const updateUserProfile = async (profileData) => {
  try {
    const { token, tokenType } = await getStoredToken();
    if (!token) throw new Error('No authentication token found');

    const response = await fetch(`${API_BASE_URL}/profile/update/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `${tokenType} ${token}`,
      },
      body: JSON.stringify({
        name: profileData.name,
        email: profileData.email,
        phone: profileData.phoneNumber,
        car_plate_ids: profileData.carPlateIds || [],
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Profile update failed');
    }

    // Update profile locally keyed by email
    await AsyncStorage.setItem(profileKey(profileData.email), JSON.stringify({
      name: profileData.name,
      email: profileData.email,
      phoneNumber: profileData.phoneNumber,
      carPlateIds: profileData.carPlateIds,
    }));

    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Get stored token
export const getStoredToken = async () => {
  try {
    const token = await AsyncStorage.getItem('access_token');
    const tokenType = await AsyncStorage.getItem('token_type');
    return { token, tokenType };
  } catch (error) {
    console.error('Error getting stored token:', error);
    return { token: null, tokenType: null };
  }
};

// Logout user (clear token and current user profile)
export const logoutUser = async () => {
  try {
    // Get current token and user email from stored profile or decode token if needed
    const token = await AsyncStorage.getItem('access_token');

    // Try to get current user email from stored profile keys or saved somewhere else if you track current user email
    // For now, clear all tokens and optionally clear all userProfiles or let profiles persist

    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('token_type');
    // Optionally: don't remove user profiles to keep them persistent per user
    // await AsyncStorage.clear(); // if you want to clear everything, but likely you don't want that

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Check if user is authenticated
export const isAuthenticated = async () => {
  const { token } = await getStoredToken();
  return token !== null;
};

// Make authenticated requests
export const makeAuthenticatedRequest = async (url, options = {}) => {
  const { token, tokenType } = await getStoredToken();

  if (!token) {
    throw new Error('No authentication token found');
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `${tokenType} ${token}`,
    ...options.headers
  };

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (response.status === 401) {
    // Token expired or invalid, logout user
    await logoutUser();
    throw new Error('Authentication expired. Please login again.');
  }

  return response;
};

// New helper: get user profile by email from AsyncStorage
export const getUserProfile = async (email) => {
  try {
    const profileJson = await AsyncStorage.getItem(profileKey(email));
    return profileJson ? JSON.parse(profileJson) : null;
  } catch (error) {
    console.error('Error loading user profile:', error);
    return null;
  }
};

// Sync any pending changes stored locally (e.g., when offline)
export const syncPendingChanges = async () => {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const profileKeys = keys.filter(key => key.startsWith('userProfile_'));

    for (const key of profileKeys) {
      const profileJson = await AsyncStorage.getItem(key);
      const profile = JSON.parse(profileJson);

      // Only sync profiles marked as needing sync
      if (profile && profile.needsSync) {
        const { token, tokenType } = await getStoredToken();
        if (!token) continue;

        const response = await fetch(`${API_BASE_URL}/profile/update/`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `${tokenType} ${token}`,
          },
          body: JSON.stringify({
            name: profile.name,
            email: profile.email,
            phone: profile.phoneNumber,
            car_plate_ids: profile.carPlateIds || [],
          }),
        });

        const data = await response.json();

        if (response.ok) {
          await AsyncStorage.setItem(key, JSON.stringify({
            ...profile,
            carPlateIds: data.car_plate_ids || [],
            needsSync: false,
          }));
        } else {
          console.warn(`Failed to sync profile ${key}:`, data.detail || data);
        }
      }
    }
  } catch (error) {
    console.error('syncPendingChanges error:', error);
  }
};
