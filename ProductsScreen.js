import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, FontSizes, BorderRadius } from '../constants/Colors';
import { apiService } from '../services/api';

const ProductsScreen = ({ navigation, route }) => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchText, setSearchText] = useState(route.params?.search || '');
  const [selectedCategory, setSelectedCategory] = useState(route.params?.categoryId || null);
  const [showFilters, setShowFilters] = useState(false);
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');

  useEffect(() => {
    loadCategories();
    loadProducts();
  }, []);

  useEffect(() => {
    if (route.params?.search || route.params?.categoryId) {
      loadProducts();
    }
  }, [route.params]);

  const loadCategories = async () => {
    try {
      const response = await apiService.getCategories();
      setCategories(response.data || []);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadProducts = async () => {
    try {
      setLoading(true);
      const params = {};
      
      if (searchText) params.search = searchText;
      if (selectedCategory) params.category_id = selectedCategory;
      if (minPrice) params.min_price = minPrice;
      if (maxPrice) params.max_price = maxPrice;
      
      params.include_supplier = true;
      params.include_category = true;

      const response = await apiService.getProducts(params);
      setProducts(response.data || []);
    } catch (error) {
      console.error('Error loading products:', error);
      Alert.alert('خطأ', 'حدث خطأ في تحميل المنتجات');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadProducts();
  };

  const handleSearch = () => {
    loadProducts();
  };

  const handleProductPress = (product) => {
    navigation.navigate('ProductDetail', { productId: product.id });
  };

  const applyFilters = () => {
    setShowFilters(false);
    loadProducts();
  };

  const clearFilters = () => {
    setSelectedCategory(null);
    setMinPrice('');
    setMaxPrice('');
    setSearchText('');
    setShowFilters(false);
    loadProducts();
  };

  const renderProductItem = ({ item }) => (
    <TouchableOpacity
      style={styles.productCard}
      onPress={() => handleProductPress(item)}
    >
      <View style={styles.productImage}>
        <Ionicons name="cube-outline" size={50} color={Colors.gray[400]} />
      </View>
      
      <View style={styles.productInfo}>
        <Text style={styles.productName} numberOfLines={2}>{item.name}</Text>
        <Text style={styles.productPrice}>{item.price} ر.س</Text>
        
        <View style={styles.productMeta}>
          <Text style={styles.supplierName}>{item.supplier?.name}</Text>
          <Text style={styles.categoryName}>{item.category?.name}</Text>
        </View>
        
        <View style={styles.productFooter}>
          <Text style={styles.stockText}>متوفر: {item.stock_quantity}</Text>
          <TouchableOpacity style={styles.favoriteButton}>
            <Ionicons name="heart-outline" size={20} color={Colors.gray[500]} />
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );

  const renderFilterModal = () => (
    <Modal
      visible={showFilters}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setShowFilters(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>فلترة المنتجات</Text>
            <TouchableOpacity onPress={() => setShowFilters(false)}>
              <Ionicons name="close" size={24} color={Colors.text} />
            </TouchableOpacity>
          </View>

          {/* Category Filter */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>الفئة</Text>
            <FlatList
              data={categories}
              horizontal
              showsHorizontalScrollIndicator={false}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={[
                    styles.categoryChip,
                    selectedCategory === item.id && styles.categoryChipSelected
                  ]}
                  onPress={() => setSelectedCategory(
                    selectedCategory === item.id ? null : item.id
                  )}
                >
                  <Text style={[
                    styles.categoryChipText,
                    selectedCategory === item.id && styles.categoryChipTextSelected
                  ]}>
                    {item.name}
                  </Text>
                </TouchableOpacity>
              )}
              keyExtractor={(item) => item.id.toString()}
            />
          </View>

          {/* Price Filter */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>نطاق السعر</Text>
            <View style={styles.priceInputs}>
              <TextInput
                style={styles.priceInput}
                placeholder="الحد الأدنى"
                value={minPrice}
                onChangeText={setMinPrice}
                keyboardType="numeric"
                textAlign="center"
              />
              <Text style={styles.priceSeparator}>إلى</Text>
              <TextInput
                style={styles.priceInput}
                placeholder="الحد الأقصى"
                value={maxPrice}
                onChangeText={setMaxPrice}
                keyboardType="numeric"
                textAlign="center"
              />
            </View>
          </View>

          <View style={styles.modalActions}>
            <TouchableOpacity style={styles.clearButton} onPress={clearFilters}>
              <Text style={styles.clearButtonText}>مسح الفلاتر</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.applyButton} onPress={applyFilters}>
              <Text style={styles.applyButtonText}>تطبيق</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-forward" size={24} color={Colors.white} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {route.params?.categoryName || 'المنتجات'}
        </Text>
        <TouchableOpacity onPress={() => setShowFilters(true)}>
          <Ionicons name="filter" size={24} color={Colors.white} />
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

      {/* Products List */}
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>جاري التحميل...</Text>
        </View>
      ) : (
        <FlatList
          data={products}
          renderItem={renderProductItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.productsList}
          refreshing={refreshing}
          onRefresh={handleRefresh}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Ionicons name="cube-outline" size={64} color={Colors.gray[400]} />
              <Text style={styles.emptyText}>لا توجد منتجات</Text>
              <Text style={styles.emptySubtext}>جرب تغيير معايير البحث</Text>
            </View>
          }
        />
      )}

      {renderFilterModal()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
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
    fontSize: FontSizes.xl,
    fontWeight: 'bold',
    color: Colors.white,
  },
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
  searchButton: {
    padding: Spacing.sm,
  },
  searchInput: {
    flex: 1,
    fontSize: FontSizes.md,
    color: Colors.text,
    textAlign: 'right',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: Spacing.md,
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  productsList: {
    padding: Spacing.lg,
  },
  productCard: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.md,
    flexDirection: 'row',
    shadowColor: Colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  productImage: {
    width: 80,
    height: 80,
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: Spacing.md,
  },
  productInfo: {
    flex: 1,
  },
  productName: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.xs,
    textAlign: 'right',
  },
  productPrice: {
    fontSize: FontSizes.xl,
    fontWeight: 'bold',
    color: Colors.secondary,
    marginBottom: Spacing.sm,
    textAlign: 'right',
  },
  productMeta: {
    marginBottom: Spacing.sm,
  },
  supplierName: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
    textAlign: 'right',
  },
  categoryName: {
    fontSize: FontSizes.sm,
    color: Colors.primary,
    textAlign: 'right',
  },
  productFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stockText: {
    fontSize: FontSizes.sm,
    color: Colors.success,
  },
  favoriteButton: {
    padding: Spacing.xs,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Spacing.xxl * 2,
  },
  emptyText: {
    fontSize: FontSizes.xl,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginTop: Spacing.lg,
    marginBottom: Spacing.sm,
  },
  emptySubtext: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.white,
    borderTopLeftRadius: BorderRadius.xl,
    borderTopRightRadius: BorderRadius.xl,
    padding: Spacing.lg,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  modalTitle: {
    fontSize: FontSizes.xl,
    fontWeight: 'bold',
    color: Colors.text,
  },
  filterSection: {
    marginBottom: Spacing.lg,
  },
  filterLabel: {
    fontSize: FontSizes.lg,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.md,
    textAlign: 'right',
  },
  categoryChip: {
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.full,
    marginLeft: Spacing.sm,
  },
  categoryChipSelected: {
    backgroundColor: Colors.primary,
  },
  categoryChipText: {
    fontSize: FontSizes.md,
    color: Colors.text,
  },
  categoryChipTextSelected: {
    color: Colors.white,
  },
  priceInputs: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  priceInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    fontSize: FontSizes.md,
    backgroundColor: Colors.white,
  },
  priceSeparator: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    marginHorizontal: Spacing.md,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: Spacing.lg,
  },
  clearButton: {
    flex: 1,
    backgroundColor: Colors.gray[200],
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.md,
    marginLeft: Spacing.sm,
  },
  clearButtonText: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
  },
  applyButton: {
    flex: 1,
    backgroundColor: Colors.primary,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.md,
    marginRight: Spacing.sm,
  },
  applyButtonText: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.white,
    textAlign: 'center',
  },
});

export default ProductsScreen;

