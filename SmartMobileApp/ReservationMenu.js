import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const ReservationMenu = ({ navigation, route }) => {
  const userEmail = route.params?.email || '';

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('Reservation', { email: userEmail })}
      >
        <Text style={styles.buttonText}>Make Reservation</Text>
      </TouchableOpacity>

      <View style={{ height: 20 }} />

      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('ReservationList', { email: userEmail })}
      >
        <Text style={styles.buttonText}>View Reservations</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#282c34', // dark background as in other screens
    justifyContent: 'center',
    padding: 20,
  },
  button: {
    backgroundColor: '#9acd32', // green color consistent with other screens
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default ReservationMenu;
