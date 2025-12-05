import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing, FontSizes, BorderRadius } from '../constants/Colors';
import { apiService } from '../services/api';

const OrderFormScreen = ({ navigation, route }) => {
  const { product } = route.params;
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    customer_address: '',
    customer_type: 'individual',
    quantity: '1',
    notes: '',
  });
  const [loading, setLoading] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    // Validation
    if (!formData.customer_name || !formData.customer_email || !formData.customer_phone) {
      Alert.alert('خطأ', 'يرجى ملء جميع الحقول المطلوبة');
      return;
    }

    try {
      setLoading(true);
      const orderData = {
        ...formData,
        product_id: product.id,
        supplier_id: product.supplier_id,
        quantity: parseInt(formData.quantity),
      };

      await apiService.createOrder(orderData);
      Alert.alert(
        'تم الإرسال',
        'تم إرسال طلبك بنجاح. سيتواصل معك المورد قريباً.',
        [{ text: 'موافق', onPress: () => navigation.goBack() }]
      );
    } catch (error) {
      console.error('Error creating order:', error);
      Alert.alert('خطأ', 'حدث خطأ في إرسال الطلب');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-forward" size={24} color={Colors.white} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>إرسال طلب شراء</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Product Info */}
        <View style={styles.productCard}>
          <Text style={styles.productName}>{product.name}</Text>
          <Text style={styles.productPrice}>{product.price} ر.س</Text>
        </View>

        {/* Form */}
        <View style={styles.form}>
          <Text style={styles.formTitle}>معلومات العميل</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>اسم العميل *</Text>
            <TextInput
              style={styles.input}
              value={formData.customer_name}
              onChangeText={(value) => handleInputChange('customer_name', value)}
              placeholder="أدخل اسمك الكامل"
              textAlign="right"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>البريد الإلكتروني *</Text>
            <TextInput
              style={styles.input}
              value={formData.customer_email}
              onChangeText={(value) => handleInputChange('customer_email', value)}
              placeholder="example@email.com"
              keyboardType="email-address"
              textAlign="right"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>رقم الهاتف *</Text>
            <TextInput
              style={styles.input}
              value={formData.customer_phone}
              onChangeText={(value) => handleInputChange('customer_phone', value)}
              placeholder="05xxxxxxxx"
              keyboardType="phone-pad"
              textAlign="right"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>العنوان</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={formData.customer_address}
              onChangeText={(value) => handleInputChange('customer_address', value)}
              placeholder="أدخل عنوانك الكامل"
              multiline
              numberOfLines={3}
              textAlign="right"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>نوع العميل</Text>
            <View style={styles.radioGroup}>
              <TouchableOpacity
                style={[
                  styles.radioOption,
                  formData.customer_type === 'individual' && styles.radioOptionSelected
                ]}
                onPress={() => handleInputChange('customer_type', 'individual')}
              >
                <Text style={[
                  styles.radioText,
                  formData.customer_type === 'individual' && styles.radioTextSelected
                ]}>
                  فرد
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.radioOption,
                  formData.customer_type === 'company' && styles.radioOptionSelected
                ]}
                onPress={() => handleInputChange('customer_type', 'company')}
              >
                <Text style={[
                  styles.radioText,
                  formData.customer_type === 'company' && styles.radioTextSelected
                ]}>
                  شركة
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>الكمية المطلوبة</Text>
            <TextInput
              style={styles.input}
              value={formData.quantity}
              onChangeText={(value) => handleInputChange('quantity', value)}
              placeholder="1"
              keyboardType="numeric"
              textAlign="center"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>ملاحظات إضافية</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={formData.notes}
              onChangeText={(value) => handleInputChange('notes', value)}
              placeholder="أي ملاحظات أو متطلبات خاصة..."
              multiline
              numberOfLines={4}
              textAlign="right"
            />
          </View>
        </View>
      </ScrollView>

      {/* Submit Button */}
      <View style={styles.submitContainer}>
        <TouchableOpacity
          style={[styles.submitButton, loading && styles.submitButtonDisabled]}
          onPress={handleSubmit}
          disabled={loading}
        >
          <Text style={styles.submitButtonText}>
            {loading ? 'جاري الإرسال...' : 'إرسال الطلب'}
          </Text>
          {!loading && <Ionicons name="send" size={20} color={Colors.white} />}
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
  productCard: {
    backgroundColor: Colors.white,
    margin: Spacing.lg,
    padding: Spacing.lg,
    borderRadius: BorderRadius.lg,
    shadowColor: Colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  productName: {
    fontSize: FontSizes.lg,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.xs,
    textAlign: 'right',
  },
  productPrice: {
    fontSize: FontSizes.xl,
    fontWeight: 'bold',
    color: Colors.secondary,
    textAlign: 'right',
  },
  form: {
    padding: Spacing.lg,
  },
  formTitle: {
    fontSize: FontSizes.xl,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.lg,
    textAlign: 'right',
  },
  inputGroup: {
    marginBottom: Spacing.lg,
  },
  label: {
    fontSize: FontSizes.md,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: Spacing.sm,
    textAlign: 'right',
  },
  input: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    fontSize: FontSizes.md,
    backgroundColor: Colors.white,
    color: Colors.text,
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  radioGroup: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  radioOption: {
    flex: 1,
    backgroundColor: Colors.surface,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.lg,
    borderRadius: BorderRadius.md,
    marginHorizontal: Spacing.xs,
    alignItems: 'center',
  },
  radioOptionSelected: {
    backgroundColor: Colors.primary,
  },
  radioText: {
    fontSize: FontSizes.md,
    color: Colors.text,
    fontWeight: '600',
  },
  radioTextSelected: {
    color: Colors.white,
  },
  submitContainer: {
    padding: Spacing.lg,
    backgroundColor: Colors.white,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  submitButton: {
    backgroundColor: Colors.secondary,
    borderRadius: BorderRadius.lg,
    paddingVertical: Spacing.lg,
    paddingHorizontal: Spacing.xl,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: Colors.gray[400],
  },
  submitButtonText: {
    fontSize: FontSizes.lg,
    fontWeight: 'bold',
    color: Colors.white,
    marginLeft: Spacing.sm,
  },
});

export default OrderFormScreen;

