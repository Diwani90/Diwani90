import { Star, MapPin, Phone, Mail, Building2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

const suppliers = [
  {
    id: 1,
    name: 'شركة العمران للمواد',
    logo: '/api/placeholder/80/80',
    rating: 4.8,
    reviews: 156,
    location: 'الرياض',
    specialties: ['خرسانة', 'حديد', 'طوب'],
    description: 'متخصصون في توريد مواد البناء عالية الجودة منذ أكثر من 15 عام',
    verified: true
  },
  {
    id: 2,
    name: 'مؤسسة البناء الحديث',
    logo: '/api/placeholder/80/80',
    rating: 4.9,
    reviews: 203,
    location: 'جدة',
    specialties: ['عزل', 'سيراميك', 'دهانات'],
    description: 'رائدون في مجال مواد التشطيب والعزل بأحدث التقنيات',
    verified: true
  },
  {
    id: 3,
    name: 'شركة الخليج للحديد',
    logo: '/api/placeholder/80/80',
    rating: 4.7,
    reviews: 89,
    location: 'الدمام',
    specialties: ['حديد', 'صلب', 'معادن'],
    description: 'متخصصون في توريد الحديد والصلب بجميع الأنواع والمقاسات',
    verified: true
  },
  {
    id: 4,
    name: 'مصنع الأبواب الذهبية',
    logo: '/api/placeholder/80/80',
    rating: 4.6,
    reviews: 124,
    location: 'الرياض',
    specialties: ['أبواب', 'نوافذ', 'ألمنيوم'],
    description: 'صناعة وتوريد الأبواب والنوافذ بأعلى معايير الجودة',
    verified: false
  }
]

const FeaturedSuppliers = () => {
  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold text-blue-800 mb-4">
            الموردين المميزين
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            تعرف على أفضل الموردين المعتمدين والموثوقين في المملكة
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {suppliers.map((supplier) => (
            <div
              key={supplier.id}
              className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-xl transition-all duration-300 group"
            >
              {/* Header */}
              <div className="flex items-center mb-4">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center ml-4">
                  <Building2 className="w-8 h-8 text-blue-800" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-blue-800">
                      {supplier.name}
                    </h3>
                    {supplier.verified && (
                      <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs">✓</span>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-1 mt-1">
                    <Star className="w-4 h-4 text-yellow-400 fill-current" />
                    <span className="text-sm font-medium">{supplier.rating}</span>
                    <span className="text-sm text-gray-500">({supplier.reviews})</span>
                  </div>
                </div>
              </div>

              {/* Location */}
              <div className="flex items-center gap-2 mb-3">
                <MapPin className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-600">{supplier.location}</span>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                {supplier.description}
              </p>

              {/* Specialties */}
              <div className="mb-4">
                <div className="flex flex-wrap gap-1">
                  {supplier.specialties.map((specialty, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-blue-50 text-blue-800 text-xs rounded-full"
                    >
                      {specialty}
                    </span>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button size="sm" className="flex-1 bg-blue-800 text-white hover:bg-blue-700">
                  عرض المنتجات
                </Button>
                <Button size="sm" variant="outline" className="px-3">
                  <Phone className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <Button className="border-2 border-blue-800 text-blue-800 px-6 py-3 rounded-lg font-medium hover:bg-blue-800 hover:text-white transition-colors">
            عرض جميع الموردين
          </Button>
        </div>
      </div>
    </section>
  )
}

export default FeaturedSuppliers

