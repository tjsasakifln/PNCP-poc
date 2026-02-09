// Landing Page Institucional - STORY-168 + STORY-173
// Route: / (root)
import LandingNavbar from './components/landing/LandingNavbar';
import HeroSection from './components/landing/HeroSection';
import OpportunityCost from './components/landing/OpportunityCost';
import PNCPStatsSection from './components/landing/PNCPStatsSection';
import DifferentialsGrid from './components/landing/DifferentialsGrid';
import HowItWorks from './components/landing/HowItWorks';
import StatsSection from './components/landing/StatsSection';
import DataSourcesSection from './components/landing/DataSourcesSection';
import SectorsGrid from './components/landing/SectorsGrid';
import FinalCTA from './components/landing/FinalCTA';
import ValuePropSection from './components/ValuePropSection';
import ComparisonTable from './components/ComparisonTable';
import TestimonialsCarousel from './components/landing/TestimonialsCarousel';
import Footer from './components/Footer';

export default function LandingPage() {
  return (
    <>
      <LandingNavbar />

      <main id="main-content">
        <HeroSection />
        <ValuePropSection />
        <OpportunityCost />
        <PNCPStatsSection />
        <ComparisonTable />
        <DifferentialsGrid />
        <HowItWorks />
        <StatsSection />
        <section id="sobre">
          <DataSourcesSection />
        </section>
        <SectorsGrid />
        <TestimonialsCarousel />
        <section id="suporte">
          <FinalCTA />
        </section>
      </main>

      <Footer />
    </>
  );
}
