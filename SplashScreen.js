import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  Image,
  Dimensions,
} from 'react-native';
import { Colors, Spacing, FontSizes } from '../constants/Colors';

const { width, height } = Dimensions.get('window');

const SplashScreen = ({ navigation }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      navigation.replace('Main');
    }, 3000);

    return () => clearTimeout(timer);
  }, [navigation]);

  return (
    <View style={styles.container}>
      <View style={styles.logoContainer}>
        <View style={styles.iconContainer}>
          <View style={styles.buildingIcon}>
            <View style={styles.brick} />
            <View style={styles.brick} />
            <View style={styles.brick} />
          </View>
        </View>
        <Text style={styles.appName}>مواد البناء</Text>
        <Text style={styles.subtitle}>منصة مواد البناء الشاملة</Text>
      </View>
      
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.secondary} />
        <Text style={styles.loadingText}>جاري التحميل...</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: Spacing.lg,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: Spacing.xxl * 2,
  },
  iconContainer: {
    width: 120,
    height: 120,
    backgroundColor: Colors.white,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.lg,
    shadowColor: Colors.black,
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  buildingIcon: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    width: 60,
    height: 60,
  },
  brick: {
    width: 18,
    height: 18,
    backgroundColor: Colors.secondary,
    margin: 1,
    borderRadius: 2,
  },
  appName: {
    fontSize: FontSizes.xxxl,
    fontWeight: 'bold',
    color: Colors.white,
    textAlign: 'center',
    marginBottom: Spacing.sm,
  },
  subtitle: {
    fontSize: FontSizes.lg,
    color: Colors.white,
    textAlign: 'center',
    opacity: 0.9,
  },
  loadingContainer: {
    position: 'absolute',
    bottom: Spacing.xxl * 2,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: FontSizes.md,
    color: Colors.white,
    marginTop: Spacing.md,
    opacity: 0.8,
  },
});

export default SplashScreen;

