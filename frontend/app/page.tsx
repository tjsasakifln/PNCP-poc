// Landing Page Institucional - STORY-168 + STORY-173 + STORY-273 + SAB-006
// Route: / (root)
// SAB-006: Condensed to 6 sections — Hero → Problema → Solução → Como Funciona → Stats → CTA
import LandingNavbar from './components/landing/LandingNavbar';
import HeroSection from './components/landing/HeroSection';
import OpportunityCost from './components/landing/OpportunityCost';
import BeforeAfter from './components/landing/BeforeAfter';
import HowItWorks from './components/landing/HowItWorks';
import StatsSection from './components/landing/StatsSection';
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

        <section id="suporte">
          <FinalCTA />
        </section>
      </main>

      <Footer />
    </>
  );
}
