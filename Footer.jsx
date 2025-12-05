import { Phone, Mail, MapPin, Facebook, Twitter, Instagram, Linkedin } from 'lucide-react'
import logo from '../assets/logo_1.png'

const Footer = () => {
  return (
    <footer className="bg-blue-800 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company Info */}
          <div>
            <img src={logo} alt="بناء ماركت" className="h-12 w-auto mb-4 brightness-0 invert" />
            <p className="text-blue-100 mb-4">
              منصة رائدة في مجال توريد مواد البناء، نربط بين الموردين والعملاء لتوفير أفضل المنتجات بأسعار تنافسية.
            </p>
            <div className="flex space-x-4 space-x-reverse">
              <a href="#" className="text-blue-200 hover:text-white transition-colors">
                <Facebook className="w-5 h-5" />
              </a>
              <a href="#" className="text-blue-200 hover:text-white transition-colors">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="text-blue-200 hover:text-white transition-colors">
                <Instagram className="w-5 h-5" />
              </a>
              <a href="#" className="text-blue-200 hover:text-white transition-colors">
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-lg font-semibold mb-4">روابط سريعة</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">الرئيسية</a></li>
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">المنتجات</a></li>
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">الموردين</a></li>
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">من نحن</a></li>
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">اتصل بنا</a></li>
            </ul>
          </div>

          {/* Categories */}
          <div>
            <h3 className="text-lg font-semibold mb-4">الفئات الرئيسية</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">خرسانة وأسمنت</a></li>
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">حديد وصلب</a></li>
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">طوب وبلوك</a></li>
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">عزل</a></li>
              <li><a href="#" className="text-blue-100 hover:text-white transition-colors">أبواب ونوافذ</a></li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="text-lg font-semibold mb-4">تواصل معنا</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Phone className="w-5 h-5 text-orange-500" />
                <span className="text-blue-100">+966 11 123 4567</span>
              </div>
              <div className="flex items-center gap-3">
                <Mail className="w-5 h-5 text-orange-500" />
                <span className="text-blue-100">info@binaamarket.sa</span>
              </div>
              <div className="flex items-center gap-3">
                <MapPin className="w-5 h-5 text-orange-500" />
                <span className="text-blue-100">الرياض، المملكة العربية السعودية</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-blue-700 mt-8 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-blue-100 text-sm">
              © 2024 بناء ماركت. جميع الحقوق محفوظة.
            </p>
            <div className="flex space-x-6 space-x-reverse mt-4 md:mt-0">
              <a href="#" className="text-blue-100 hover:text-white text-sm transition-colors">
                سياسة الخصوصية
              </a>
              <a href="#" className="text-blue-100 hover:text-white text-sm transition-colors">
                شروط الاستخدام
              </a>
              <a href="#" className="text-blue-100 hover:text-white text-sm transition-colors">
                الدعم الفني
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer

