import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import { PhoneIcon, KeyIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

const LoginPage = () => {
  const [step, setStep] = useState('phone'); // 'phone' or 'otp'
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [countdown, setCountdown] = useState(0);

  const { login, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  // Countdown timer for resend
  React.useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

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
      await axios.post('/users/auth/login', { phone_number: phone });
      setStep('otp');
      setCountdown(60);
      toast.success('تم الإرسال', 'تم إرسال رمز التحقق إلى رقم هاتفك');
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || 'حدث خطأ أثناء إرسال رمز التحقق';
      setErrors({ phone: errorMessage });
      toast.error('خطأ', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();

    if (!otp || otp.length !== 6) {
      setErrors({ otp: 'يرجى إدخال رمز التحقق المكون من 6 أرقام' });
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      const response = await axios.post('/users/auth/verify', {
        phone_number: phone,
        code: otp,
        platform: 'web'
      });

      // استخدام دالة login من AuthContext
      const result = await login({
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
        user: response.data.user
      });

      if (result.success) {
        toast.success('تم تسجيل الدخول بنجاح', `مرحباً ${response.data.user.first_name || 'بك'}!`);
        navigate(from, { replace: true });
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || 'رمز التحقق غير صحيح أو منتهي الصلاحية';
      setErrors({ otp: errorMessage });
      toast.error('خطأ', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (countdown > 0) return;

    setLoading(true);
    try {
      await axios.post('/users/auth/login', { phone_number: phone });
      setCountdown(60);
      setOtp('');
      toast.success('تم الإرسال', 'تم إرسال رمز تحقق جديد');
    } catch (error) {
      toast.error('خطأ', 'فشل إرسال رمز التحقق');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mb-6">
            {step === 'phone' ? (
              <PhoneIcon className="h-8 w-8 text-white" />
            ) : (
              <KeyIcon className="h-8 w-8 text-white" />
            )}
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {step === 'phone' ? 'تسجيل الدخول' : 'التحقق من الهاتف'}
          </h2>
          <p className="text-gray-600">
            {step === 'phone'
              ? 'ادخل رقم هاتفك لتسجيل الدخول'
              : `أدخل رمز التحقق المرسل إلى ${phone}`}
          </p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
          {step === 'phone' ? (
            <form className="space-y-6" onSubmit={handleSendOTP}>
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
                    type="tel"
                    inputMode="numeric"
                    value={phone}
                    onChange={(e) => {
                      setPhone(formatPhone(e.target.value));
                      setErrors({});
                    }}
                    className={`input-field pr-10 text-left dir-ltr ${errors.phone ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''}`}
                    placeholder="05xxxxxxxx"
                    maxLength={10}
                  />
                </div>
                {errors.phone && (
                  <p className="mt-2 text-sm text-red-600">{errors.phone}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary flex items-center justify-center"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white ml-2"></div>
                    جاري الإرسال...
                  </div>
                ) : (
                  'إرسال رمز التحقق'
                )}
              </button>
            </form>
          ) : (
            <form className="space-y-6" onSubmit={handleVerifyOTP}>
              <div>
                <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-2">
                  رمز التحقق
                </label>
                <input
                  id="otp"
                  type="text"
                  inputMode="numeric"
                  value={otp}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                    setOtp(value);
                    setErrors({});
                  }}
                  className={`input-field text-center text-2xl tracking-widest ${errors.otp ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''}`}
                  placeholder="000000"
                  maxLength={6}
                  autoComplete="one-time-code"
                />
                {errors.otp && (
                  <p className="mt-2 text-sm text-red-600">{errors.otp}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading || otp.length !== 6}
                className="w-full btn-primary flex items-center justify-center"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white ml-2"></div>
                    جاري التحقق...
                  </div>
                ) : (
                  'تسجيل الدخول'
                )}
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
                <button
                  type="button"
                  onClick={() => {
                    setStep('phone');
                    setOtp('');
                    setErrors({});
                  }}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  تغيير رقم الهاتف
                </button>
              </div>
            </form>
          )}

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">أو</span>
            </div>
          </div>

          {/* Register Link */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              ليس لديك حساب؟{' '}
              <Link
                to="/register"
                className="font-medium text-blue-600 hover:text-blue-700"
              >
                إنشاء حساب جديد
              </Link>
            </p>
          </div>
        </div>

        {/* Additional Info */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            بتسجيل الدخول، أنت توافق على{' '}
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

export default LoginPage;
