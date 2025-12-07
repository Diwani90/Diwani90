import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheckIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

const PrivacyPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-green-600 to-emerald-600 rounded-2xl flex items-center justify-center mb-6">
            <ShieldCheckIcon className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">سياسة الخصوصية</h1>
          <p className="text-gray-600">آخر تحديث: ديسمبر 2024</p>
        </div>

        {/* Content */}
        <div className="bg-white rounded-2xl shadow-lg p-8 space-y-8">
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">1. مقدمة</h2>
            <p className="text-gray-600 leading-relaxed">
              نحن في منصة ديواني نقدر خصوصيتك ونلتزم بحماية بياناتك الشخصية.
              توضح هذه السياسة كيفية جمعنا واستخدامنا وحمايتنا لمعلوماتك.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">2. البيانات التي نجمعها</h2>
            <p className="text-gray-600 leading-relaxed mb-4">نقوم بجمع الأنواع التالية من البيانات:</p>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li><strong>بيانات التسجيل:</strong> الاسم، رقم الهاتف، البريد الإلكتروني</li>
              <li><strong>بيانات الملف الشخصي:</strong> العنوان، التفضيلات، الصورة الشخصية</li>
              <li><strong>بيانات المعاملات:</strong> تاريخ الطلبات، المدفوعات</li>
              <li><strong>بيانات الاستخدام:</strong> كيفية تفاعلك مع المنصة</li>
              <li><strong>بيانات الجهاز:</strong> نوع الجهاز، عنوان IP، نظام التشغيل</li>
              <li><strong>بيانات الموقع:</strong> لتحديد عنوان التوصيل (بموافقتك)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">3. كيف نستخدم بياناتك</h2>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>معالجة طلباتك وتوصيلها</li>
              <li>التواصل معك بشأن طلباتك وحسابك</li>
              <li>تحسين خدماتنا ومنتجاتنا</li>
              <li>إرسال العروض والتحديثات (بموافقتك)</li>
              <li>منع الاحتيال وضمان الأمان</li>
              <li>الامتثال للمتطلبات القانونية</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">4. مشاركة البيانات</h2>
            <p className="text-gray-600 leading-relaxed mb-4">قد نشارك بياناتك مع:</p>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li><strong>الموردين:</strong> لتنفيذ طلباتك</li>
              <li><strong>شركات التوصيل:</strong> لتوصيل طلباتك</li>
              <li><strong>مزودي خدمات الدفع:</strong> لمعالجة المدفوعات</li>
              <li><strong>الجهات القانونية:</strong> عند الاقتضاء بموجب القانون</li>
            </ul>
            <p className="text-gray-600 leading-relaxed mt-4">
              لن نبيع بياناتك الشخصية لأي طرف ثالث لأغراض تسويقية.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">5. أمان البيانات</h2>
            <p className="text-gray-600 leading-relaxed">
              نستخدم تدابير أمنية متقدمة لحماية بياناتك، بما في ذلك:
            </p>
            <ul className="list-disc list-inside text-gray-600 space-y-2 mt-4">
              <li>تشفير SSL لجميع البيانات المنقولة</li>
              <li>تشفير البيانات الحساسة في قواعد البيانات</li>
              <li>مراقبة أمنية على مدار الساعة</li>
              <li>سياسات صارمة للوصول إلى البيانات</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">6. حقوقك</h2>
            <p className="text-gray-600 leading-relaxed mb-4">لديك الحق في:</p>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>الوصول إلى بياناتك الشخصية</li>
              <li>تصحيح البيانات غير الدقيقة</li>
              <li>طلب حذف بياناتك</li>
              <li>الاعتراض على معالجة بياناتك</li>
              <li>نقل بياناتك لمزود آخر</li>
              <li>سحب موافقتك في أي وقت</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">7. ملفات تعريف الارتباط (Cookies)</h2>
            <p className="text-gray-600 leading-relaxed">
              نستخدم ملفات تعريف الارتباط لتحسين تجربتك على المنصة. يمكنك
              التحكم في إعدادات ملفات تعريف الارتباط من خلال متصفحك.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">8. الاحتفاظ بالبيانات</h2>
            <p className="text-gray-600 leading-relaxed">
              نحتفظ ببياناتك طالما كان حسابك نشطاً أو حسب الحاجة لتقديم
              خدماتنا. قد نحتفظ ببعض البيانات لفترة أطول للامتثال للمتطلبات
              القانونية أو لحل النزاعات.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">9. خصوصية الأطفال</h2>
            <p className="text-gray-600 leading-relaxed">
              خدماتنا غير موجهة للأشخاص دون سن 18 عاماً. لا نجمع بيانات
              من القاصرين عن قصد.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">10. التغييرات على هذه السياسة</h2>
            <p className="text-gray-600 leading-relaxed">
              قد نحدث هذه السياسة من وقت لآخر. سنخطرك بأي تغييرات جوهرية
              عبر البريد الإلكتروني أو إشعار على المنصة.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">11. الاتصال بنا</h2>
            <p className="text-gray-600 leading-relaxed">
              إذا كان لديك أي استفسارات حول سياسة الخصوصية هذه، يرجى التواصل معنا:
            </p>
            <ul className="list-disc list-inside text-gray-600 space-y-2 mt-4">
              <li>البريد الإلكتروني: privacy@diwani.sa</li>
              <li>الهاتف: 920000000</li>
            </ul>
          </section>
        </div>

        {/* Back Link */}
        <div className="text-center mt-8">
          <Link
            to="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium"
          >
            <ArrowRightIcon className="h-5 w-5 ml-2" />
            العودة للرئيسية
          </Link>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPage;
