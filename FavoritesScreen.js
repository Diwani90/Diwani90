import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, FontSizes } from '../constants/Colors';

const FavoritesScreen = () => {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>المفضلة</Text>
      </View>
      <View style={styles.content}>
        <Ionicons name="heart-outline" size={64} color={Colors.gray[400]} />
        <Text style={styles.text}>لا توجد منتجات مفضلة</Text>
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
    alignItems: 'center',
  },
  headerTitle: { fontSize: FontSizes.xl, fontWeight: 'bold', color: Colors.white },
  content: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  text: { fontSize: FontSizes.lg, color: Colors.textSecondary, marginTop: Spacing.lg },
});

export default FavoritesScreen;

