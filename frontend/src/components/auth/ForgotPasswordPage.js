import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { PhoneIcon, ArrowRightIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { useToast } from '../ui/toast';
import axios from 'axios';

const ForgotPasswordPage = () => {
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const { toast } = useToast();
  const navigate = useNavigate();

  // تنسيق رقم الهاتف
  const formatPhone = (value) => {
    // إزالة كل شيء غير الأرقام
    let cleaned = value.replace(/\D/g, '');

    // إذا بدأ بـ 966، نزيله ونضيف 0
    if (cleaned.startsWith('966')) {
      cleaned = '0' + cleaned.slice(3);
    }

    // إذا بدأ بـ 5، نضيف 0
    if (cleaned.startsWith('5') && cleaned.length <= 9) {
      cleaned = '0' + cleaned;
    }

    return cleaned;
  };

  const validatePhone = (phoneNumber) => {
    // التحقق من صحة رقم الهاتف السعودي
    const cleaned = phoneNumber.replace(/\D/g, '');
    const saudiPhoneRegex = /^(05|5)\d{8}$/;
    return saudiPhoneRegex.test(cleaned) || (cleaned.startsWith('966') && cleaned.length === 12);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!phone) {
      setError('رقم الهاتف مطلوب');
      return;
    }

    if (!validatePhone(phone)) {
      setError('رقم الهاتف غير صحيح. يجب أن يكون رقم سعودي (مثال: 05xxxxxxxx)');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // إرسال OTP لرقم الهاتف (نفس endpoint تسجيل الدخول)
      await axios.post('/users/auth/login', { phone_number: phone });
      setSent(true);
      toast.success('تم الإرسال', 'تم إرسال رمز التحقق إلى رقم هاتفك');
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.response?.data?.detail || 'حدث خطأ أثناء إرسال الطلب';
      setError(errorMessage);
      toast.error('خطأ', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="mx-auto h-16 w-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mb-6">
              <CheckCircleIcon className="h-8 w-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">تم الإرسال!</h2>
            <p className="text-gray-600 mb-8">
              تم إرسال رمز التحقق إلى رقم هاتفك
              <br />
              <span className="font-medium text-blue-600 dir-ltr inline-block">{phone}</span>
            </p>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100 text-center">
            <p className="text-sm text-gray-600 mb-6">
              أدخل رمز التحقق المرسل لإعادة الدخول إلى حسابك.
              الرمز صالح لمدة 10 دقائق.
            </p>
            <div className="space-y-4">
              <button
                onClick={() => navigate('/login')}
                className="w-full btn-primary inline-flex items-center justify-center"
              >
                <ArrowRightIcon className="h-5 w-5 ml-2" />
                المتابعة لتسجيل الدخول
              </button>
              <button
                onClick={() => {
                  setSent(false);
                  setPhone('');
                }}
                className="w-full text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                إرسال رمز جديد
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mb-6">
            <PhoneIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">استعادة الحساب</h2>
          <p className="text-gray-600">أدخل رقم هاتفك وسنرسل لك رمز التحقق</p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
          <form className="space-y-6" onSubmit={handleSubmit}>
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
                    setError('');
                  }}
                  className={`input-field pr-10 text-left dir-ltr ${error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''}`}
                  placeholder="05xxxxxxxx"
                  maxLength={10}
                />
              </div>
              {error && (
                <p className="mt-2 text-sm text-red-600">{error}</p>
              )}
              <p className="mt-2 text-xs text-gray-500">
                أدخل رقم الهاتف المسجل في حسابك
              </p>
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

            <div className="text-center">
              <Link
                to="/login"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                العودة لتسجيل الدخول
              </Link>
            </div>
          </form>
        </div>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            ليس لديك حساب؟{' '}
            <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium">
              إنشاء حساب جديد
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
