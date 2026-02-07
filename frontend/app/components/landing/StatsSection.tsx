interface StatsSectionProps {
  className?: string;
}

interface StatCard {
  value: string;
  label: string;
  highlight?: boolean;
}

const stats: StatCard[] = [
  {
    value: '6M+',
    label: 'licitações/ano publicadas no Brasil',
  },
  {
    value: '500k',
    label: 'oportunidades mensais processadas automaticamente',
  },
  {
    value: '12 setores',
    label: 'atendidos + em expansão constante',
  },
  {
    value: 'Criado por servidores públicos',
    label: 'Expertise insider: conhecemos a máquina por dentro',
    highlight: true,
  },
];

export default function StatsSection({ className = '' }: StatsSectionProps) {
  return (
    <section
      className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 bg-blue-50 dark:bg-blue-900/10 ${className}`}
    >
      <h2 className="text-3xl sm:text-4xl font-bold text-center text-gray-900 dark:text-white mb-12">
        Números que falam por si
      </h2>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
        {stats.map((stat, index) => (
          <div
            key={index}
            className={`text-center p-6 rounded-lg ${
              stat.highlight
                ? 'bg-blue-600 dark:bg-blue-700'
                : 'bg-white dark:bg-gray-800'
            }`}
          >
            <div
              className={`text-4xl sm:text-5xl font-bold mb-3 ${
                stat.highlight
                  ? 'text-white'
                  : 'text-blue-600 dark:text-blue-400'
              }`}
            >
              {stat.value}
            </div>
            <div
              className={`text-sm sm:text-base ${
                stat.highlight
                  ? 'text-blue-50'
                  : 'text-gray-600 dark:text-gray-300'
              }`}
            >
              {stat.label}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
