import Header from './components/Header'
import HeroSection from './components/HeroSection'
import Categories from './components/Categories'
import FeaturedSuppliers from './components/FeaturedSuppliers'
import Footer from './components/Footer'
import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main>
        <HeroSection />
        <Categories />
        <FeaturedSuppliers />
      </main>
      <Footer />
    </div>
  )
}

export default App

