import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View } from 'react-native';
import AppNavigator from './src/navigation/AppNavigator';
import { Colors } from './src/constants/Colors';

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar style="light" backgroundColor={Colors.primary} />
      <AppNavigator />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
});

