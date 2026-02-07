import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Política de Privacidade | SmartLic',
  description: 'Política de Privacidade do SmartLic - Como coletamos, usamos e protegemos seus dados',
};

export default function PrivacidadePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-950">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 md:p-12">
          <h1 className="text-4xl font-bold mb-2 text-gray-900 dark:text-white">
            Política de Privacidade
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-8">
            Última atualização: 07 de fevereiro de 2026
          </p>

          <div className="prose prose-gray dark:prose-invert max-w-none">
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                1. Introdução
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                A <strong>SmartLic</strong> ("nós", "nosso" ou "empresa") respeita sua privacidade e está
                comprometida em proteger seus dados pessoais. Esta Política de Privacidade descreve como
                coletamos, usamos, armazenamos e protegemos suas informações ao utilizar nossa plataforma
                de descoberta automatizada de oportunidades de licitações públicas.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                2. Informações que Coletamos
              </h2>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                2.1 Informações Fornecidas por Você
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li><strong>Cadastro:</strong> Nome, e-mail, telefone, CPF/CNPJ, cargo e empresa</li>
                <li><strong>Perfil de Busca:</strong> Setores de interesse, estados/regiões, filtros de valor</li>
                <li><strong>Comunicação:</strong> Mensagens enviadas através de formulários de contato</li>
                <li><strong>Pagamento:</strong> Dados de cobrança (processados por Stripe/Mercado Pago)</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                2.2 Informações Coletadas Automaticamente
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li><strong>Dados de Uso:</strong> Páginas visitadas, tempo de sessão, buscas realizadas</li>
                <li><strong>Dados Técnicos:</strong> Endereço IP, tipo de navegador, sistema operacional</li>
                <li><strong>Cookies:</strong> Preferências de tema, sessão de autenticação, análise de uso</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                2.3 Informações de Terceiros
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li><strong>Google OAuth:</strong> Nome, e-mail e foto de perfil (se autorizado)</li>
                <li><strong>PNCP API:</strong> Dados públicos de licitações (não inclui dados pessoais)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                3. Como Usamos Suas Informações
              </h2>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Fornecer e melhorar nossos serviços de busca de licitações</li>
                <li>Personalizar resultados de acordo com suas preferências</li>
                <li>Enviar notificações sobre novas oportunidades relevantes</li>
                <li>Processar pagamentos e gerenciar assinaturas</li>
                <li>Comunicar atualizações de sistema e novidades do produto</li>
                <li>Analisar uso da plataforma para melhorias de UX</li>
                <li>Prevenir fraudes e garantir segurança da plataforma</li>
                <li>Cumprir obrigações legais e regulatórias</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                4. Compartilhamento de Dados
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                <strong>Nós NÃO vendemos seus dados pessoais.</strong> Compartilhamos informações apenas nas seguintes situações:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li><strong>Prestadores de Serviço:</strong> Supabase (hospedagem), Railway (backend), OpenAI (IA), Stripe/Mercado Pago (pagamentos)</li>
                <li><strong>Requisições Legais:</strong> Quando exigido por lei, ordem judicial ou autoridades competentes</li>
                <li><strong>Proteção de Direitos:</strong> Para proteger nossos direitos, propriedade ou segurança</li>
                <li><strong>Consentimento:</strong> Quando você autorizar explicitamente</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                5. Segurança dos Dados
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                Implementamos medidas técnicas e organizacionais para proteger seus dados:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Criptografia SSL/TLS para todas as comunicações</li>
                <li>Autenticação de dois fatores (quando disponível)</li>
                <li>Controle de acesso baseado em funções (RBAC)</li>
                <li>Backups regulares e recuperação de desastres</li>
                <li>Monitoramento contínuo de segurança</li>
                <li>Auditoria de logs de acesso</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                6. Seus Direitos (LGPD)
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                Conforme a Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018), você tem direito a:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li><strong>Acesso:</strong> Confirmar se processamos seus dados e obter cópia</li>
                <li><strong>Correção:</strong> Atualizar dados incompletos, inexatos ou desatualizados</li>
                <li><strong>Anonimização/Bloqueio:</strong> Limitar processamento de dados desnecessários</li>
                <li><strong>Eliminação:</strong> Excluir dados tratados com consentimento (com exceções legais)</li>
                <li><strong>Portabilidade:</strong> Receber dados em formato estruturado e interoperável</li>
                <li><strong>Revogação de Consentimento:</strong> Retirar autorização a qualquer momento</li>
                <li><strong>Oposição:</strong> Se opor ao tratamento de dados em certas situações</li>
              </ul>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-4">
                Para exercer seus direitos, envie um e-mail para <a href="mailto:privacidade@smartlic.tech" className="text-blue-600 dark:text-blue-400 hover:underline">privacidade@smartlic.tech</a>
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                7. Cookies e Tecnologias Similares
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                Utilizamos cookies essenciais, funcionais e analíticos. Você pode gerenciar preferências de cookies através do seu navegador.
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li><strong>Essenciais:</strong> Autenticação, segurança</li>
                <li><strong>Funcionais:</strong> Preferências de tema, idioma</li>
                <li><strong>Analíticos:</strong> Google Analytics (anonimizado)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                8. Retenção de Dados
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Mantemos seus dados apenas pelo tempo necessário para cumprir as finalidades descritas nesta política,
                ou conforme exigido por lei. Dados de contas inativas por mais de 24 meses serão anonimizados ou excluídos.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                9. Transferência Internacional de Dados
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Alguns de nossos prestadores de serviço estão localizados fora do Brasil (EUA, Europa).
                Garantimos que essas transferências seguem padrões adequados de proteção de dados (GDPR, Privacy Shield, etc.).
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                10. Menores de Idade
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Nossos serviços são destinados a profissionais e empresas. Não coletamos intencionalmente dados
                de menores de 18 anos sem consentimento dos pais/responsáveis.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                11. Alterações nesta Política
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Podemos atualizar esta política periodicamente. Notificaremos sobre mudanças significativas
                por e-mail ou através de aviso destacado na plataforma.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                12. Contato
              </h2>
              <div className="text-gray-700 dark:text-gray-300 leading-relaxed space-y-2">
                <p><strong>Encarregado de Dados (DPO):</strong></p>
                <p>E-mail: <a href="mailto:privacidade@smartlic.tech" className="text-blue-600 dark:text-blue-400 hover:underline">privacidade@smartlic.tech</a></p>
                <p>E-mail alternativo: <a href="mailto:tiago.sasaki@gmail.com" className="text-blue-600 dark:text-blue-400 hover:underline">tiago.sasaki@gmail.com</a></p>
                <p className="mt-4">
                  Para questões relacionadas à LGPD, você também pode contatar a Autoridade Nacional de Proteção de Dados (ANPD):
                  <a href="https://www.gov.br/anpd" target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline ml-1">
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
              ← Voltar para a página inicial
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
