import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  PhoneIcon,
  KeyIcon,
  UserIcon,
  BuildingOfficeIcon,
  EnvelopeIcon,
  MapPinIcon,
  CheckCircleIcon,
  TruckIcon,
  IdentificationIcon
} from '@heroicons/react/24/outline';

const RegisterPage = () => {
  // خطوات التسجيل: phone -> otp -> details -> complete
  const [step, setStep] = useState('phone');
  const [userType, setUserType] = useState('customer'); // customer, vendor, or driver

  // بيانات المستخدم
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    // حقول العميل
    city: '',
    delivery_address: '',
    // حقول المورد
    company_name: '',
    commercial_register: '',
    tax_number: '',
    business_type: '',
    // حقول السائق
    national_id: '',
    license_number: '',
    license_expiry: '',
    vehicle_type: '',
    vehicle_model: '',
    vehicle_plate: '',
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [countdown, setCountdown] = useState(0);
  const [categories, setCategories] = useState([]);

  const { login, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  // إعادة التوجيه إذا كان مسجل
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // عداد إعادة الإرسال
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // جلب الفئات للموردين
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axios.get('/products/categories');
        setCategories(response.data || []);
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };
    if (userType === 'vendor') {
      fetchCategories();
    }
  }, [userType]);

  // تنسيق رقم الهاتف
  const formatPhone = (value) => {
    let cleaned = value.replace(/\D/g, '');
    if (cleaned.startsWith('966')) {
      cleaned = '0' + cleaned.slice(3);
    }
    if (cleaned.startsWith('5') && cleaned.length <= 9) {
      cleaned = '0' + cleaned;
    }
    return cleaned.slice(0, 10);
  };

  const validatePhone = (phoneNumber) => {
    const cleaned = phoneNumber.replace(/\D/g, '');
    return /^05\d{8}$/.test(cleaned);
  };

  // الخطوة 1: إرسال OTP
  const handleSendOTP = async (e) => {
    e.preventDefault();

    if (!phone) {
      setErrors({ phone: 'رقم الهاتف مطلوب' });
      return;
    }

    if (!validatePhone(phone)) {
      setErrors({ phone: 'رقم الهاتف غير صحيح. يجب أن يكون رقم سعودي (مثال: 05xxxxxxxx)' });
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      await axios.post('/users/auth/register/request-otp', {
        phone_number: phone,
        user_type: userType
      });
      setStep('otp');
      setCountdown(60);
      toast.success('تم الإرسال', 'تم إرسال رمز التحقق إلى رقم هاتفك');
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || 'حدث خطأ أثناء إرسال رمز التحقق';

      // إذا كان الرقم مسجل مسبقاً
      if (error.response?.status === 400 && errorMessage.includes('مسجل')) {
        setErrors({ phone: 'هذا الرقم مسجل مسبقاً. يرجى تسجيل الدخول بدلاً من ذلك.' });
      } else {
        setErrors({ phone: errorMessage });
      }
      toast.error('خطأ', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // الخطوة 2: التحقق من OTP
  const handleVerifyOTP = async (e) => {
    e.preventDefault();

    if (!otp || otp.length !== 6) {
      setErrors({ otp: 'يرجى إدخال رمز التحقق المكون من 6 أرقام' });
      return;
    }

    // التحقق من OTP يتم مع التسجيل النهائي
    setStep('details');
    setErrors({});
  };

  // الخطوة 3: إكمال التسجيل
  const handleRegister = async (e) => {
    e.preventDefault();

    // التحقق من الحقول المطلوبة
    const newErrors = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'الاسم الأول مطلوب';
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'الاسم الأخير مطلوب';
    }

    if (userType === 'vendor') {
      if (!formData.email) {
        newErrors.email = 'البريد الإلكتروني مطلوب للموردين';
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        newErrors.email = 'البريد الإلكتروني غير صحيح';
      }
      if (!formData.company_name.trim()) {
        newErrors.company_name = 'اسم الشركة مطلوب';
      }
    }

    if (userType === 'driver') {
      if (!formData.national_id.trim()) {
        newErrors.national_id = 'رقم الهوية مطلوب';
      } else if (!/^\d{10}$/.test(formData.national_id)) {
        newErrors.national_id = 'رقم الهوية يجب أن يكون 10 أرقام';
      }
      if (!formData.license_number.trim()) {
        newErrors.license_number = 'رقم رخصة القيادة مطلوب';
      }
      if (!formData.license_expiry) {
        newErrors.license_expiry = 'تاريخ انتهاء الرخصة مطلوب';
      } else {
        const expiryDate = new Date(formData.license_expiry);
        if (expiryDate < new Date()) {
          newErrors.license_expiry = 'رخصة القيادة منتهية الصلاحية';
        }
      }
      if (!formData.vehicle_type.trim()) {
        newErrors.vehicle_type = 'نوع المركبة مطلوب';
      }
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      let endpoint;
      if (userType === 'vendor') {
        endpoint = '/users/auth/register/vendor';
      } else if (userType === 'driver') {
        endpoint = '/users/auth/register/driver';
      } else {
        endpoint = '/users/auth/register/customer';
      }

      const registerData = {
        phone_number: phone,
        otp_code: otp,
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email || undefined,
        platform: 'web',
      };

      if (userType === 'vendor') {
        registerData.company_name = formData.company_name;
        registerData.commercial_register = formData.commercial_register || undefined;
        registerData.tax_number = formData.tax_number || undefined;
        registerData.business_type = formData.business_type || undefined;
      }

      if (userType === 'driver') {
        registerData.national_id = formData.national_id;
        registerData.license_number = formData.license_number;
        registerData.license_expiry = formData.license_expiry;
        registerData.vehicle_type = formData.vehicle_type;
        registerData.vehicle_model = formData.vehicle_model || undefined;
        registerData.vehicle_plate = formData.vehicle_plate || undefined;
      }

      const response = await axios.post(endpoint, registerData);

      // تسجيل الدخول تلقائياً
      const result = await login({
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
        user: response.data.user
      });

      if (result.success) {
        setStep('complete');
        toast.success('تم إنشاء الحساب بنجاح', `مرحباً ${formData.first_name}!`);
        setTimeout(() => navigate('/dashboard', { replace: true }), 2000);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || 'حدث خطأ أثناء إنشاء الحساب';

      // إذا كان OTP خاطئ
      if (errorMessage.includes('OTP') || errorMessage.includes('رمز')) {
        setStep('otp');
        setErrors({ otp: 'رمز التحقق غير صحيح أو منتهي الصلاحية' });
      } else {
        setErrors({ general: errorMessage });
      }
      toast.error('خطأ', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // إعادة إرسال OTP
  const handleResendOTP = async () => {
    if (countdown > 0) return;

    setLoading(true);
    try {
      await axios.post('/users/auth/register/request-otp', {
        phone_number: phone,
        user_type: userType
      });
      setCountdown(60);
      setOtp('');
      toast.success('تم الإرسال', 'تم إرسال رمز تحقق جديد');
    } catch (error) {
      toast.error('خطأ', 'فشل إرسال رمز التحقق');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const saudiCities = [
    'الرياض', 'جدة', 'مكة المكرمة', 'المدينة المنورة', 'الدمام', 'الخبر',
    'تبوك', 'بريدة', 'خميس مشيط', 'حائل', 'الجبيل', 'نجران', 'ينبع', 'أبها'
  ];

  // شاشة الإكمال
  if (step === 'complete') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-white to-blue-50 py-12 px-4">
        <div className="max-w-md w-full text-center">
          <div className="mx-auto h-20 w-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center mb-6">
            <CheckCircleIcon className="h-10 w-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">مرحباً بك في ديواني!</h2>
          <p className="text-gray-600 mb-8">تم إنشاء حسابك بنجاح. جاري تحويلك...</p>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mb-6">
            {step === 'phone' && <PhoneIcon className="h-8 w-8 text-white" />}
            {step === 'otp' && <KeyIcon className="h-8 w-8 text-white" />}
            {step === 'details' && <UserIcon className="h-8 w-8 text-white" />}
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {step === 'phone' && 'إنشاء حساب جديد'}
            {step === 'otp' && 'التحقق من الهاتف'}
            {step === 'details' && 'أكمل بياناتك'}
          </h2>
          <p className="text-gray-600">
            {step === 'phone' && 'انضم إلى منصة ديواني لمواد البناء'}
            {step === 'otp' && `أدخل رمز التحقق المرسل إلى ${phone}`}
            {step === 'details' && 'أدخل معلوماتك لإكمال التسجيل'}
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center space-x-4 space-x-reverse">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'phone' ? 'bg-blue-600 text-white' : 'bg-green-500 text-white'}`}>
              {step === 'phone' ? '1' : '✓'}
            </div>
            <div className={`w-16 h-1 ${step !== 'phone' ? 'bg-green-500' : 'bg-gray-300'}`}></div>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'otp' ? 'bg-blue-600 text-white' : step === 'details' ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'}`}>
              {step === 'details' ? '✓' : '2'}
            </div>
            <div className={`w-16 h-1 ${step === 'details' ? 'bg-green-500' : 'bg-gray-300'}`}></div>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'details' ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'}`}>
              3
            </div>
          </div>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
          {/* خطوة 1: رقم الهاتف ونوع الحساب */}
          {step === 'phone' && (
            <form className="space-y-6" onSubmit={handleSendOTP}>
              {/* نوع الحساب */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">نوع الحساب</label>
                <div className="grid grid-cols-3 gap-3">
                  <label className={`relative flex flex-col items-center p-4 border-2 rounded-xl cursor-pointer transition-all ${
                    userType === 'customer' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                  }`}>
                    <input
                      type="radio"
                      name="userType"
                      value="customer"
                      checked={userType === 'customer'}
                      onChange={(e) => setUserType(e.target.value)}
                      className="sr-only"
                    />
                    <UserIcon className="h-6 w-6 mb-2 text-blue-600" />
                    <div className="text-center">
                      <div className="font-semibold text-gray-900 text-sm">عميل</div>
                      <div className="text-xs text-gray-500">أشتري مواد البناء</div>
                    </div>
                  </label>
                  <label className={`relative flex flex-col items-center p-4 border-2 rounded-xl cursor-pointer transition-all ${
                    userType === 'vendor' ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-gray-300'
                  }`}>
                    <input
                      type="radio"
                      name="userType"
                      value="vendor"
                      checked={userType === 'vendor'}
                      onChange={(e) => setUserType(e.target.value)}
                      className="sr-only"
                    />
                    <BuildingOfficeIcon className="h-6 w-6 mb-2 text-purple-600" />
                    <div className="text-center">
                      <div className="font-semibold text-gray-900 text-sm">مورد</div>
                      <div className="text-xs text-gray-500">أبيع مواد البناء</div>
                    </div>
                  </label>
                  <label className={`relative flex flex-col items-center p-4 border-2 rounded-xl cursor-pointer transition-all ${
                    userType === 'driver' ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300'
                  }`}>
                    <input
                      type="radio"
                      name="userType"
                      value="driver"
                      checked={userType === 'driver'}
                      onChange={(e) => setUserType(e.target.value)}
                      className="sr-only"
                    />
                    <TruckIcon className="h-6 w-6 mb-2 text-green-600" />
                    <div className="text-center">
                      <div className="font-semibold text-gray-900 text-sm">سائق</div>
                      <div className="text-xs text-gray-500">أوصل الطلبات</div>
                    </div>
                  </label>
                </div>
              </div>

              {/* رقم الهاتف */}
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">رقم الهاتف</label>
                <div className="relative">
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <PhoneIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="phone"
                    type="tel"
                    inputMode="numeric"
                    value={phone}
                    onChange={(e) => {
                      setPhone(formatPhone(e.target.value));
                      setErrors({});
                    }}
                    className={`input-field pr-10 text-left dir-ltr ${errors.phone ? 'border-red-300' : ''}`}
                    placeholder="05xxxxxxxx"
                    maxLength={10}
                  />
                </div>
                {errors.phone && <p className="mt-2 text-sm text-red-600">{errors.phone}</p>}
              </div>

              <button type="submit" disabled={loading} className="w-full btn-primary">
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white ml-2"></div>
                    جاري الإرسال...
                  </span>
                ) : 'إرسال رمز التحقق'}
              </button>
            </form>
          )}

          {/* خطوة 2: التحقق من OTP */}
          {step === 'otp' && (
            <form className="space-y-6" onSubmit={handleVerifyOTP}>
              <div>
                <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-2">رمز التحقق</label>
                <input
                  id="otp"
                  type="text"
                  inputMode="numeric"
                  value={otp}
                  onChange={(e) => {
                    setOtp(e.target.value.replace(/\D/g, '').slice(0, 6));
                    setErrors({});
                  }}
                  className={`input-field text-center text-2xl tracking-widest ${errors.otp ? 'border-red-300' : ''}`}
                  placeholder="000000"
                  maxLength={6}
                  autoComplete="one-time-code"
                />
                {errors.otp && <p className="mt-2 text-sm text-red-600">{errors.otp}</p>}
              </div>

              <button type="submit" disabled={loading || otp.length !== 6} className="w-full btn-primary">
                {loading ? 'جاري التحقق...' : 'متابعة'}
              </button>

              <div className="text-center space-y-2">
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={countdown > 0 || loading}
                  className={`text-sm font-medium ${countdown > 0 ? 'text-gray-400' : 'text-blue-600 hover:text-blue-700'}`}
                >
                  {countdown > 0 ? `إعادة الإرسال بعد ${countdown} ثانية` : 'إعادة إرسال الرمز'}
                </button>
                <br />
                <button type="button" onClick={() => { setStep('phone'); setOtp(''); }} className="text-sm text-gray-500">
                  تغيير رقم الهاتف
                </button>
              </div>
            </form>
          )}

          {/* خطوة 3: البيانات الشخصية */}
          {step === 'details' && (
            <form className="space-y-6" onSubmit={handleRegister}>
              {errors.general && (
                <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">{errors.general}</div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-2">الاسم الأول</label>
                  <input
                    id="first_name"
                    name="first_name"
                    type="text"
                    value={formData.first_name}
                    onChange={handleChange}
                    className={`input-field ${errors.first_name ? 'border-red-300' : ''}`}
                    placeholder="الاسم الأول"
                  />
                  {errors.first_name && <p className="mt-1 text-sm text-red-600">{errors.first_name}</p>}
                </div>
                <div>
                  <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-2">الاسم الأخير</label>
                  <input
                    id="last_name"
                    name="last_name"
                    type="text"
                    value={formData.last_name}
                    onChange={handleChange}
                    className={`input-field ${errors.last_name ? 'border-red-300' : ''}`}
                    placeholder="الاسم الأخير"
                  />
                  {errors.last_name && <p className="mt-1 text-sm text-red-600">{errors.last_name}</p>}
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  البريد الإلكتروني {userType === 'customer' && <span className="text-gray-400">(اختياري)</span>}
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

              {/* حقول المورد */}
              {userType === 'vendor' && (
                <div className="space-y-4 p-4 bg-purple-50 rounded-xl">
                  <h3 className="font-semibold text-gray-900">معلومات الشركة</h3>
                  <div>
                    <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-2">اسم الشركة</label>
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
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="commercial_register" className="block text-sm font-medium text-gray-700 mb-2">السجل التجاري</label>
                      <input
                        id="commercial_register"
                        name="commercial_register"
                        type="text"
                        value={formData.commercial_register}
                        onChange={handleChange}
                        className="input-field"
                        placeholder="رقم السجل"
                      />
                    </div>
                    <div>
                      <label htmlFor="tax_number" className="block text-sm font-medium text-gray-700 mb-2">الرقم الضريبي</label>
                      <input
                        id="tax_number"
                        name="tax_number"
                        type="text"
                        value={formData.tax_number}
                        onChange={handleChange}
                        className="input-field"
                        placeholder="اختياري"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* حقول السائق */}
              {userType === 'driver' && (
                <div className="space-y-4 p-4 bg-green-50 rounded-xl">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <IdentificationIcon className="h-5 w-5 text-green-600" />
                    معلومات السائق
                  </h3>
                  <div>
                    <label htmlFor="national_id" className="block text-sm font-medium text-gray-700 mb-2">رقم الهوية الوطنية</label>
                    <input
                      id="national_id"
                      name="national_id"
                      type="text"
                      inputMode="numeric"
                      value={formData.national_id}
                      onChange={handleChange}
                      className={`input-field ${errors.national_id ? 'border-red-300' : ''}`}
                      placeholder="10 أرقام"
                      maxLength={10}
                    />
                    {errors.national_id && <p className="mt-1 text-sm text-red-600">{errors.national_id}</p>}
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="license_number" className="block text-sm font-medium text-gray-700 mb-2">رقم رخصة القيادة</label>
                      <input
                        id="license_number"
                        name="license_number"
                        type="text"
                        value={formData.license_number}
                        onChange={handleChange}
                        className={`input-field ${errors.license_number ? 'border-red-300' : ''}`}
                        placeholder="رقم الرخصة"
                      />
                      {errors.license_number && <p className="mt-1 text-sm text-red-600">{errors.license_number}</p>}
                    </div>
                    <div>
                      <label htmlFor="license_expiry" className="block text-sm font-medium text-gray-700 mb-2">تاريخ انتهاء الرخصة</label>
                      <input
                        id="license_expiry"
                        name="license_expiry"
                        type="date"
                        value={formData.license_expiry}
                        onChange={handleChange}
                        className={`input-field ${errors.license_expiry ? 'border-red-300' : ''}`}
                        min={new Date().toISOString().split('T')[0]}
                      />
                      {errors.license_expiry && <p className="mt-1 text-sm text-red-600">{errors.license_expiry}</p>}
                    </div>
                  </div>
                  <h4 className="font-medium text-gray-800 mt-4 flex items-center gap-2">
                    <TruckIcon className="h-5 w-5 text-green-600" />
                    معلومات المركبة
                  </h4>
                  <div>
                    <label htmlFor="vehicle_type" className="block text-sm font-medium text-gray-700 mb-2">نوع المركبة</label>
                    <select
                      id="vehicle_type"
                      name="vehicle_type"
                      value={formData.vehicle_type}
                      onChange={handleChange}
                      className={`input-field ${errors.vehicle_type ? 'border-red-300' : ''}`}
                    >
                      <option value="">اختر نوع المركبة</option>
                      <option value="motorcycle">دراجة نارية</option>
                      <option value="car">سيارة صغيرة</option>
                      <option value="van">فان / سيارة عائلية</option>
                      <option value="pickup">بيك أب</option>
                      <option value="truck_small">شاحنة صغيرة</option>
                      <option value="truck_medium">شاحنة متوسطة</option>
                      <option value="truck_large">شاحنة كبيرة</option>
                    </select>
                    {errors.vehicle_type && <p className="mt-1 text-sm text-red-600">{errors.vehicle_type}</p>}
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="vehicle_model" className="block text-sm font-medium text-gray-700 mb-2">
                        موديل المركبة <span className="text-gray-400">(اختياري)</span>
                      </label>
                      <input
                        id="vehicle_model"
                        name="vehicle_model"
                        type="text"
                        value={formData.vehicle_model}
                        onChange={handleChange}
                        className="input-field"
                        placeholder="مثال: تويوتا هايلكس 2022"
                      />
                    </div>
                    <div>
                      <label htmlFor="vehicle_plate" className="block text-sm font-medium text-gray-700 mb-2">
                        رقم اللوحة <span className="text-gray-400">(اختياري)</span>
                      </label>
                      <input
                        id="vehicle_plate"
                        name="vehicle_plate"
                        type="text"
                        value={formData.vehicle_plate}
                        onChange={handleChange}
                        className="input-field"
                        placeholder="أ ب ج 1234"
                      />
                    </div>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mt-4">
                    <p className="text-sm text-yellow-800">
                      <strong>ملاحظة:</strong> سيتم مراجعة طلب التسجيل والتحقق من بياناتك قبل تفعيل حسابك كسائق.
                    </p>
                  </div>
                </div>
              )}

              <button type="submit" disabled={loading} className="w-full btn-primary">
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white ml-2"></div>
                    جاري إنشاء الحساب...
                  </span>
                ) : 'إنشاء الحساب'}
              </button>

              <button type="button" onClick={() => setStep('otp')} className="w-full text-sm text-gray-500 hover:text-gray-700">
                العودة للخطوة السابقة
              </button>
            </form>
          )}

          {/* رابط تسجيل الدخول */}
          {step !== 'complete' && (
            <>
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">أو</span>
                </div>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">
                  لديك حساب بالفعل؟{' '}
                  <Link to="/login" className="font-medium text-blue-600 hover:text-blue-700">تسجيل الدخول</Link>
                </p>
              </div>
            </>
          )}
        </div>

        {/* شروط الاستخدام */}
        {step !== 'complete' && (
          <div className="text-center mt-6">
            <p className="text-xs text-gray-500">
              بإنشاء الحساب، أنت توافق على{' '}
              <Link to="/terms" className="text-blue-600 hover:text-blue-700">شروط الاستخدام</Link>
              {' '}و{' '}
              <Link to="/privacy" className="text-blue-600 hover:text-blue-700">سياسة الخصوصية</Link>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default RegisterPage;
