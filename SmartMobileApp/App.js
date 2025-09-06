import React, { useEffect } from 'react';
import { SafeAreaView, Text, StyleSheet, Button, View, Image } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import LoginScreen from './LoginScreen';
import RegisterScreen from './RegisterScreen';
import ProfilePage from './ProfilePage';
import MenuScreen from './MenuScreen';
import Reservation from './Reservation';
import ReservationMenu from './ReservationMenu';    
import ReservationList from './ReservationList';       

import { syncPendingChanges } from './api/authService';

const Stack = createStackNavigator();

const WelcomeScreen = ({ navigation }) => (
  <SafeAreaView style={styles.container}>
    <Image source={require('./images/park.jpg')} style={styles.image} />
    <Text style={styles.title}>Welcome to My Private Parking App</Text>
    <View style={styles.buttonContainer}>
      <Button title="Login" onPress={() => navigation.navigate('Login')} color="#9acd32" />
      <View style={styles.buttonSpace} />
      <Button title="Register" onPress={() => navigation.navigate('Register')} color="#9acd32" />
    </View>
  </SafeAreaView>
);

const App = () => {
  useEffect(() => {
    syncPendingChanges();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <NavigationContainer>
        <Stack.Navigator initialRouteName="Welcome">
          <Stack.Screen name="Welcome" component={WelcomeScreen} />
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
          <Stack.Screen name="Profile" component={ProfilePage} />
          <Stack.Screen
            name="Menu"
            component={MenuScreen}
            options={{ headerLeft: () => null }} // hide back button here
          />
          <Stack.Screen name="ReservationMenu" component={ReservationMenu} options={{ title: 'Reservation' }} />
          <Stack.Screen name="Reservation" component={Reservation} options={{ title: 'Make Reservation' }} />
          <Stack.Screen name="ReservationList" component={ReservationList} options={{ title: 'My Reservations' }} />
        </Stack.Navigator>
      </NavigationContainer>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#282c34',
  },
  title: {
    fontSize: 30,
    textAlign: 'center',
    margin: 10,
    color: 'white',
  },
  image: {
    width: 250,
    height: 200,
    marginBottom: 20,
    marginTop: 10,
  },
  buttonContainer: {
    flexDirection: 'row',
    marginTop: 30,
  },
  buttonSpace: {
    width: 20,
  },
});

export default App;
