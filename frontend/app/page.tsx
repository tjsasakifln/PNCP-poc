// Landing Page Institucional
// Route: / (root)
// Tema claro padrão (light theme) — brand-navy (#0a1e3f) distinto de brand-blue (#116dff)
import LandingNavbar from './components/landing/LandingNavbar';
import HeroB2GIntel from './components/landing/HeroB2GIntel';
import AntecipeDecidaExecute from './components/landing/AntecipeDecidaExecute';
import TerminalComparison from './components/landing/TerminalComparison';
import SocialProofMetrics from './components/landing/SocialProofMetrics';
import PersonasSection from './components/landing/PersonasSection';
import PublicIntelligenceSection from './components/landing/PublicIntelligenceSection';
import MarketSocialProof from './components/landing/MarketSocialProof';
import Footer from './components/Footer';
import NewsletterFooter from './components/landing/NewsletterFooter';
import { HomeFaqStructuredData } from './components/HomeFaqStructuredData';
import { ExitIntentPopup } from './components/ExitIntentPopup';

export default function LandingPage() {
  return (
    <>
      <HomeFaqStructuredData />
      <LandingNavbar />

      <main id="main-content">
        <HeroB2GIntel />
        <AntecipeDecidaExecute />
        <TerminalComparison />
        <SocialProofMetrics />
        <PersonasSection />
        <PublicIntelligenceSection />
        <MarketSocialProof />
      </main>

      <NewsletterFooter />
      <Footer />
      <ExitIntentPopup />
    </>
  );
}
