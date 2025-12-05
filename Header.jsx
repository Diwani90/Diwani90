import { Search, ShoppingCart, User, Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import logo from '../assets/logo_1.png'

const Header = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <img src={logo} alt="بناء ماركت" className="h-10 w-auto" />
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8 space-x-reverse">
            <a href="#" className="text-blue-800 hover:text-blue-600 font-medium transition-colors">الرئيسية</a>
            <a href="#" className="text-gray-700 hover:text-blue-800 font-medium transition-colors">الموردين</a>
            <a href="#" className="text-gray-700 hover:text-blue-800 font-medium transition-colors">المنتجات</a>
            <a href="#" className="text-gray-700 hover:text-blue-800 font-medium transition-colors">من نحن</a>
            <a href="#" className="text-gray-700 hover:text-blue-800 font-medium transition-colors">اتصل بنا</a>
          </nav>

          {/* Search Bar */}
          <div className="flex-1 max-w-lg mx-8 hidden lg:block">
            <div className="relative">
              <input
                type="text"
                placeholder="ابحث عن مواد البناء..."
                className="w-full px-4 py-3 pr-10 rounded-lg border border-gray-200 focus:border-blue-800 focus:ring-2 focus:ring-blue-800/20 outline-none"
              />
              <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            </div>
          </div>

          {/* User Actions */}
          <div className="flex items-center space-x-4 space-x-reverse">
            <Button variant="ghost" size="sm" className="relative">
              <ShoppingCart className="w-5 h-5" />
              <span className="absolute -top-2 -right-2 bg-orange-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                3
              </span>
            </Button>
            <Button variant="ghost" size="sm">
              <User className="w-5 h-5" />
            </Button>
            <Button variant="outline" size="sm">
              تسجيل الدخول
            </Button>
            <Button size="sm" className="bg-blue-800 text-white hover:bg-blue-700">
              إنشاء حساب
            </Button>
            <Button variant="ghost" size="sm" className="md:hidden">
              <Menu className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header

