import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Alert } from 'react-native';
import { CommonActions, useNavigation, useRoute } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const MenuScreen = () => {
  const navigation = useNavigation();
  const route = useRoute();

  const user = route.params?.user || null;

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            // Clear only tokens/session, NOT user profile data
            await AsyncStorage.removeItem('authToken'); // if you have token saved

            navigation.dispatch(
              CommonActions.reset({
                index: 0,
                routes: [{ name: 'Welcome' }],
              })
            );
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('Profile', { user })}
      >
        <Image source={require('./images/user.png')} style={styles.image} />
        <Text style={styles.buttonText}>My Profile</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.button}
        onPress={() => {
          if (user?.email) {
            navigation.navigate('ReservationMenu', { email: user.email });
          } else {
            Alert.alert('Error', 'No user logged in or email not found.');
          }
        }}
      >
        <Image source={require('./images/reservation.png')} style={styles.image} />
        <Text style={styles.buttonText}>Reservation</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#282c34',
  },
  button: {
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#9acd32',
    borderRadius: 10,
    padding: 20,
    margin: 10,
    width: 200,
    height: 200,
    position: 'relative',
  },
  image: {
    width: 120,
    height: 120,
    marginBottom: 10,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 18,
  },
  logoutButton: {
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ff4d4d',
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 20,
    margin: 10,
    width: 200,
    height: 60,
  },
  logoutText: {
    color: '#ffffff',
    fontSize: 18,
  },
});

export default MenuScreen;
