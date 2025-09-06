import React, { useState, useEffect } from 'react';
import { View, Text, Button, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Picker } from '@react-native-picker/picker';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useFocusEffect } from '@react-navigation/native';
import { makeReservation } from './api/reserveService';

const Reservation = ({ route }) => {
  const userEmail = route.params?.email || '';

  const [carPlateIds, setCarPlateIds] = useState([]);
  const [selectedCarPlateId, setSelectedCarPlateId] = useState('');

  const parkingSpotId = 1;

  const [reservationDate, setReservationDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);

  // Store hours and minutes separately for precise control
  const [startHour, setStartHour] = useState(new Date().getHours());
  const [startMinute, setStartMinute] = useState(new Date().getMinutes());

  const [durationHours, setDurationHours] = useState(1);
  const [durationMinutes, setDurationMinutes] = useState(0);

  const [loading, setLoading] = useState(false);

  const loadProfile = async () => {
    if (!userEmail) {
      setCarPlateIds([]);
      setSelectedCarPlateId('');
      return;
    }

    try {
      const key = `userProfile_${userEmail.toLowerCase()}`;
      const profileString = await AsyncStorage.getItem(key);

      if (profileString) {
        const profile = JSON.parse(profileString);
        if (profile.carPlateIds && profile.carPlateIds.length > 0) {
          setCarPlateIds(profile.carPlateIds);
          setSelectedCarPlateId(profile.carPlateIds[0]);
        } else {
          setCarPlateIds([]);
          setSelectedCarPlateId('');
        }
      } else {
        setCarPlateIds([]);
        setSelectedCarPlateId('');
      }
    } catch (error) {
      console.error('Failed to load user profile:', error);
    }
  };

  useEffect(() => {
    loadProfile();
    const now = new Date();
    setStartHour(now.getHours());
    setStartMinute(now.getMinutes());
  }, [userEmail]);

  useFocusEffect(
    React.useCallback(() => {
      loadProfile();
    }, [userEmail])
  );

  const onChangeDate = (event, selectedDate) => {
    setShowDatePicker(false);
    if (selectedDate) {
      setReservationDate(selectedDate);
    }
  };

  const formatTime = (dateObj) => {
    const h = dateObj.getHours().toString().padStart(2, '0');
    const m = dateObj.getMinutes().toString().padStart(2, '0');
    const s = '00';
    return `${h}:${m}:${s}`;
  };

  const handleReservation = async () => {
    if (!selectedCarPlateId) {
      Alert.alert('Validation Error', 'Please select a car plate ID.');
      return;
    }

    if (durationHours === 0 && durationMinutes === 0) {
      Alert.alert('Validation Error', 'Please select a duration greater than 0.');
      return;
    }

    setLoading(true);

    try {
      const startDateTime = new Date(reservationDate);
      startDateTime.setHours(startHour);
      startDateTime.setMinutes(startMinute);
      startDateTime.setSeconds(0);
      startDateTime.setMilliseconds(0);

      const endTime = new Date(startDateTime);
      endTime.setHours(endTime.getHours() + durationHours);
      endTime.setMinutes(endTime.getMinutes() + durationMinutes);

      const reservationPayload = {
        email: userEmail,
        car_plate: selectedCarPlateId,
        parking_spot_id: parkingSpotId,
        date: reservationDate.toISOString().split('T')[0], // YYYY-MM-DD
        hour_range: [formatTime(startDateTime), formatTime(endTime)],
      };

      const result = await makeReservation(reservationPayload);

      if (result.success) {
        Alert.alert('Success', 'Reservation successful!');
      } else {
        Alert.alert('Error', `Reservation failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      Alert.alert('Error', `Unexpected error: ${error.message || error}`);
    } finally {
      setLoading(false);
    }
  };

  const hourOptions = [...Array(24).keys()];
  const minuteOptions = [...Array(60).keys()]; // 0 to 59

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Select Car Plate ID:</Text>
      <View style={styles.pickerContainer}>
        <Picker
          selectedValue={selectedCarPlateId}
          onValueChange={(itemValue) => setSelectedCarPlateId(itemValue)}
          style={styles.picker}
        >
          {carPlateIds.length > 0 ? (
            carPlateIds.map((plateId, index) => (
              <Picker.Item key={index} label={plateId} value={plateId} />
            ))
          ) : (
            <Picker.Item label="No car plates found" value="" />
          )}
        </Picker>
      </View>

      <Text style={styles.label}>Select Reservation Date:</Text>
      <Button
        title={reservationDate.toDateString()}
        onPress={() => setShowDatePicker(true)}
        color="#9acd32"
      />
      {showDatePicker && (
        <DateTimePicker
          value={reservationDate}
          mode="date"
          display="default"
          onChange={onChangeDate}
          minimumDate={new Date()}
        />
      )}

      <Text style={styles.label}>Select Start Time:</Text>
      <View style={styles.timePickerRow}>
        <Picker
          selectedValue={startHour}
          onValueChange={(hour) => setStartHour(hour)}
          style={styles.smallPicker}
        >
          {hourOptions.map((h) => (
            <Picker.Item key={h} label={`${h}:00`} value={h} />
          ))}
        </Picker>

        <Picker
          selectedValue={startMinute}
          onValueChange={(minute) => setStartMinute(minute)}
          style={styles.smallPicker}
        >
          {minuteOptions.map((m) => (
            <Picker.Item key={m} label={m.toString().padStart(2, '0')} value={m} />
          ))}
        </Picker>
      </View>

      <Text style={styles.label}>Select Duration:</Text>
      <View style={styles.timePickerRow}>
        <Picker
          selectedValue={durationHours}
          onValueChange={setDurationHours}
          style={styles.smallPicker}
        >
          {[...Array(24).keys()].map((h) => (
            <Picker.Item key={h} label={`${h}h`} value={h} />
          ))}
        </Picker>
        <Picker
          selectedValue={durationMinutes}
          onValueChange={setDurationMinutes}
          style={styles.smallPicker}
        >
          {[...Array(60).keys()].map((m) => (
            <Picker.Item key={m} label={m.toString().padStart(2, '0')} value={m} />
          ))}
        </Picker>
      </View>

      <View style={{ marginTop: 20 }}>
        {loading ? (
          <ActivityIndicator size="large" color="#9acd32" />
        ) : (
          <Button
            title="Make Reservation"
            onPress={handleReservation}
            color="#9acd32"
            disabled={
              !selectedCarPlateId ||
              (durationHours === 0 && durationMinutes === 0)
            }
          />
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#282c34',
    padding: 20,
  },
  label: {
    fontWeight: 'bold',
    fontSize: 18,
    color: 'white',
    marginBottom: 10,
    marginTop: 15,
  },
  pickerContainer: {
    borderColor: 'gray',
    borderWidth: 1,
    borderRadius: 5,
    backgroundColor: 'white',
  },
  picker: {
    height: 50,
    width: '100%',
  },
  timePickerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  smallPicker: {
    height: 50,
    width: '48%',
    backgroundColor: 'white',
  },
});

export default Reservation;
