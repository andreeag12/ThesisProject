import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  Alert,
  ActivityIndicator,
  StyleSheet,
  Pressable,
} from 'react-native';
import { getReservations, deleteReservation } from './api/reserveService';

const ReservationList = ({ route }) => {
  const userEmail = route.params?.email || '';
  const [reservations, setReservations] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchReservations = async () => {
    setLoading(true);
    const result = await getReservations(userEmail);
    if (result.success) {
      setReservations(result.data);
      console.log('Fetched reservations:', result.data);
    } else {
      Alert.alert('Error', 'Failed to fetch reservations');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchReservations();
  }, []);

  const handleDelete = (reservationId) => {
    Alert.alert(
      'Confirm Delete',
      'Are you sure you want to delete this reservation?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            const result = await deleteReservation(reservationId);
            if (result.success) {
              Alert.alert('Deleted', 'Reservation deleted successfully');
              fetchReservations();
            } else {
              Alert.alert('Error', 'Failed to delete reservation');
            }
          },
        },
      ]
    );
  };

const renderItem = ({ item }) => (
  <View style={styles.itemContainer}>
    <Text style={styles.text}>Date: {item.date}</Text>
    <Text style={styles.text}>Car Plate Number: {item.car_plate}</Text>
    <Text style={styles.text}>Start Time: {item.hour_range[0]}</Text>
    <Text style={styles.text}>End Time: {item.hour_range[1]}</Text>
    <Pressable
      style={styles.button}
      onPress={() => handleDelete(item.reservation_id)}
    >
      <Text style={styles.buttonText}>Delete</Text>
    </Pressable>
  </View>
);

  if (loading) {
    return (
      <ActivityIndicator
        size="large"
        color="#4CAF50"
        style={{ flex: 1, justifyContent: 'center' }}
      />
    );
  }

  if (reservations.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.text}>No reservations found.</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={reservations}
      keyExtractor={(item) => item.reservation_id}
      renderItem={renderItem}
      contentContainerStyle={styles.container}
    />
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: '#282c34', 
    flexGrow: 1,
  },
  itemContainer: {
    borderColor: '#ddd',
    borderWidth: 1,
    borderRadius: 5,
    padding: 15,
    marginBottom: 15,
    backgroundColor: 'white',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  text: {
    marginBottom: 5,
    color: '#333',
    fontSize: 16,
  },
  button: {
    marginTop: 10,
    backgroundColor: '#4CAF50', // Green button
    paddingVertical: 10,
    borderRadius: 5,
    alignItems: 'center',
  },
  buttonText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 16,
  },
});

export default ReservationList;
