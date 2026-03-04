import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Politica de Privacidade | SmartLic',
  description: 'Politica de Privacidade do SmartLic - Como coletamos, usamos e protegemos seus dados',
};

export default function PrivacidadePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-950">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 md:p-12">
          <h1 className="text-4xl font-bold mb-2 text-gray-900 dark:text-white">
            Politica de Privacidade
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-8">
            Ultima atualizacao: 27 de fevereiro de 2026
          </p>

          <div className="prose prose-gray dark:prose-invert max-w-none">
            {/* 1. Introducao */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                1. Introducao
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                A <strong>CONFENGE Avaliacoes e Inteligencia Artificial LTDA</strong> (&quot;SmartLic&quot;, &quot;nos&quot; ou &quot;empresa&quot;),
                inscrita no CNPJ sob o n. XX.XXX.XXX/0001-XX, com sede na cidade de Sao Paulo/SP,
                respeita sua privacidade e esta comprometida em proteger seus dados pessoais em conformidade com
                a <strong>Lei Geral de Protecao de Dados (LGPD - Lei 13.709/2018)</strong>.
                Esta Politica de Privacidade descreve como coletamos, usamos, armazenamos e protegemos suas informacoes
                ao utilizar a plataforma SmartLic de descoberta automatizada de oportunidades de licitacoes publicas.
              </p>
            </section>

            {/* 2. Controlador de Dados */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                2. Controlador de Dados
              </h2>
              <div className="text-gray-700 dark:text-gray-300 leading-relaxed space-y-2">
                <p><strong>Razao Social:</strong> CONFENGE Avaliacoes e Inteligencia Artificial LTDA</p>
                <p><strong>Encarregado de Dados (DPO):</strong> Tiago Sasaki</p>
                <p><strong>E-mail do DPO:</strong>{' '}
                  <a href="mailto:privacidade@smartlic.tech" className="text-blue-600 dark:text-blue-400 hover:underline">privacidade@smartlic.tech</a>
                </p>
              </div>
            </section>

            {/* 3. Dados Coletados e Base Legal (Art. 7 LGPD) */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                3. Dados Coletados, Finalidade e Base Legal (Art. 7&#176; LGPD)
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                Cada tipo de dado pessoal que coletamos possui uma finalidade especifica e uma base legal conforme o Art. 7&#176; da LGPD:
              </p>

              <div className="overflow-x-auto">
                <table className="min-w-full text-sm border border-gray-200 dark:border-gray-700">
                  <thead>
                    <tr className="bg-gray-100 dark:bg-gray-700">
                      <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b">Dado Pessoal</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b">Finalidade</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b">Base Legal (Art. 7&#176;)</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b">Retencao</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-700 dark:text-gray-300">
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>Nome e e-mail</strong></td>
                      <td className="px-4 py-3">Criacao e manutencao de conta; comunicacao</td>
                      <td className="px-4 py-3">Execucao de contrato (Art. 7&#176;, V)</td>
                      <td className="px-4 py-3">Duracao da conta + 6 meses</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>CNPJ/CPF, cargo, empresa</strong></td>
                      <td className="px-4 py-3">Perfil empresarial para classificacao de licitacoes</td>
                      <td className="px-4 py-3">Execucao de contrato (Art. 7&#176;, V)</td>
                      <td className="px-4 py-3">Duracao da conta + 6 meses</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>Setores de interesse, UFs, filtros</strong></td>
                      <td className="px-4 py-3">Personalizacao de análise e classificação IA</td>
                      <td className="px-4 py-3">Execucao de contrato (Art. 7&#176;, V)</td>
                      <td className="px-4 py-3">Duracao da conta + 6 meses</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>Historico de análises</strong></td>
                      <td className="px-4 py-3">Funcionalidade de historico e analytics</td>
                      <td className="px-4 py-3">Execucao de contrato (Art. 7&#176;, V)</td>
                      <td className="px-4 py-3">12 meses (rolling)</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>Dados de pagamento</strong></td>
                      <td className="px-4 py-3">Processamento de cobrancas via Stripe</td>
                      <td className="px-4 py-3">Execucao de contrato (Art. 7&#176;, V)</td>
                      <td className="px-4 py-3">5 anos (obrigacao fiscal)</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>IP, navegador, SO</strong></td>
                      <td className="px-4 py-3">Seguranca, rate limiting, prevencao de fraude</td>
                      <td className="px-4 py-3">Interesse legitimo (Art. 7&#176;, IX)</td>
                      <td className="px-4 py-3">90 dias</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>Dados de uso (Mixpanel)</strong></td>
                      <td className="px-4 py-3">Melhoria de UX e analytics de produto</td>
                      <td className="px-4 py-3">Consentimento (Art. 7&#176;, I)</td>
                      <td className="px-4 py-3">12 meses</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>Cookies de sessao</strong></td>
                      <td className="px-4 py-3">Autenticacao e seguranca</td>
                      <td className="px-4 py-3">Execucao de contrato (Art. 7&#176;, V)</td>
                      <td className="px-4 py-3">Duracao da sessao</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>Google OAuth (nome, e-mail, foto)</strong></td>
                      <td className="px-4 py-3">Login social simplificado</td>
                      <td className="px-4 py-3">Consentimento (Art. 7&#176;, I)</td>
                      <td className="px-4 py-3">Duracao da conta + 6 meses</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3"><strong>Logs de erro (Sentry)</strong></td>
                      <td className="px-4 py-3">Monitoramento de estabilidade e debug</td>
                      <td className="px-4 py-3">Interesse legitimo (Art. 7&#176;, IX)</td>
                      <td className="px-4 py-3">90 dias</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <p className="text-gray-600 dark:text-gray-400 text-sm mt-4">
                <strong>Nota:</strong> Dados de pagamento (numero do cartao, CVV) sao processados exclusivamente pela Stripe e
                nunca armazenados em nossos servidores. A SmartLic recebe apenas informacoes de cobranca (status, valor, data).
              </p>
            </section>

            {/* 4. Compartilhamento de Dados */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                4. Compartilhamento de Dados
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                <strong>Nos NAO vendemos seus dados pessoais.</strong> Compartilhamos informacoes apenas nas seguintes situacoes:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li><strong>Supabase (EUA):</strong> Hospedagem de banco de dados e autenticacao</li>
                <li><strong>Railway (EUA):</strong> Hospedagem de backend e frontend</li>
                <li><strong>OpenAI (EUA):</strong> Classificacao IA de licitacoes (dados anonimizados)</li>
                <li><strong>Stripe (EUA):</strong> Processamento de pagamentos</li>
                <li><strong>Mixpanel (EUA):</strong> Analise de uso (apenas com consentimento explicito)</li>
                <li><strong>Sentry (EUA):</strong> Monitoramento de erros (dados sanitizados, sem PII)</li>
                <li><strong>Requisicoes Legais:</strong> Quando exigido por lei, ordem judicial ou autoridades competentes</li>
              </ul>
            </section>

            {/* 5. Transferencia Internacional */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                5. Transferencia Internacional de Dados
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Nossos prestadores de servico estao localizados nos Estados Unidos. As transferencias internacionais
                de dados pessoais sao realizadas com base no Art. 33 da LGPD, garantindo nivel adequado de protecao
                por meio de clausulas contratuais padrao e certificacoes de seguranca dos prestadores (SOC 2, ISO 27001).
              </p>
            </section>

            {/* 6. Seguranca dos Dados */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                6. Seguranca dos Dados
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                Implementamos medidas tecnicas e organizacionais para proteger seus dados:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Criptografia TLS 1.3 para todas as comunicacoes</li>
                <li>Autenticacao JWT com validacao local (ES256)</li>
                <li>Row Level Security (RLS) no banco de dados</li>
                <li>Sanitizacao de logs (PII nunca exposta em logs de producao)</li>
                <li>Content Security Policy (CSP) contra XSS</li>
                <li>Rate limiting por usuario e IP</li>
                <li>Monitoramento continuo de seguranca (Sentry, Prometheus)</li>
                <li>Backups regulares com recuperacao de desastres</li>
              </ul>
            </section>

            {/* 7. Direitos do Titular (Art. 18 LGPD) */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                7. Seus Direitos (Art. 18&#176; LGPD)
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                Conforme a Lei Geral de Protecao de Dados (LGPD - Lei 13.709/2018), voce tem os seguintes direitos:
              </p>
              <ul className="list-disc pl-6 space-y-3 text-gray-700 dark:text-gray-300">
                <li>
                  <strong>I - Confirmacao e Acesso:</strong> Confirmar se processamos seus dados e obter copia.
                  <span className="text-sm text-gray-500 dark:text-gray-400 block mt-1">
                    Disponivel em: Minha Conta &gt; Exportar Dados
                  </span>
                </li>
                <li>
                  <strong>II - Correcao:</strong> Atualizar dados incompletos, inexatos ou desatualizados.
                  <span className="text-sm text-gray-500 dark:text-gray-400 block mt-1">
                    Disponivel em: Minha Conta &gt; Editar Perfil
                  </span>
                </li>
                <li>
                  <strong>III - Anonimizacao/Bloqueio:</strong> Limitar processamento de dados desnecessarios ou excessivos.
                </li>
                <li>
                  <strong>IV - Portabilidade:</strong> Receber dados em formato estruturado (JSON).
                  <span className="text-sm text-gray-500 dark:text-gray-400 block mt-1">
                    Disponivel em: Minha Conta &gt; Exportar Dados (download JSON completo)
                  </span>
                </li>
                <li>
                  <strong>V - Eliminacao:</strong> Excluir todos os dados pessoais tratados com consentimento.
                  <span className="text-sm text-gray-500 dark:text-gray-400 block mt-1">
                    Disponivel em: Minha Conta &gt; Excluir Conta (exclusao completa e irrecuperavel)
                  </span>
                </li>
                <li>
                  <strong>VI - Informacao sobre compartilhamento:</strong> Saber com quais entidades seus dados sao compartilhados (veja secao 4).
                </li>
                <li>
                  <strong>VII - Revogacao de Consentimento:</strong> Retirar autorizacao a qualquer momento (cookies analiticos, notificacoes).
                </li>
                <li>
                  <strong>VIII - Oposicao:</strong> Se opor ao tratamento de dados em certas situacoes.
                </li>
              </ul>
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mt-4">
                <p className="text-gray-700 dark:text-gray-300">
                  <strong>Como exercer seus direitos:</strong>
                </p>
                <ul className="list-disc pl-6 space-y-1 mt-2 text-gray-700 dark:text-gray-300">
                  <li>
                    <strong>Self-service:</strong> Acesse{' '}
                    <a href="/conta" className="text-blue-600 dark:text-blue-400 hover:underline">Minha Conta</a> para
                    exportar dados, editar perfil ou excluir conta.
                  </li>
                  <li>
                    <strong>Via DPO:</strong> Envie e-mail para{' '}
                    <a href="mailto:privacidade@smartlic.tech" className="text-blue-600 dark:text-blue-400 hover:underline">privacidade@smartlic.tech</a>.
                    Resposta em ate 15 dias uteis.
                  </li>
                </ul>
              </div>
            </section>

            {/* 8. Cookies e Consentimento */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                8. Cookies e Tecnologias Similares
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                Utilizamos cookies para funcionamento da plataforma. Cookies analiticos so sao ativados apos
                seu consentimento explicito via banner de cookies.
              </p>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm border border-gray-200 dark:border-gray-700">
                  <thead>
                    <tr className="bg-gray-100 dark:bg-gray-700">
                      <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b">Tipo</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b">Finalidade</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b">Base Legal</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b">Duracao</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-700 dark:text-gray-300">
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>Essenciais</strong></td>
                      <td className="px-4 py-3">Autenticacao (Supabase session)</td>
                      <td className="px-4 py-3">Execucao de contrato</td>
                      <td className="px-4 py-3">Sessao</td>
                    </tr>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3"><strong>Funcionais</strong></td>
                      <td className="px-4 py-3">Preferencias de tema, idioma</td>
                      <td className="px-4 py-3">Interesse legitimo</td>
                      <td className="px-4 py-3">1 ano</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3"><strong>Analiticos</strong></td>
                      <td className="px-4 py-3">Mixpanel (uso da plataforma)</td>
                      <td className="px-4 py-3">Consentimento</td>
                      <td className="px-4 py-3">12 meses</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mt-4">
                Voce pode gerenciar suas preferencias de cookies a qualquer momento atraves do
                link &quot;Gerenciar Cookies&quot; no rodape da plataforma.
              </p>
            </section>

            {/* 9. Retencao de Dados */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                9. Retencao e Eliminacao de Dados
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                Mantemos seus dados apenas pelo tempo necessario para cumprir as finalidades descritas nesta politica.
                Os periodos de retencao por categoria estao descritos na tabela da secao 3. Alem disso:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Contas inativas por mais de 24 meses serao anonimizadas ou excluidas</li>
                <li>Dados fiscais sao retidos por 5 anos conforme legislacao tributaria</li>
                <li>Logs de seguranca sao retidos por 90 dias e depois deletados automaticamente</li>
                <li>Ao solicitar exclusao de conta, todos os dados sao deletados em ate 30 dias (exceto obrigacoes legais)</li>
              </ul>
            </section>

            {/* 10. Menores de Idade */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                10. Menores de Idade
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Nossos servicos sao destinados a profissionais e empresas. Nao coletamos intencionalmente dados
                de menores de 18 anos sem consentimento dos pais/responsaveis conforme Art. 14 da LGPD.
              </p>
            </section>

            {/* 11. Alteracoes */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                11. Alteracoes nesta Politica
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Podemos atualizar esta politica periodicamente. Notificaremos sobre mudancas significativas
                por e-mail ou atraves de aviso destacado na plataforma. A data de &quot;ultima atualizacao&quot; no topo
                reflete a versao mais recente.
              </p>
            </section>

            {/* 12. Contato e ANPD */}
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                12. Contato do Encarregado (DPO) e ANPD
              </h2>
              <div className="text-gray-700 dark:text-gray-300 leading-relaxed space-y-4">
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-2">
                  <p><strong>Encarregado de Dados (DPO):</strong> Tiago Sasaki</p>
                  <p><strong>E-mail:</strong>{' '}
                    <a href="mailto:privacidade@smartlic.tech" className="text-blue-600 dark:text-blue-400 hover:underline">privacidade@smartlic.tech</a>
                  </p>
                  <p><strong>Prazo de resposta:</strong> Ate 15 dias uteis</p>
                </div>
                <p>
                  Para questoes relacionadas a LGPD, voce tambem pode contatar a
                  Autoridade Nacional de Protecao de Dados (ANPD):{' '}
                  <a href="https://www.gov.br/anpd" target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">
                    www.gov.br/anpd
                  </a>
                </p>
              </div>
            </section>
          </div>

          <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
            <a
              href="/"
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:underline"
            >
              &larr; Voltar para a pagina inicial
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
