import React from 'react';
import { Link } from 'react-router-dom';
import { DocumentTextIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

const TermsPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mb-6">
            <DocumentTextIcon className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">شروط الاستخدام</h1>
          <p className="text-gray-600">آخر تحديث: ديسمبر 2024</p>
        </div>

        {/* Content */}
        <div className="bg-white rounded-2xl shadow-lg p-8 space-y-8">
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">1. مقدمة</h2>
            <p className="text-gray-600 leading-relaxed">
              مرحباً بك في منصة ديواني لمواد البناء. هذه الشروط والأحكام تحكم استخدامك
              لمنصتنا وخدماتنا. باستخدامك للمنصة، فإنك توافق على الالتزام بهذه الشروط.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">2. التسجيل والحسابات</h2>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>يجب أن تكون عمرك 18 سنة أو أكثر للتسجيل</li>
              <li>يجب تقديم معلومات صحيحة ودقيقة عند التسجيل</li>
              <li>أنت مسؤول عن الحفاظ على سرية حسابك وكلمة المرور</li>
              <li>يجب إخطارنا فوراً عند أي استخدام غير مصرح به لحسابك</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">3. استخدام المنصة</h2>
            <p className="text-gray-600 leading-relaxed mb-4">
              بصفتك مستخدماً للمنصة، توافق على عدم:
            </p>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>استخدام المنصة لأي غرض غير قانوني</li>
              <li>انتحال شخصية أي شخص أو كيان</li>
              <li>التدخل في أمان المنصة أو تعطيلها</li>
              <li>جمع معلومات المستخدمين الآخرين دون إذن</li>
              <li>نشر محتوى مسيء أو ضار أو مخالف للأنظمة</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">4. الطلبات والمدفوعات</h2>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>جميع الأسعار معروضة بالريال السعودي وتشمل ضريبة القيمة المضافة</li>
              <li>نحتفظ بحق رفض أي طلب لأي سبب</li>
              <li>يتم تأكيد الطلب بعد استلام الدفع</li>
              <li>سياسة الإرجاع والاستبدال تخضع لشروط محددة</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">5. التوصيل</h2>
            <p className="text-gray-600 leading-relaxed">
              نلتزم بتوصيل الطلبات في المواعيد المحددة. قد تتغير مواعيد التوصيل
              حسب الموقع وتوفر المنتجات. سيتم إخطارك بأي تأخيرات متوقعة.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">6. المسؤولية</h2>
            <p className="text-gray-600 leading-relaxed">
              المنصة تعمل كوسيط بين المشترين والبائعين. نحن غير مسؤولين عن
              جودة المنتجات المقدمة من البائعين الخارجيين، ولكننا نسعى لضمان
              معايير الجودة من خلال نظام التقييمات والمراجعات.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">7. الملكية الفكرية</h2>
            <p className="text-gray-600 leading-relaxed">
              جميع المحتويات والعلامات التجارية والشعارات الموجودة على المنصة
              هي ملك لديواني أو مرخصة لنا. لا يجوز استخدامها دون إذن كتابي مسبق.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">8. التعديلات</h2>
            <p className="text-gray-600 leading-relaxed">
              نحتفظ بالحق في تعديل هذه الشروط في أي وقت. سيتم إخطارك بأي
              تغييرات جوهرية. استمرار استخدامك للمنصة بعد التعديلات يعني موافقتك عليها.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-4">9. الاتصال بنا</h2>
            <p className="text-gray-600 leading-relaxed">
              إذا كان لديك أي استفسارات حول هذه الشروط، يرجى التواصل معنا عبر:
            </p>
            <ul className="list-disc list-inside text-gray-600 space-y-2 mt-4">
              <li>البريد الإلكتروني: support@diwani.sa</li>
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

export default TermsPage;
