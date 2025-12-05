import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import { PhoneIcon, LockClosedIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

const LoginPage = () => {
  const [step, setStep] = useState(1); // 1: phone, 2: otp
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [errors, setErrors] = useState({});
  const [countdown, setCountdown] = useState(0);
  const [otpLoading, setOtpLoading] = useState(false);

  const otpRefs = useRef([]);
  const { login, requestOTP, loading, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  // Countdown timer for resend OTP
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const validatePhone = () => {
    const phoneRegex = /^(\+966|0)?5[0-9]{8}$/;
    const cleanPhone = phone.replace(/\s/g, '');

    if (!cleanPhone) {
      setErrors({ phone: 'رقم الجوال مطلوب' });
      return false;
    }
    if (!phoneRegex.test(cleanPhone)) {
      setErrors({ phone: 'رقم الجوال غير صحيح' });
      return false;
    }
    setErrors({});
    return true;
  };

  const handleSendOTP = async () => {
    if (!validatePhone()) return;

    setOtpLoading(true);
    const result = await requestOTP(phone);
    setOtpLoading(false);

    if (result.success) {
      toast.success('تم إرسال رمز التحقق', 'تحقق من رسائل هاتفك');
      setStep(2);
      setCountdown(60); // 60 seconds countdown
      // Focus first OTP input
      setTimeout(() => otpRefs.current[0]?.focus(), 100);
    } else {
      toast.error('خطأ', result.error);
    }
  };

  const handleOtpChange = (index, value) => {
    // Only allow numbers
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, 6);
    if (/^\d+$/.test(pastedData)) {
      const newOtp = [...otp];
      for (let i = 0; i < pastedData.length; i++) {
        newOtp[i] = pastedData[i];
      }
      setOtp(newOtp);
      // Focus the next empty input or the last one
      const nextIndex = Math.min(pastedData.length, 5);
      otpRefs.current[nextIndex]?.focus();
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();

    const otpCode = otp.join('');
    if (otpCode.length !== 6) {
      setErrors({ otp: 'أدخل رمز التحقق كاملاً' });
      return;
    }

    const result = await login({ phone, otp: otpCode });

    if (result.success) {
      toast.success('تم تسجيل الدخول بنجاح', 'مرحباً بك في منصة ديواني');
      navigate(from, { replace: true });
    } else {
      toast.error('خطأ في تسجيل الدخول', result.error);
      setOtp(['', '', '', '', '', '']);
      otpRefs.current[0]?.focus();
    }
  };

  const handleResendOTP = async () => {
    if (countdown > 0) return;

    setOtpLoading(true);
    const result = await requestOTP(phone);
    setOtpLoading(false);

    if (result.success) {
      toast.success('تم إعادة إرسال رمز التحقق', 'تحقق من رسائل هاتفك');
      setCountdown(60);
      setOtp(['', '', '', '', '', '']);
      otpRefs.current[0]?.focus();
    } else {
      toast.error('خطأ', result.error);
    }
  };

  const handleBackToPhone = () => {
    setStep(1);
    setOtp(['', '', '', '', '', '']);
    setErrors({});
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mb-6">
            <LockClosedIcon className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">تسجيل الدخول</h2>
          <p className="text-gray-600">
            {step === 1
              ? 'أدخل رقم جوالك للمتابعة'
              : `أدخل رمز التحقق المرسل إلى ${phone}`
            }
          </p>
        </div>

        <div className="bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
          {step === 1 ? (
            // Step 1: Phone Number
            <div className="space-y-6">
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                  رقم الجوال
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <PhoneIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="phone"
                    type="tel"
                    value={phone}
                    onChange={(e) => {
                      setPhone(e.target.value);
                      if (errors.phone) setErrors({});
                    }}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendOTP()}
                    className={`input-field pr-10 text-left direction-ltr ${errors.phone ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''}`}
                    placeholder="05xxxxxxxx"
                    dir="ltr"
                  />
                </div>
                {errors.phone && (
                  <p className="mt-2 text-sm text-red-600">{errors.phone}</p>
                )}
              </div>

              <button
                type="button"
                onClick={handleSendOTP}
                disabled={otpLoading}
                className="w-full btn-primary flex items-center justify-center"
              >
                {otpLoading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white ml-2"></div>
                    جاري الإرسال...
                  </div>
                ) : (
                  'إرسال رمز التحقق'
                )}
              </button>
            </div>
          ) : (
            // Step 2: OTP Verification
            <form onSubmit={handleVerifyOTP} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-4 text-center">
                  رمز التحقق
                </label>
                <div className="flex justify-center gap-2" dir="ltr">
                  {otp.map((digit, index) => (
                    <input
                      key={index}
                      ref={(el) => (otpRefs.current[index] = el)}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(index, e)}
                      onPaste={handleOtpPaste}
                      className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                    />
                  ))}
                </div>
                {errors.otp && (
                  <p className="mt-2 text-sm text-red-600 text-center">{errors.otp}</p>
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
                    جاري التحقق...
                  </div>
                ) : (
                  'تسجيل الدخول'
                )}
              </button>

              <div className="flex items-center justify-between text-sm">
                <button
                  type="button"
                  onClick={handleBackToPhone}
                  className="text-gray-600 hover:text-gray-800"
                >
                  تغيير رقم الجوال
                </button>
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={countdown > 0 || otpLoading}
                  className={`flex items-center ${countdown > 0 ? 'text-gray-400' : 'text-blue-600 hover:text-blue-700'}`}
                >
                  <ArrowPathIcon className="h-4 w-4 ml-1" />
                  {countdown > 0 ? `إعادة الإرسال (${countdown})` : 'إعادة إرسال الرمز'}
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
