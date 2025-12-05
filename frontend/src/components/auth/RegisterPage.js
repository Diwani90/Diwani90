import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import { 
  EyeIcon, 
  EyeSlashIcon, 
  EnvelopeIcon, 
  LockClosedIcon,
  UserIcon,
  PhoneIcon,
  BuildingOfficeIcon,
  MapPinIcon
} from '@heroicons/react/24/outline';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone: '',
    role: 'customer',
    // Customer fields
    delivery_address: '',
    city: '',
    // Supplier fields
    company_name: '',
    commercial_registration: '',
    tax_number: '',
    business_description: '',
    categories: [],
    location: null
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [categories, setCategories] = useState([]);
  
  const { register, loading, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Fetch categories for suppliers
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axios.get('/stores/categories');
        setCategories(response.data || []);
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };
    fetchCategories();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (type === 'checkbox' && name === 'categories') {
      setFormData(prev => ({
        ...prev,
        categories: checked 
          ? [...prev.categories, value]
          : prev.categories.filter(cat => cat !== value)
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Common validations
    if (!formData.full_name.trim()) {
      newErrors.full_name = 'الاسم الكامل مطلوب';
    }

    if (!formData.email) {
      newErrors.email = 'البريد الإلكتروني مطلوب';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'البريد الإلكتروني غير صحيح';
    }

    if (!formData.phone.trim()) {
      newErrors.phone = 'رقم الهاتف مطلوب';
    } else if (!/^(\+966|0)?[5-9]\d{8}$/.test(formData.phone.replace(/\s/g, ''))) {
      newErrors.phone = 'رقم الهاتف غير صحيح';
    }

    if (!formData.password) {
      newErrors.password = 'كلمة المرور مطلوبة';
    } else if (formData.password.length < 6) {
      newErrors.password = 'كلمة المرور يجب أن تكون 6 أحرف على الأقل';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'كلمات المرور غير متطابقة';
    }

    // Customer specific validations
    if (formData.role === 'customer') {
      if (!formData.delivery_address.trim()) {
        newErrors.delivery_address = 'عنوان التوصيل مطلوب';
      }
      if (!formData.city.trim()) {
        newErrors.city = 'المدينة مطلوبة';
      }
    }

    // Supplier specific validations
    if (formData.role === 'supplier') {
      if (!formData.company_name.trim()) {
        newErrors.company_name = 'اسم الشركة مطلوب';
      }
      if (!formData.commercial_registration.trim()) {
        newErrors.commercial_registration = 'السجل التجاري مطلوب';
      }
      if (!formData.business_description.trim()) {
        newErrors.business_description = 'وصف النشاط التجاري مطلوب';
      }
      if (formData.categories.length === 0) {
        newErrors.categories = 'يجب اختيار فئة واحدة على الأقل';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Prepare data for submission
    const submitData = { ...formData };
    delete submitData.confirmPassword;

    const result = await register(submitData);
    
    if (result.success) {
      toast.success('تم إنشاء الحساب بنجاح', 'مرحباً بك في منصة مواد البناء');
      navigate('/dashboard', { replace: true });
    } else {
      toast.error('خطأ في إنشاء الحساب', result.error);
    }
  };

  const saudiCities = [
    'الرياض', 'جدة', 'مكة المكرمة', 'المدينة المنورة', 'الدمام', 'الخبر', 'الظهران',
    'تبوك', 'بريدة', 'خميس مشيط', 'حائل', 'الجبيل', 'نجران', 'ينبع', 'أبها'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mb-6">
            <UserIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">إنشاء حساب جديد</h2>
          <p className="text-gray-600">انضم إلى منصة مواد البناء الرائدة</p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Role Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                نوع الحساب
              </label>
              <div className="grid grid-cols-2 gap-4">
                <label className={`relative flex items-center p-4 border-2 rounded-xl cursor-pointer transition-all ${
                  formData.role === 'customer' 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <input
                    type="radio"
                    name="role"
                    value="customer"
                    checked={formData.role === 'customer'}
                    onChange={handleChange}
                    className="sr-only"
                  />
                  <UserIcon className="h-6 w-6 ml-3 text-blue-600" />
                  <div>
                    <div className="font-semibold text-gray-900">عميل</div>
                    <div className="text-sm text-gray-500">أشتري مواد البناء</div>
                  </div>
                </label>
                <label className={`relative flex items-center p-4 border-2 rounded-xl cursor-pointer transition-all ${
                  formData.role === 'supplier' 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <input
                    type="radio"
                    name="role"
                    value="supplier"
                    checked={formData.role === 'supplier'}
                    onChange={handleChange}
                    className="sr-only"
                  />
                  <BuildingOfficeIcon className="h-6 w-6 ml-3 text-purple-600" />
                  <div>
                    <div className="font-semibold text-gray-900">مورد</div>
                    <div className="text-sm text-gray-500">أبيع مواد البناء</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Common Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Full Name */}
              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
                  الاسم الكامل
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <UserIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    value={formData.full_name}
                    onChange={handleChange}
                    className={`input-field pr-10 ${errors.full_name ? 'border-red-300' : ''}`}
                    placeholder="الاسم الكامل"
                  />
                </div>
                {errors.full_name && <p className="mt-1 text-sm text-red-600">{errors.full_name}</p>}
              </div>

              {/* Phone */}
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                  رقم الهاتف
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <PhoneIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={handleChange}
                    className={`input-field pr-10 ${errors.phone ? 'border-red-300' : ''}`}
                    placeholder="05xxxxxxxx"
                  />
                </div>
                {errors.phone && <p className="mt-1 text-sm text-red-600">{errors.phone}</p>}
              </div>
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                البريد الإلكتروني
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                  <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`input-field pr-10 ${errors.email ? 'border-red-300' : ''}`}
                  placeholder="example@domain.com"
                />
              </div>
              {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
            </div>

            {/* Password Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  كلمة المرور
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <LockClosedIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={handleChange}
                    className={`input-field pr-10 pl-10 ${errors.password ? 'border-red-300' : ''}`}
                    placeholder="كلمة المرور"
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 left-0 pl-3 flex items-center"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </button>
                </div>
                {errors.password && <p className="mt-1 text-sm text-red-600">{errors.password}</p>}
              </div>

              {/* Confirm Password */}
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  تأكيد كلمة المرور
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <LockClosedIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={`input-field pr-10 pl-10 ${errors.confirmPassword ? 'border-red-300' : ''}`}
                    placeholder="تأكيد كلمة المرور"
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 left-0 pl-3 flex items-center"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </button>
                </div>
                {errors.confirmPassword && <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>}
              </div>
            </div>

            {/* Customer Specific Fields */}
            {formData.role === 'customer' && (
              <div className="space-y-6 p-6 bg-blue-50 rounded-xl">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">معلومات العميل</h3>
                
                <div>
                  <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-2">
                    المدينة
                  </label>
                  <select
                    id="city"
                    name="city"
                    value={formData.city}
                    onChange={handleChange}
                    className={`input-field ${errors.city ? 'border-red-300' : ''}`}
                  >
                    <option value="">اختر المدينة</option>
                    {saudiCities.map(city => (
                      <option key={city} value={city}>{city}</option>
                    ))}
                  </select>
                  {errors.city && <p className="mt-1 text-sm text-red-600">{errors.city}</p>}
                </div>

                <div>
                  <label htmlFor="delivery_address" className="block text-sm font-medium text-gray-700 mb-2">
                    عنوان التوصيل
                  </label>
                  <textarea
                    id="delivery_address"
                    name="delivery_address"
                    rows={3}
                    value={formData.delivery_address}
                    onChange={handleChange}
                    className={`input-field ${errors.delivery_address ? 'border-red-300' : ''}`}
                    placeholder="العنوان التفصيلي للتوصيل"
                  />
                  {errors.delivery_address && <p className="mt-1 text-sm text-red-600">{errors.delivery_address}</p>}
                </div>
              </div>
            )}

            {/* Supplier Specific Fields */}
            {formData.role === 'supplier' && (
              <div className="space-y-6 p-6 bg-purple-50 rounded-xl">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">معلومات المورد</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-2">
                      اسم الشركة
                    </label>
                    <input
                      id="company_name"
                      name="company_name"
                      type="text"
                      value={formData.company_name}
                      onChange={handleChange}
                      className={`input-field ${errors.company_name ? 'border-red-300' : ''}`}
                      placeholder="اسم الشركة"
                    />
                    {errors.company_name && <p className="mt-1 text-sm text-red-600">{errors.company_name}</p>}
                  </div>

                  <div>
                    <label htmlFor="commercial_registration" className="block text-sm font-medium text-gray-700 mb-2">
                      السجل التجاري
                    </label>
                    <input
                      id="commercial_registration"
                      name="commercial_registration"
                      type="text"
                      value={formData.commercial_registration}
                      onChange={handleChange}
                      className={`input-field ${errors.commercial_registration ? 'border-red-300' : ''}`}
                      placeholder="رقم السجل التجاري"
                    />
                    {errors.commercial_registration && <p className="mt-1 text-sm text-red-600">{errors.commercial_registration}</p>}
                  </div>
                </div>

                <div>
                  <label htmlFor="tax_number" className="block text-sm font-medium text-gray-700 mb-2">
                    الرقم الضريبي (اختياري)
                  </label>
                  <input
                    id="tax_number"
                    name="tax_number"
                    type="text"
                    value={formData.tax_number}
                    onChange={handleChange}
                    className="input-field"
                    placeholder="الرقم الضريبي"
                  />
                </div>

                <div>
                  <label htmlFor="business_description" className="block text-sm font-medium text-gray-700 mb-2">
                    وصف النشاط التجاري
                  </label>
                  <textarea
                    id="business_description"
                    name="business_description"
                    rows={3}
                    value={formData.business_description}
                    onChange={handleChange}
                    className={`input-field ${errors.business_description ? 'border-red-300' : ''}`}
                    placeholder="اكتب وصفاً مختصراً عن نشاطك التجاري"
                  />
                  {errors.business_description && <p className="mt-1 text-sm text-red-600">{errors.business_description}</p>}
                </div>

                {/* Categories */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    فئات المنتجات التي تتعامل بها
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {categories.map((category) => (
                      <label key={category.id} className="flex items-center">
                        <input
                          type="checkbox"
                          name="categories"
                          value={category.id}
                          checked={formData.categories.includes(category.id)}
                          onChange={handleChange}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="mr-2 text-sm text-gray-700">{category.name}</span>
                      </label>
                    ))}
                  </div>
                  {errors.categories && <p className="mt-1 text-sm text-red-600">{errors.categories}</p>}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary flex items-center justify-center"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white ml-2"></div>
                  جاري إنشاء الحساب...
                </div>
              ) : (
                'إنشاء الحساب'
              )}
            </button>

            {/* Login Link */}
            <div className="text-center">
              <p className="text-sm text-gray-600">
                لديك حساب بالفعل؟{' '}
                <Link
                  to="/login"
                  className="font-medium text-blue-600 hover:text-blue-700"
                >
                  تسجيل الدخول
                </Link>
              </p>
            </div>
          </form>
        </div>

        {/* Terms */}
        <div className="text-center mt-6">
          <p className="text-xs text-gray-500">
            بإنشاء الحساب، أنت توافق على{' '}
            <Link to="/terms" className="text-blue-600 hover:text-blue-700">
              شروط الاستخدام
            </Link>{' '}
            و{' '}
            <Link to="/privacy" className="text-blue-600 hover:text-blue-700">
              سياسة الخصوصية
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;