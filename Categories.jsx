import { 
  Building2, 
  Hammer, 
  Brick, 
  Shield, 
  Door, 
  Palette, 
  Wrench, 
  Zap 
} from 'lucide-react'

const categories = [
  {
    id: 1,
    name: 'خرسانة وأسمنت',
    icon: Building2,
    count: '1,250 منتج',
    color: 'text-blue-600'
  },
  {
    id: 2,
    name: 'حديد وصلب',
    icon: Hammer,
    count: '890 منتج',
    color: 'text-gray-600'
  },
  {
    id: 3,
    name: 'طوب وبلوك',
    icon: Brick,
    count: '650 منتج',
    color: 'text-red-600'
  },
  {
    id: 4,
    name: 'عزل',
    icon: Shield,
    count: '420 منتج',
    color: 'text-green-600'
  },
  {
    id: 5,
    name: 'أبواب ونوافذ',
    icon: Door,
    count: '780 منتج',
    color: 'text-brown-600'
  },
  {
    id: 6,
    name: 'سيراميك وبلاط',
    icon: Palette,
    count: '950 منتج',
    color: 'text-purple-600'
  },
  {
    id: 7,
    name: 'سباكة',
    icon: Wrench,
    count: '560 منتج',
    color: 'text-blue-500'
  },
  {
    id: 8,
    name: 'كهرباء',
    icon: Zap,
    count: '340 منتج',
    color: 'text-yellow-600'
  }
]

const Categories = () => {
  return (
    <section className="py-16 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold text-blue-800 mb-4">
            فئات مواد البناء
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            اكتشف مجموعة واسعة من مواد البناء عالية الجودة من موردين معتمدين
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-6">
          {categories.map((category) => {
            const IconComponent = category.icon
            return (
              <div
                key={category.id}
                className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center hover:shadow-lg transition-all duration-300 cursor-pointer group"
              >
                <div className="mb-4">
                  <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center group-hover:bg-blue-800 group-hover:text-white transition-colors">
                    <IconComponent className={`w-8 h-8 ${category.color} group-hover:text-white`} />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-blue-800 mb-2">
                  {category.name}
                </h3>
                <p className="text-sm text-gray-500">
                  {category.count}
                </p>
              </div>
            )
          })}
        </div>

        <div className="text-center mt-12">
          <button className="border-2 border-blue-800 text-blue-800 px-6 py-3 rounded-lg font-medium hover:bg-blue-800 hover:text-white transition-colors">
            عرض جميع الفئات
          </button>
        </div>
      </div>
    </section>
  )
}

export default Categories

