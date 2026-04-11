// DEBT-FE-017: Footer is now an RSC — client islands (StatusFooterBadge, ManageCookiesButton)
// are in FooterClientIslands.tsx to minimize the 'use client' footprint.
import type { ReactNode } from 'react';
import { footer } from '@/lib/copy/valueProps';
import { StatusFooterBadge, ManageCookiesButton } from '@/app/components/FooterClientIslands';

/**
 * STORY-174 AC6: Footer - Refined Layout with Animations
 *
 * Features:
 * - Gradient border-top separator
 * - Link underline animations (width: 0 → 100%)
 * - Social icons with glow effect on hover
 * - 4-column grid layout
 * - Transparency disclaimer (STORY-173)
 */
export default function Footer() {
  return (
    <footer id="site-footer" className="relative bg-surface-1 text-ink">
      {/* Gradient border-top separator */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{
          background: 'linear-gradient(90deg, transparent 0%, var(--brand-blue) 50%, transparent 100%)',
        }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Main Footer Grid */}
        <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 mb-8">
          {/* Sobre */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-ink">Sobre</h3>
            <ul className="space-y-2 text-sm text-ink-secondary">
              <li>
                <FooterLink href="/sobre">Quem somos</FooterLink>
              </li>
              <li>
                <FooterLink href="/sobre#metodologia">Metodologia</FooterLink>
              </li>
              <li>
                <FooterLink href="/stack">Tech Stack</FooterLink>
              </li>
              <li>
                <FooterLink href="#como-funciona">Como funciona</FooterLink>
              </li>
            </ul>
          </div>

          {/* Ferramentas — SEO-PLAYBOOK Fundação §5 */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-ink">Ferramentas</h3>
            <ul className="space-y-2 text-sm text-ink-secondary">
              <li>
                <FooterLink href="/calculadora">Calculadora de Oportunidades</FooterLink>
              </li>
              <li>
                {/* STORY-431 AC1: link Observatório no footer */}
                <FooterLink href="/observatorio">Observatório de Licitações</FooterLink>
              </li>
              <li>
                <FooterLink href="/cnpj">Consulta CNPJ B2G</FooterLink>
              </li>
              <li>
                <FooterLink href="/glossario">Glossário de Licitações</FooterLink>
              </li>
              <li>
                <FooterLink href="/dados">Dados de Licitações</FooterLink>
              </li>
              <li>
                <FooterLink href="/estatisticas">Estatísticas Citáveis</FooterLink>
              </li>
              <li>
                <FooterLink href="/casos">Casos de sucesso</FooterLink>
              </li>
              <li>
                <FooterLink href="/comparador">Comparador de Editais</FooterLink>
              </li>
              <li>
                <FooterLink href="/demo">Demo Interativo</FooterLink>
              </li>
            </ul>
          </div>

          {/* Conteudo */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-ink">Conteúdo</h3>
            <ul className="space-y-2 text-sm text-ink-secondary">
              <li>
                <FooterLink href="/como-avaliar-licitacao">Avaliar licitações</FooterLink>
              </li>
              <li>
                <FooterLink href="/como-evitar-prejuizo-licitacao">Evitar prejuízo</FooterLink>
              </li>
              <li>
                <FooterLink href="/como-filtrar-editais">Filtrar editais</FooterLink>
              </li>
              <li>
                <FooterLink href="/como-priorizar-oportunidades">Priorizar oportunidades</FooterLink>
              </li>
              <li>
                <FooterLink href="/perguntas">Perguntas Frequentes</FooterLink>
              </li>
            </ul>
          </div>

          {/* STORY-261 AC11: Blog section */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-ink">Blog</h3>
            <ul className="space-y-2 text-sm text-ink-secondary">
              <li>
                <FooterLink href="/blog">Todos os artigos</FooterLink>
              </li>
              <li>
                <FooterLink href="/blog?category=Empresas+B2G">Empresas B2G</FooterLink>
              </li>
              <li>
                <FooterLink href="/blog?category=Consultorias+de+Licita%C3%A7%C3%A3o">Consultorias</FooterLink>
              </li>
            </ul>
          </div>

          {/* STORY-324 AC15: Sector landing page links */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-ink">Setores</h3>
            <ul className="space-y-2 text-sm text-ink-secondary">
              <li>
                <FooterLink href="/licitacoes">Todos os setores</FooterLink>
              </li>
              <li>
                <FooterLink href="/licitacoes/saude">Saúde</FooterLink>
              </li>
              <li>
                <FooterLink href="/licitacoes/informatica">TI e Hardware</FooterLink>
              </li>
              <li>
                <FooterLink href="/licitacoes/engenharia">Engenharia</FooterLink>
              </li>
              <li>
                <FooterLink href="/licitacoes/alimentos">Alimentação</FooterLink>
              </li>
            </ul>
          </div>

          {/* Planos */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-ink">Planos</h3>
            <ul className="space-y-2 text-sm text-ink-secondary">
              <li>
                <FooterLink href="/planos">Planos e Preços</FooterLink>
              </li>
              <li>
                <FooterLink href="/signup?source=footer">Teste Gratuito</FooterLink>
              </li>
            </ul>
          </div>

          {/* Suporte */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-ink">Suporte</h3>
            <ul className="space-y-2 text-sm text-ink-secondary">
              <li>
                <FooterLink href="/ajuda">Central de Ajuda</FooterLink>
              </li>
              <li>
                <FooterLink href="/ajuda#contato">Contato</FooterLink>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-ink">Legal</h3>
            <ul className="space-y-2 text-sm text-ink-secondary">
              <li>
                <FooterLink href="/privacidade">Política de Privacidade</FooterLink>
              </li>
              <li>
                <FooterLink href="/termos">Termos de Uso</FooterLink>
              </li>
              <li>
                <ManageCookiesButton />
              </li>
            </ul>
          </div>
        </div>

        {/* STORY-173: Transparency Disclaimer Section */}
        <div className="border-t border-[var(--border-strong)] pt-8 mb-8">
          <div className="bg-surface-2 rounded-lg p-6 border border-border">
            <div className="flex items-start gap-4">
              {/* Info Icon with Glow */}
              <div className="flex-shrink-0">
                <svg
              role="img"
              aria-label="Ícone"
                  className="w-6 h-6 text-brand-blue"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>

              {/* Transparency Content */}
              <div className="flex-1">
                <h4 className="font-semibold text-ink mb-2">
                  Transparência de Fontes de Dados
                </h4>
                <p className="text-sm text-ink-secondary mb-3">
                  {footer.dataSource}
                </p>
                <p className="text-sm text-ink-secondary mb-3">
                  {footer.disclaimer}
                </p>
                <div className="flex items-center gap-2 text-sm text-brand-blue">
                  <svg
              role="img"
              aria-label="Ícone"
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>{footer.trustBadge}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-[var(--border-strong)] pt-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {/* Copyright */}
            <p className="text-sm text-ink-secondary">
              © 2026 SmartLic.tech. Todos os direitos reservados.
            </p>
            <p className="text-xs text-ink-muted">
              CONFENGE Avaliações e Inteligência Artificial LTDA — CNPJ 56.688.745/0001-00 — Av. Pref. Osmar Cunha, 416 - Centro, Florianópolis - SC, 88015-100
            </p>

            {/* LGPD Badge */}
            <div className="flex items-center gap-2">
              <svg
              role="img"
              aria-label="Ícone"
                className="w-5 h-5 text-success"
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-sm text-ink-secondary">Em conformidade com a LGPD</span>
            </div>

            {/* STORY-316 AC16: Status badge with link to /status */}
            <StatusFooterBadge />

            {/* Developer Attribution */}
            <p className="text-sm text-ink-secondary">
              Uma Solução CONFENGE
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}


/**
 * Footer Link with Underline Animation
 */
function FooterLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      className="
        relative
        inline-block
        hover:text-brand-blue
        transition-colors
        focus-visible:outline-none
        focus-visible:ring-[3px]
        focus-visible:ring-[var(--ring)]
        focus-visible:ring-offset-2
        rounded
        px-1
        group
      "
    >
      {children}
      {/* Animated underline */}
      <span className="
        absolute
        bottom-0
        left-0
        w-0
        h-[2px]
        bg-brand-blue
        transition-all
        duration-300
        group-hover:w-full
      " />
    </a>
  );
}
