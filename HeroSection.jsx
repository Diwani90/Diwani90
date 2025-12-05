import { Search, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'

const HeroSection = () => {
  return (
    <section className="bg-gradient-to-br from-blue-800 to-blue-600 text-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <div className="text-center lg:text-right">
            <h1 className="text-4xl lg:text-6xl font-bold mb-6">
              منصة مواد البناء
            </h1>
            <p className="text-xl lg:text-2xl mb-8 text-blue-100">
              أكبر سوق لمواد البناء وكل ما تحتاجين
            </p>
            <p className="text-lg mb-8 text-blue-200">
              اكتشف أفضل الموردين والمنتجات بأسعار تنافسية مع ضمان الجودة والتسليم السريع
            </p>
            
            {/* Search Bar */}
            <div className="max-w-md mx-auto lg:mx-0 mb-8">
              <div className="relative">
                <input
                  type="text"
                  placeholder="ابحث عن المنتج الذي تحتاجه..."
                  className="w-full px-6 py-4 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-400"
                />
                <Button className="absolute left-2 top-2 bg-orange-500 text-white hover:bg-orange-600">
                  <Search className="w-5 h-5" />
                </Button>
              </div>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Button className="bg-orange-500 text-white hover:bg-orange-600 text-lg px-8 py-4">
                تسوق الآن
                <ArrowLeft className="mr-2 w-5 h-5" />
              </Button>
              <Button variant="outline" className="text-lg px-8 py-4 border-white text-white hover:bg-white hover:text-blue-900">
                انضم كمورد
              </Button>
            </div>
          </div>

          {/* Image/Illustration */}
          <div className="hidden lg:block">
            <div className="relative">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white/20 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold">500+</div>
                    <div className="text-sm">مورد معتمد</div>
                  </div>
                  <div className="bg-white/20 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold">10K+</div>
                    <div className="text-sm">منتج متاح</div>
                  </div>
                  <div className="bg-white/20 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold">24/7</div>
                    <div className="text-sm">دعم العملاء</div>
                  </div>
                  <div className="bg-white/20 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold">99%</div>
                    <div className="text-sm">رضا العملاء</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default HeroSection

