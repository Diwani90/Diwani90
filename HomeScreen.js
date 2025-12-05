import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  FlatList,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, FontSizes, BorderRadius } from '../constants/Colors';
import { apiService } from '../services/api';

const HomeScreen = ({ navigation }) => {
  const [categories, setCategories] = useState([]);
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [featuredSuppliers, setFeaturedSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [categoriesRes, productsRes, suppliersRes] = await Promise.all([
        apiService.getMainCategories(),
        apiService.getFeaturedProducts(),
        apiService.getFeaturedSuppliers(),
      ]);

      setCategories(categoriesRes.data || []);
      setFeaturedProducts(productsRes.data || []);
      setFeaturedSuppliers(suppliersRes.data || []);
    } catch (error) {
      console.error('Error loading data:', error);
      Alert.alert('خطأ', 'حدث خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (searchText.trim()) {
      navigation.navigate('Products', { search: searchText.trim() });
    }
  };

  const handleCategoryPress = (category) => {
    navigation.navigate('Products', { categoryId: category.id, categoryName: category.name });
  };

  const handleProductPress = (product) => {
    navigation.navigate('ProductDetail', { productId: product.id });
  };

  const handleSupplierPress = (supplier) => {
    navigation.navigate('SupplierProfile', { supplierId: supplier.id });
  };

  const renderCategoryItem = ({ item }) => (
    <TouchableOpacity
      style={styles.categoryCard}
      onPress={() => handleCategoryPress(item)}
    >
      <View style={styles.categoryIcon}>
        <Ionicons 
          name={getCategoryIcon(item.icon)} 
          size={32} 
          color={Colors.primary} 
        />
      </View>
      <Text style={styles.categoryName}>{item.name}</Text>
      <Text style={styles.categoryCount}>{item.products_count} منتج</Text>
    </TouchableOpacity>
  );

  const renderProductItem = ({ item }) => (
    <TouchableOpacity
      style={styles.productCard}
      onPress={() => handleProductPress(item)}
    >
      <View style={styles.productImage}>
        <Ionicons name="cube-outline" size={40} color={Colors.gray[400]} />
      </View>
      <Text style={styles.productName} numberOfLines={2}>{item.name}</Text>
      <Text style={styles.productPrice}>{item.price} ر.س</Text>
      <Text style={styles.productSupplier}>{item.supplier?.name}</Text>
    </TouchableOpacity>
  );

  const renderSupplierItem = ({ item }) => (
    <TouchableOpacity
      style={styles.supplierCard}
      onPress={() => handleSupplierPress(item)}
    >
      <View style={styles.supplierInfo}>
        <Text style={styles.supplierName}>{item.name}</Text>
        <Text style={styles.supplierCity}>{item.city}</Text>
        <View style={styles.ratingContainer}>
          <Ionicons name="star" size={16} color={Colors.warning} />
          <Text style={styles.rating}>{item.rating}</Text>
          <Text style={styles.reviewsCount}>({item.reviews_count} تقييم)</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  const getCategoryIcon = (iconName) => {
    const iconMap = {
      'Building2': 'business-outline',
      'Hammer': 'hammer-outline',
      'Brick': 'cube-outline',
      'Shield': 'shield-outline',
      'Door': 'door-outline',
      'Grid': 'grid-outline',
      'Wrench': 'build-outline',
      'Zap': 'flash-outline',
    };
    return iconMap[iconName] || 'cube-outline';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>جاري التحميل...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>مواد البناء</Text>
        <TouchableOpacity style={styles.menuButton}>
          <Ionicons name="menu" size={24} color={Colors.white} />
        </TouchableOpacity>
      </View>

      {/* Search Bar */}
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

      {/* Categories */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>الفئات الرئيسية</Text>
        <FlatList
          data={categories}
          renderItem={renderCategoryItem}
          keyExtractor={(item) => item.id.toString()}
          numColumns={2}
          scrollEnabled={false}
          contentContainerStyle={styles.categoriesGrid}
        />
      </View>

      {/* Featured Products */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>منتجات مميزة</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Products')}>
            <Text style={styles.seeAllText}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <FlatList
          data={featuredProducts}
          renderItem={renderProductItem}
          keyExtractor={(item) => item.id.toString()}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.horizontalList}
        />
      </View>

      {/* Featured Suppliers */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>موردون مميزون</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Suppliers')}>
            <Text style={styles.seeAllText}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <FlatList
          data={featuredSuppliers}
          renderItem={renderSupplierItem}
          keyExtractor={(item) => item.id.toString()}
          scrollEnabled={false}
        />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
  },
  loadingText: {
    marginTop: Spacing.md,
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  header: {
    backgroundColor: Colors.primary,
    paddingTop: 50,
    paddingBottom: Spacing.lg,
    paddingHorizontal: Spacing.lg,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: FontSizes.xxl,
    fontWeight: 'bold',
    color: Colors.white,
  },
  menuButton: {
    padding: Spacing.sm,
  },
  searchContainer: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    backgroundColor: Colors.primary,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.lg,
    paddingHorizontal: Spacing.md,
    height: 48,
  },
  searchButton: {
    padding: Spacing.sm,
  },
  searchInput: {
    flex: 1,
    fontSize: FontSizes.md,
    color: Colors.text,
    textAlign: 'right',
  },
  section: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  sectionTitle: {
    fontSize: FontSizes.xl,
    fontWeight: 'bold',
    color: Colors.text,
  },
  seeAllText: {
    fontSize: FontSizes.md,
    color: Colors.secondary,
    fontWeight: '600',
  },
  categoriesGrid: {
    gap: Spacing.md,
  },
  categoryCard: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    alignItems: 'center',
    marginHorizontal: Spacing.xs,
    marginVertical: Spacing.xs,
    shadowColor: Colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  categoryIcon: {
    width: 60,
    height: 60,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  categoryName: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
    marginBottom: Spacing.xs,
  },
  categoryCount: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  horizontalList: {
    paddingRight: Spacing.lg,
  },
  productCard: {
    width: 160,
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginLeft: Spacing.md,
    shadowColor: Colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  productImage: {
    width: '100%',
    height: 100,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  productName: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
    textAlign: 'right',
  },
  productPrice: {
    fontSize: FontSizes.lg,
    fontWeight: 'bold',
    color: Colors.secondary,
    marginBottom: Spacing.xs,
    textAlign: 'right',
  },
  productSupplier: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    textAlign: 'right',
  },
  supplierCard: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.md,
    shadowColor: Colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  supplierInfo: {
    flex: 1,
  },
  supplierName: {
    fontSize: FontSizes.lg,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.xs,
    textAlign: 'right',
  },
  supplierCity: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    textAlign: 'right',
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  rating: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginLeft: Spacing.xs,
  },
  reviewsCount: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginLeft: Spacing.xs,
  },
});

export default HomeScreen;

