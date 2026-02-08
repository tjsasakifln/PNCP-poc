import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Termos de Serviço | SmartLic',
  description: 'Termos de Serviço do SmartLic - Condições de uso da plataforma',
};

export default function TermosPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-950">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 md:p-12">
          <h1 className="text-4xl font-bold mb-2 text-gray-900 dark:text-white">
            Termos de Serviço
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-8">
            Última atualização: 07 de fevereiro de 2026
          </p>

          <div className="prose prose-gray dark:prose-invert max-w-none">
            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                1. Aceitação dos Termos
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Ao acessar e utilizar a plataforma <strong>SmartLic</strong> ("Plataforma", "Serviço" ou "nós"),
                você ("Usuário", "você" ou "Cliente") concorda em cumprir e estar vinculado a estes Termos de Serviço.
                Se você não concordar com qualquer parte destes termos, não utilize nossos serviços.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                2. Descrição do Serviço
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                A SmartLic é uma plataforma SaaS que oferece:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Busca automatizada de oportunidades de licitações públicas no Portal Nacional de Contratações Públicas (PNCP)</li>
                <li>Filtragem por setor, estado, município, modalidade e faixa de valor</li>
                <li>Geração de relatórios em Excel com dados estruturados</li>
                <li>Resumos executivos gerados por inteligência artificial</li>
                <li>Notificações por e-mail sobre novas oportunidades relevantes</li>
                <li>Histórico de buscas e análises personalizadas</li>
              </ul>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-4">
                <strong>IMPORTANTE:</strong> A SmartLic é uma ferramenta de descoberta e análise de informações públicas.
                Não somos responsáveis pela exatidão, integridade ou atualização dos dados fornecidos pela PNCP.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                3. Cadastro e Conta
              </h2>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                3.1 Requisitos
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Você deve ter pelo menos 18 anos ou ser legalmente capaz de celebrar contratos</li>
                <li>Fornecer informações precisas, atualizadas e completas no cadastro</li>
                <li>Manter a segurança de sua senha e aceitar responsabilidade por atividades em sua conta</li>
                <li>Notificar-nos imediatamente sobre qualquer uso não autorizado de sua conta</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                3.2 Tipos de Conta
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li><strong>Free:</strong> Acesso limitado com até 5 buscas/mês</li>
                <li><strong>Professional:</strong> Buscas ilimitadas, notificações por e-mail, suporte prioritário</li>
                <li><strong>Enterprise:</strong> API access, white-label, SLA dedicado, suporte técnico 24/7</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                3.3 Suspensão e Encerramento
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Reservamo-nos o direito de suspender ou encerrar sua conta caso:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Violação destes Termos de Serviço</li>
                <li>Uso fraudulento ou abusivo da Plataforma</li>
                <li>Inadimplência no pagamento (planos pagos)</li>
                <li>Atividades que coloquem em risco a segurança da Plataforma</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                4. Uso Aceitável
              </h2>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                4.1 Você Concorda em NÃO:
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Usar a Plataforma para finalidades ilegais ou não autorizadas</li>
                <li>Tentar acessar áreas restritas do sistema ou dados de outros usuários</li>
                <li>Realizar engenharia reversa, descompilar ou desmontar qualquer parte do software</li>
                <li>Automatizar requisições à Plataforma sem autorização prévia (ex: scraping, bots)</li>
                <li>Sobrecarregar intencionalmente a infraestrutura (ataques DDoS)</li>
                <li>Compartilhar credenciais de acesso com terceiros não autorizados</li>
                <li>Revender, sublicenciar ou redistribuir os Serviços sem autorização expressa</li>
                <li>Coletar dados de outros usuários sem consentimento</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                4.2 Limites de Uso (Rate Limits)
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                A Plataforma possui limites de requisições por minuto/hora para garantir qualidade do serviço.
                Violações sistemáticas podem resultar em suspensão temporária ou permanente.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                5. Propriedade Intelectual
              </h2>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                5.1 Propriedade da SmartLic
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                A Plataforma, incluindo código-fonte, design, marca, conteúdo e funcionalidades, são de propriedade
                exclusiva da SmartLic e protegidos por leis de direitos autorais, marcas registradas e outras leis de propriedade intelectual.
              </p>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                5.2 Dados da PNCP
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Os dados de licitações públicas são de domínio público, fornecidos pelo Portal Nacional de Contratações Públicas (PNCP).
                A SmartLic agrega, filtra e enriquece esses dados, mas não reivindica propriedade sobre informações públicas.
              </p>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                5.3 Conteúdo do Usuário
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Você mantém propriedade de qualquer conteúdo que enviar à Plataforma (ex: filtros personalizados, notas).
                Ao enviar conteúdo, você nos concede uma licença não exclusiva, mundial e livre de royalties para
                operar, hospedar e melhorar os Serviços.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                6. Pagamentos e Renovação
              </h2>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                6.1 Planos Pagos
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Cobranças mensais ou anuais (de acordo com o plano escolhido)</li>
                <li>Renovação automática, salvo cancelamento prévio</li>
                <li>Preços sujeitos a alteração mediante aviso prévio de 30 dias</li>
                <li>Pagamentos processados via Stripe ou Mercado Pago</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                6.2 Cancelamento e Reembolso
              </h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Você pode cancelar sua assinatura a qualquer momento através das configurações de conta</li>
                <li>Cancelamentos terão efeito ao final do período de cobrança atual (não há reembolso proporcional)</li>
                <li><strong>Garantia de Reembolso:</strong> Planos pagos têm garantia de 7 dias (reembolso integral se solicitado dentro deste período)</li>
                <li>Após 7 dias, não oferecemos reembolsos, exceto em casos excepcionais a nosso critério</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                6.3 Inadimplência
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Em caso de falha no pagamento, sua conta será downgrade para o plano Free até regularização.
                Após 90 dias de inadimplência, podemos encerrar a conta permanentemente.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                7. Garantias e Limitações de Responsabilidade
              </h2>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                7.1 Isenção de Garantias
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                A Plataforma é fornecida "COMO ESTÁ" e "CONFORME DISPONÍVEL". <strong>NÃO GARANTIMOS:</strong>
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Disponibilidade ininterrupta ou livre de erros</li>
                <li>Exatidão, integridade ou atualização dos dados da PNCP</li>
                <li>Adequação para qualquer finalidade específica</li>
                <li>Que o uso da Plataforma resultará em sucesso nas licitações</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6 text-gray-800 dark:text-gray-200">
                7.2 Limitação de Responsabilidade
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                EM NENHUMA CIRCUNSTÂNCIA A SMARTLIC SERÁ RESPONSÁVEL POR DANOS INDIRETOS, INCIDENTAIS, ESPECIAIS,
                CONSEQUENCIAIS OU PUNITIVOS, INCLUINDO (MAS NÃO LIMITADO A):
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Perda de lucros ou oportunidades de negócio</li>
                <li>Perda de dados ou informações</li>
                <li>Interrupção de negócios</li>
                <li>Danos resultantes de erros ou omissões nos dados da PNCP</li>
              </ul>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-4">
                <strong>Nossa responsabilidade máxima é limitada ao valor pago por você nos últimos 12 meses.</strong>
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                8. Indenização
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Você concorda em indenizar, defender e isentar a SmartLic, seus diretores, funcionários e parceiros
                de quaisquer reclamações, perdas, danos, responsabilidades e despesas (incluindo honorários advocatícios)
                decorrentes de:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Seu uso da Plataforma</li>
                <li>Violação destes Termos de Serviço</li>
                <li>Violação de direitos de terceiros</li>
                <li>Qualquer conteúdo que você enviar à Plataforma</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                9. Privacidade e Proteção de Dados
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Seu uso da Plataforma também é regido por nossa{' '}
                <a href="/privacidade" className="text-blue-600 dark:text-blue-400 hover:underline">
                  Política de Privacidade
                </a>
                , que descreve como coletamos, usamos e protegemos seus dados pessoais em conformidade com a LGPD.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                10. Modificações dos Termos
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Reservamo-nos o direito de modificar estes Termos de Serviço a qualquer momento.
                Notificaremos sobre mudanças significativas por e-mail ou através de aviso na Plataforma com
                pelo menos 30 dias de antecedência. O uso continuado após as alterações constitui aceitação dos novos termos.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                11. Lei Aplicável e Foro
              </h2>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                Estes Termos de Serviço são regidos pelas leis da República Federativa do Brasil.
                Qualquer disputa será resolvida no foro da Comarca de São Paulo/SP, com exclusão de qualquer outro,
                por mais privilegiado que seja.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                12. Disposições Gerais
              </h2>
              <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                <li><strong>Acordo Integral:</strong> Estes Termos constituem o acordo completo entre você e a SmartLic</li>
                <li><strong>Independência das Cláusulas:</strong> Se qualquer disposição for considerada inválida, as demais permanecem em vigor</li>
                <li><strong>Não Renúncia:</strong> Nossa falha em fazer cumprir um direito não constitui renúncia dele</li>
                <li><strong>Cessão:</strong> Você não pode transferir seus direitos sem nosso consentimento prévio</li>
                <li><strong>Idioma:</strong> Versão em português prevalece sobre traduções</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
                13. Contato
              </h2>
              <div className="text-gray-700 dark:text-gray-300 leading-relaxed space-y-2">
                <p>Para questões sobre estes Termos de Serviço:</p>
                <p><strong>SmartLic</strong></p>
                <p>Entre em contato através da nossa plataforma, na seção de suporte.</p>
              </div>
            </section>

            <section className="mt-12 p-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                <strong>⚠️ IMPORTANTE:</strong> Ao utilizar a SmartLic, você reconhece ter lido, compreendido e
                concordado com estes Termos de Serviço e com nossa Política de Privacidade. Se você não concordar
                com qualquer parte, não utilize nossos serviços.
              </p>
            </section>
          </div>

          <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row gap-4 justify-between">
            <a
              href="/"
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:underline"
            >
              ← Voltar para a página inicial
            </a>
            <a
              href="/privacidade"
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:underline"
            >
              Ver Política de Privacidade →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
