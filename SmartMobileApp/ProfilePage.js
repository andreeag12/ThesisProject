import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { getCarPlates, addCarPlate, deleteCarPlate } from './api/plateService';  
import { updateUserProfile } from './api/authService'; 

const ProfilePage = ({ route, navigation }) => {
  const userFromParams = route.params?.user;

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [carPlateIds, setCarPlateIds] = useState([]);
  const [selectedCarPlateId, setSelectedCarPlateId] = useState('');

  // Compute storage key dynamically
  const storageKey = email ? `userProfile_${email.toLowerCase()}` : null;

  // Load user profile and car plates
  useEffect(() => {
    const loadUserData = async () => {
      try {
        let userEmail = userFromParams?.email || email;
        if (!userEmail) return;

        const key = `userProfile_${userEmail.toLowerCase()}`;
        let profile = null;

        const stored = await AsyncStorage.getItem(key);
        if (stored) {
          profile = JSON.parse(stored);
        } else if (userFromParams) {
          profile = {
            name: userFromParams.name || '',
            email: userFromParams.email || '',
            phoneNumber: userFromParams.phoneNumber || '',
            carPlateIds: userFromParams.carPlateIds || []
          };
          await AsyncStorage.setItem(key, JSON.stringify(profile));
        }

        if (profile) {
          setName(profile.name || '');
          setEmail(profile.email || '');
          setPhoneNumber(profile.phoneNumber || '');
        }

        // Load car plates from backend
        if (userEmail) {
          const plates = await getCarPlates(userEmail);
          setCarPlateIds(plates);
          setSelectedCarPlateId(plates[0] || '');
        }
      } catch (e) {
        console.error('Failed to load stored profile or car plates:', e);
      }
    };

    loadUserData();
  }, [userFromParams, email]);

  const saveProfile = async (updatedProfile) => {
    if (!storageKey) return;
    try {
      await AsyncStorage.setItem(storageKey, JSON.stringify(updatedProfile));
    } catch (e) {
      console.error('Failed to save profile:', e);
    }
  };

  const handleSave = async () => {
    if (!name || !email || !phoneNumber) {
      Alert.alert('Error', 'Name, email, and phone number are required.');
      return;
    }

    const filteredCarPlates = carPlateIds.filter((plate) => plate.trim() !== '');
    if (filteredCarPlates.length === 0) {
      Alert.alert('Error', 'Please add at least one valid car plate ID.');
      return;
    }

    const updatedProfile = { name, email, phoneNumber, carPlateIds: filteredCarPlates };

    try {
      // Update profile on backend
      const profileResult = await updateUserProfile(updatedProfile);
      if (!profileResult.success) {
        Alert.alert('Error', `Failed to update profile: ${profileResult.error}`);
        return;
      }

      // Sync car plates
      const existingPlates = await getCarPlates(email);
      for (const plate of filteredCarPlates) {
        if (!existingPlates.includes(plate)) {
          try {
            await addCarPlate(email, plate);
          } catch (addErr) {
            console.warn(`Failed to add plate ${plate}: ${addErr.message}`);
          }
        }
      }

      const syncedPlates = await getCarPlates(email);
      setCarPlateIds(syncedPlates);
      setSelectedCarPlateId(syncedPlates[0] || '');

      await saveProfile({ ...updatedProfile, carPlateIds: syncedPlates });

      Alert.alert('Success', 'Profile and car plates updated successfully!');
    } catch (error) {
      Alert.alert('Error', `Update failed: ${error.message}`);
    }
  };

  const handleAddCarPlateId = () => {
    setCarPlateIds((prev) => [...prev, '']);
    setSelectedCarPlateId('');
  };

  const handleUpdateCarPlateId = (text, index) => {
    const updated = [...carPlateIds];
    updated[index] = text;
    setCarPlateIds(updated);
    if (selectedCarPlateId === carPlateIds[index]) setSelectedCarPlateId(text);
  };

  const handleDeleteCarPlateId = async (index) => {
    try {
      const plateToDelete = carPlateIds[index];
      if (!email || !plateToDelete.trim()) {
        const updated = carPlateIds.filter((_, i) => i !== index);
        setCarPlateIds(updated);
        if (plateToDelete === selectedCarPlateId) setSelectedCarPlateId(updated[0] || '');
        return;
      }

      const updatedPlates = await deleteCarPlate(email, plateToDelete);

      setCarPlateIds(updatedPlates);
      setSelectedCarPlateId(updatedPlates[0] || '');
      Alert.alert('Success', 'Car plate deleted.');
    } catch (e) {
      Alert.alert('Error', `Failed to delete plate: ${e.message}`);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Name:</Text>
      <TextInput style={styles.input} value={name} onChangeText={setName} placeholder="Enter your name" />

      <Text style={styles.label}>Email:</Text>
      <TextInput
        style={styles.input}
        value={email}
        onChangeText={setEmail}
        placeholder="Enter your email"
        keyboardType="email-address"
        autoCapitalize="none"
      />

      <Text style={styles.label}>Phone Number:</Text>
      <TextInput
        style={styles.input}
        value={phoneNumber}
        onChangeText={setPhoneNumber}
        placeholder="Enter your phone number"
        keyboardType="phone-pad"
      />

      <Text style={styles.label}>Select Car Plate ID:</Text>
      <Picker selectedValue={selectedCarPlateId} style={styles.picker} onValueChange={setSelectedCarPlateId}>
        {carPlateIds.length > 0 ? (
          carPlateIds.map((plateId, idx) => <Picker.Item key={idx} label={plateId} value={plateId} />)
        ) : (
          <Picker.Item label="No car plates available" value="" />
        )}
      </Picker>

      <Text style={styles.label}>Add or Update Car Plate IDs:</Text>
      {carPlateIds.map((plateId, idx) => (
        <View key={idx} style={styles.carPlateRow}>
          <TextInput
            style={styles.input}
            value={plateId}
            onChangeText={(text) => handleUpdateCarPlateId(text, idx)}
            placeholder={`Enter car plate ID ${idx + 1}`}
          />
          <TouchableOpacity style={styles.deleteButton} onPress={() => handleDeleteCarPlateId(idx)}>
            <Text style={styles.deleteButtonText}>Delete</Text>
          </TouchableOpacity>
        </View>
      ))}

      <Button title="Add Car Plate ID" onPress={handleAddCarPlateId} color="#9acd32" />
      <View style={{ height: 20 }} />
      <Button title="Save" onPress={handleSave} color="#9acd32" />

      {email ? (
        <>
          <View style={{ height: 20 }} />
          <Button title="Go to Reservation" onPress={() => navigation.navigate('Reservation', { email })} color="#4682b4" />
        </>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 20, backgroundColor: '#282c34' },
  label: { fontSize: 18, fontWeight: 'bold', color: 'white', marginBottom: 10, alignSelf: 'flex-start' },
  input: { height: 40, width: '100%', borderColor: 'gray', borderWidth: 1, marginBottom: 20, paddingHorizontal: 10, backgroundColor: 'white' },
  picker: { height: 50, width: '100%', borderColor: 'gray', borderWidth: 1, marginBottom: 20, backgroundColor: 'white' },
  carPlateRow: { flexDirection: 'row', alignItems: 'center', width: '100%', marginBottom: 10 },
  deleteButton: { backgroundColor: '#ff6347', padding: 10, marginLeft: 10, borderRadius: 4 },
  deleteButtonText: { color: 'white' },
});

export default ProfilePage;
