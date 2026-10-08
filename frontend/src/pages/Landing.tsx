import Features from '@/components/landing/Features'
import Hero from '@/components/landing/Hero'
import HowItWorks from '@/components/landing/HowItWorks'
import Navbar from '@/components/landing/Navbar'
import { CtaBand, Footer } from '@/components/landing/CtaBandFooter'

export default function Landing() {
  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Navbar />
      <main>
        <Hero />
        <HowItWorks />
        <Features />
        <CtaBand />
      </main>
      <Footer />
    </div>
  )
}
