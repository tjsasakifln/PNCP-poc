/**
 * DEBT-011: Shared constants for conta sub-routes.
 */

export const ATESTADOS_CATALOG: Array<{ id: string; label: string }> = [
  { id: "crea", label: "CREA (Engenharia)" },
  { id: "crf", label: "CRF (Farmácia)" },
  { id: "inmetro", label: "INMETRO" },
  { id: "iso_9001", label: "ISO 9001 (Qualidade)" },
  { id: "iso_14001", label: "ISO 14001 (Ambiental)" },
  { id: "pgr_pcmso", label: "PGR/PCMSO (Segurança do Trabalho)" },
  { id: "alvara_sanitario", label: "Alvará Sanitário" },
  { id: "registro_anvisa", label: "Registro ANVISA" },
  { id: "habilitacao_antt", label: "Habilitação ANTT" },
  { id: "registro_cfq", label: "Registro CRQ (Química)" },
  { id: "licenca_ambiental", label: "Licença Ambiental" },
  { id: "crt", label: "CRT (Técnico)" },
];

export const PORTE_OPTIONS = [
  { value: "mei", label: "MEI — Microempreendedor Individual" },
  { value: "me", label: "ME — Microempresa" },
  { value: "epp", label: "EPP — Empresa de Pequeno Porte" },
  { value: "medio", label: "Medio Porte" },
  { value: "grande", label: "Grande Empresa" },
];

export const EXPERIENCIA_OPTIONS = [
  { value: "iniciante", label: "Iniciante — nunca participei" },
  { value: "basico", label: "Basico — ja participei de algumas" },
  { value: "intermediario", label: "Intermediario — participo regularmente" },
  { value: "avancado", label: "Avancado — processo sistematizado" },
];

export const ALL_UFS = [
  "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
  "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
  "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
];
