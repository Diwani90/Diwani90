import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, FontSizes } from '../constants/Colors';

const SupplierProfileScreen = ({ navigation }) => {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-forward" size={24} color={Colors.white} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>ملف المورد</Text>
        <View style={{ width: 24 }} />
      </View>
      <View style={styles.content}>
        <Text style={styles.text}>شاشة ملف المورد قيد التطوير</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: {
    backgroundColor: Colors.primary,
    paddingTop: 50,
    paddingBottom: Spacing.lg,
    paddingHorizontal: Spacing.lg,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: { fontSize: FontSizes.xl, fontWeight: 'bold', color: Colors.white },
  content: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  text: { fontSize: FontSizes.lg, color: Colors.textSecondary },
});

export default SupplierProfileScreen;

