import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, FontSizes, BorderRadius } from '../constants/Colors';
import { apiService } from '../services/api';

const ProductDetailScreen = ({ navigation, route }) => {
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const { productId } = route.params;

  useEffect(() => {
    loadProduct();
  }, []);

  const loadProduct = async () => {
    try {
      setLoading(true);
      const response = await apiService.getProduct(productId);
      setProduct(response.data);
    } catch (error) {
      console.error('Error loading product:', error);
      Alert.alert('خطأ', 'حدث خطأ في تحميل المنتج');
    } finally {
      setLoading(false);
    }
  };

  const handleOrderPress = () => {
    navigation.navigate('OrderForm', { product });
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>جاري التحميل...</Text>
      </View>
    );
  }

  if (!product) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>المنتج غير موجود</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-forward" size={24} color={Colors.white} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>تفاصيل المنتج</Text>
        <TouchableOpacity>
          <Ionicons name="heart-outline" size={24} color={Colors.white} />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Product Image */}
        <View style={styles.imageContainer}>
          <Ionicons name="cube-outline" size={120} color={Colors.gray[400]} />
        </View>

        {/* Product Info */}
        <View style={styles.productInfo}>
          <Text style={styles.productName}>{product.name}</Text>
          <Text style={styles.productPrice}>{product.price} ر.س</Text>
          
          {/* Supplier Info */}
          <TouchableOpacity 
            style={styles.supplierCard}
            onPress={() => navigation.navigate('SupplierProfile', { supplierId: product.supplier_id })}
          >
            <View style={styles.supplierInfo}>
              <Text style={styles.supplierName}>{product.supplier?.name}</Text>
              <Text style={styles.supplierCity}>{product.supplier?.city}</Text>
            </View>
            <View style={styles.ratingContainer}>
              <Ionicons name="star" size={16} color={Colors.warning} />
              <Text style={styles.rating}>{product.supplier?.rating}</Text>
            </View>
          </TouchableOpacity>

          {/* Description */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>الوصف</Text>
            <Text style={styles.description}>{product.description}</Text>
          </View>

          {/* Specifications */}
          {product.specifications && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>المواصفات</Text>
              {Object.entries(product.specifications).map(([key, value]) => (
                <View key={key} style={styles.specRow}>
                  <Text style={styles.specValue}>{value}</Text>
                  <Text style={styles.specKey}>{key}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Stock Info */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>معلومات المخزون</Text>
            <View style={styles.stockInfo}>
              <Text style={styles.stockText}>الكمية المتوفرة: {product.stock_quantity}</Text>
              <Text style={styles.unitText}>الوحدة: {product.unit}</Text>
              <Text style={styles.minOrderText}>الحد الأدنى للطلب: {product.minimum_order}</Text>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* Order Button */}
      <View style={styles.orderContainer}>
        <TouchableOpacity style={styles.orderButton} onPress={handleOrderPress}>
          <Text style={styles.orderButtonText}>إرسال طلب شراء</Text>
          <Ionicons name="send" size={20} color={Colors.white} />
        </TouchableOpacity>
      </View>
    </View>
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
  },
  loadingText: {
    marginTop: Spacing.md,
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: FontSizes.lg,
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
    fontSize: FontSizes.xl,
    fontWeight: 'bold',
    color: Colors.white,
  },
  content: {
    flex: 1,
  },
  imageContainer: {
    height: 250,
    backgroundColor: Colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  productInfo: {
    padding: Spacing.lg,
  },
  productName: {
    fontSize: FontSizes.xxl,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.sm,
    textAlign: 'right',
  },
  productPrice: {
    fontSize: FontSizes.xxxl,
    fontWeight: 'bold',
    color: Colors.secondary,
    marginBottom: Spacing.lg,
    textAlign: 'right',
  },
  supplierCard: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.lg,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
    textAlign: 'right',
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rating: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginLeft: Spacing.xs,
  },
  section: {
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: FontSizes.xl,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.md,
    textAlign: 'right',
  },
  description: {
    fontSize: FontSizes.md,
    color: Colors.text,
    lineHeight: 24,
    textAlign: 'right',
  },
  specRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  specKey: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
  },
  specValue: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  stockInfo: {
    backgroundColor: Colors.surface,
    borderRadius: BorderRadius.md,
    padding: Spacing.lg,
  },
  stockText: {
    fontSize: FontSizes.md,
    color: Colors.success,
    marginBottom: Spacing.xs,
    textAlign: 'right',
  },
  unitText: {
    fontSize: FontSizes.md,
    color: Colors.text,
    marginBottom: Spacing.xs,
    textAlign: 'right',
  },
  minOrderText: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    textAlign: 'right',
  },
  orderContainer: {
    padding: Spacing.lg,
    backgroundColor: Colors.white,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  orderButton: {
    backgroundColor: Colors.secondary,
    borderRadius: BorderRadius.lg,
    paddingVertical: Spacing.lg,
    paddingHorizontal: Spacing.xl,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  orderButtonText: {
    fontSize: FontSizes.lg,
    fontWeight: 'bold',
    color: Colors.white,
    marginLeft: Spacing.sm,
  },
});

export default ProductDetailScreen;

