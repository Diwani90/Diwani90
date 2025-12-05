import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, FontSizes, BorderRadius } from '../constants/Colors';

const SearchScreen = ({ navigation }) => {
  const [searchText, setSearchText] = useState('');

  const handleSearch = () => {
    if (searchText.trim()) {
      navigation.navigate('Products', { search: searchText.trim() });
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>البحث</Text>
      </View>
      
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <TouchableOpacity onPress={handleSearch} style={styles.searchButton}>
            <Ionicons name="search" size={20} color={Colors.gray[500]} />
          </TouchableOpacity>
          <TextInput
            style={styles.searchInput}
            placeholder="ابحث عن المنتجات..."
            value={searchText}
            onChangeText={setSearchText}
            onSubmitEditing={handleSearch}
            textAlign="right"
          />
        </View>
      </View>

      <View style={styles.content}>
        <Ionicons name="search-outline" size={64} color={Colors.gray[400]} />
        <Text style={styles.text}>ابحث عن المنتجات التي تحتاجها</Text>
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
  searchContainer: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    backgroundColor: Colors.surface,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.lg,
    paddingHorizontal: Spacing.md,
    height: 48,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  searchButton: { padding: Spacing.sm },
  searchInput: {
    flex: 1,
    fontSize: FontSizes.md,
    color: Colors.text,
    textAlign: 'right',
  },
  content: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  text: { fontSize: FontSizes.lg, color: Colors.textSecondary, marginTop: Spacing.lg },
});

export default SearchScreen;

