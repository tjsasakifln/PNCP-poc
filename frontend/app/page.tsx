// Landing Page Institucional - STORY-168 + STORY-173 + STORY-273 + SAB-006 + DEBT-122
// Route: / (root)
// SAB-006: Condensed to 7 sections — Hero → Problema → Solução → Como Funciona → Stats → Testimonials → CTA
import LandingNavbar from './components/landing/LandingNavbar';
import HeroSection from './components/landing/HeroSection';
import OpportunityCost from './components/landing/OpportunityCost';
import BeforeAfter from './components/landing/BeforeAfter';
import HowItWorks from './components/landing/HowItWorks';
import StatsSection from './components/landing/StatsSection';
import TestimonialSection from '../components/TestimonialSection';
import FinalCTA from './components/landing/FinalCTA';
import Footer from './components/Footer';

export default function LandingPage() {
  return (
    <>
      <LandingNavbar />

      <main id="main-content">
        <HeroSection />
        <OpportunityCost />
        <BeforeAfter />
        <HowItWorks />
        <StatsSection />
        <TestimonialSection />

        <section id="suporte">
          <FinalCTA />
        </section>
      </main>

      <Footer />
    </>
  );
}
