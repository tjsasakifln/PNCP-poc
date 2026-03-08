/**
 * STORY-325 AC20: Testes unitários — PdfOptionsModal e botão PDF no SearchResults
 *
 * Cobre:
 * - Modal abre com elementos corretos
 * - onGenerate chamado com dados corretos
 * - onClose chamado pelo botão Cancelar
 * - Estado de loading desabilita botão
 * - Default de 20 itens
 * - Opções desabilitadas quando totalResults < opção
 * - Modal fechado não renderiza nada
 * - Tecla Escape fecha modal
 * - Botão PDF no SearchResults visível quando onGeneratePdf fornecido
 * - Botão PDF em estado de loading
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mock framer-motion to avoid animation issues in tests
// ---------------------------------------------------------------------------

jest.mock("framer-motion", () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

// ---------------------------------------------------------------------------
// Mocks for SearchResults dependencies
// ---------------------------------------------------------------------------

jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  );
});

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  })),
  usePathname: jest.fn(() => "/buscar"),
  useSearchParams: jest.fn(() => new URLSearchParams()),
}));

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("../../app/buscar/components/SearchStateManager", () => ({
  SearchStateManager: () => null,
}));
jest.mock("../../app/buscar/components/DataQualityBanner", () => ({
  DataQualityBanner: () => null,
}));
jest.mock("../../app/buscar/components/RefreshBanner", () => ({
  __esModule: true,
  default: () => null,
}));
jest.mock("../../app/buscar/components/LlmSourceBadge", () => ({
  LlmSourceBadge: () => null,
}));
jest.mock("../../app/buscar/components/ErrorDetail", () => ({
  ErrorDetail: () => null,
}));
jest.mock("../../app/buscar/components/ZeroResultsSuggestions", () => ({
  ZeroResultsSuggestions: () => null,
}));
jest.mock("../../app/buscar/components/FilterRelaxedBanner", () => ({
  FilterRelaxedBanner: () => null,
}));
jest.mock("../../app/buscar/components/ExpiredCacheBanner", () => ({
  ExpiredCacheBanner: () => null,
}));
jest.mock("../../app/buscar/components/SourcesUnavailable", () => ({
  SourcesUnavailable: () => null,
}));
jest.mock("../../app/buscar/components/PartialResultsPrompt", () => ({
  PartialResultsPrompt: () => null,
}));
jest.mock("../../app/buscar/components/SourceStatusGrid", () => ({
  __esModule: true,
  default: () => null,
}));
jest.mock("../../app/buscar/components/UfProgressGrid", () => ({
  UfProgressGrid: () => null,
}));
jest.mock("../../components/EnhancedLoadingProgress", () => ({
  EnhancedLoadingProgress: () => null,
}));
jest.mock("../../app/components/LoadingResultsSkeleton", () => ({
  LoadingResultsSkeleton: () => null,
}));
jest.mock("../../app/buscar/components/SearchEmptyState", () => ({
  SearchEmptyState: () => null,
}));
jest.mock("../../app/components/LicitacoesPreview", () => ({
  LicitacoesPreview: () => (
    <div data-testid="licitacoes-preview">Preview</div>
  ),
}));
jest.mock("../../app/components/OrdenacaoSelect", () => ({
  OrdenacaoSelect: () => null,
}));
jest.mock("../../app/components/QuotaCounter", () => ({
  QuotaCounter: () => null,
}));
jest.mock("../../components/GoogleSheetsExportButton", () => ({
  __esModule: true,
  default: () => null,
}));
jest.mock("../../components/billing/TrialUpsellCTA", () => ({
  TrialUpsellCTA: () => null,
}));
jest.mock("../../components/billing/TrialPaywall", () => ({
  TrialPaywall: () => null,
}));
jest.mock("../../app/buscar/types/searchPhase", () => ({
  deriveSearchPhase: () => "idle",
}));

// ---------------------------------------------------------------------------
// Component imports — after mocks
// ---------------------------------------------------------------------------

import PdfOptionsModal from "../../components/reports/PdfOptionsModal";
import SearchResults from "../../app/buscar/components/SearchResults";
import type { BuscaResult } from "../../app/types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const defaultModalProps = {
  isOpen: true,
  onClose: jest.fn(),
  onGenerate: jest.fn(),
  isGenerating: false,
  sectorName: "Informática",
  totalResults: 25,
};

function makeResult(overrides: Partial<BuscaResult> = {}): BuscaResult {
  return {
    resumo: {
      total_oportunidades: 5,
      valor_total: 0,
      texto: "Resumo de teste",
      resumo_executivo: "Resumo executivo de teste.",
    } as any,
    licitacoes: [{ id: "1" }] as any,
    download_id: null,
    download_url: null,
    total_raw: 10,
    total_filtrado: 5,
    filter_stats: null,
    termos_utilizados: null,
    stopwords_removidas: null,
    excel_available: false,
    upgrade_message: null,
    source_stats: null,
    response_state: "live",
    ...overrides,
  };
}

const BASE_PLAN_INFO = {
  plan_id: "smartlic_pro",
  plan_name: "SmartLic Pro",
  quota_used: 5,
  quota_reset_date: "2026-03-01",
  capabilities: {
    max_history_days: 1825,
    max_requests_per_month: 1000,
    allow_excel: true,
  },
};

const DEFAULT_SEARCH_RESULTS_PROPS = {
  loading: false,
  loadingStep: 1,
  estimatedTime: 30,
  stateCount: 5,
  statesProcessed: 5,
  onCancel: jest.fn(),
  sseEvent: null,
  useRealProgress: false,
  sseAvailable: false,
  onStageChange: jest.fn(),
  error: null,
  quotaError: null,
  rawCount: 10,
  ufsSelecionadas: new Set(["SP", "RJ"]),
  sectorName: "Informática",
  searchMode: "setor" as const,
  termosArray: [] as string[],
  ordenacao: "relevancia" as any,
  onOrdenacaoChange: jest.fn(),
  downloadLoading: false,
  downloadError: null,
  onDownload: jest.fn(),
  onSearch: jest.fn(),
  session: { access_token: "test-token" },
  onShowUpgradeModal: jest.fn(),
  onTrackEvent: jest.fn(),
  planInfo: BASE_PLAN_INFO,
};

// ===========================================================================
// PdfOptionsModal Tests
// ===========================================================================

describe("PdfOptionsModal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // -------------------------------------------------------------------------
  // Renderização básica
  // -------------------------------------------------------------------------

  describe("Renderização", () => {
    it("renderiza modal com título, input de nome do cliente e opções de itens", () => {
      render(<PdfOptionsModal {...defaultModalProps} />);

      expect(screen.getByText("Gerar Relatório PDF")).toBeInTheDocument();
      expect(screen.getByLabelText(/Nome da empresa/)).toBeInTheDocument();
      expect(
        screen.getByRole("radio", { name: "10 oportunidades" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("radio", { name: "20 oportunidades" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("radio", { name: "50 oportunidades" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Gerar PDF/ }),
      ).toBeInTheDocument();
    });

    it("não renderiza nada quando isOpen é false", () => {
      render(<PdfOptionsModal {...defaultModalProps} isOpen={false} />);

      expect(screen.queryByText("Gerar Relatório PDF")).not.toBeInTheDocument();
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("exibe o nome do setor na área de contexto", () => {
      render(
        <PdfOptionsModal {...defaultModalProps} sectorName="Construção Civil" />,
      );

      expect(screen.getByText("Construção Civil")).toBeInTheDocument();
    });

    it("exibe o total de resultados na área de contexto quando totalResults > 0", () => {
      render(<PdfOptionsModal {...defaultModalProps} totalResults={42} />);

      expect(screen.getByText(/42/)).toBeInTheDocument();
    });

    it("exibe o placeholder correto no campo de nome da empresa", () => {
      render(<PdfOptionsModal {...defaultModalProps} />);

      const input = screen.getByPlaceholderText("Ex: Empresa ABC Ltda");
      expect(input).toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // Valor padrão
  // -------------------------------------------------------------------------

  describe("Valor padrão", () => {
    it("opção 20 itens é selecionada por padrão quando totalResults >= 20", () => {
      render(<PdfOptionsModal {...defaultModalProps} totalResults={30} />);

      const radio20 = screen.getByRole("radio", {
        name: "20 oportunidades",
      }) as HTMLInputElement;
      expect(radio20.checked).toBe(true);
    });

    it("opção 10 itens é selecionada por padrão quando totalResults < 20", () => {
      render(<PdfOptionsModal {...defaultModalProps} totalResults={15} />);

      const radio10 = screen.getByRole("radio", {
        name: "10 oportunidades",
      }) as HTMLInputElement;
      expect(radio10.checked).toBe(true);
    });
  });

  // -------------------------------------------------------------------------
  // Opções desabilitadas
  // -------------------------------------------------------------------------

  describe("Opções desabilitadas", () => {
    it("desabilita opções cujo valor excede o total de resultados", () => {
      render(<PdfOptionsModal {...defaultModalProps} totalResults={15} />);

      const radio10 = screen.getByRole("radio", {
        name: "10 oportunidades",
      }) as HTMLInputElement;
      const radio20 = screen.getByRole("radio", {
        name: "20 oportunidades",
      }) as HTMLInputElement;
      const radio50 = screen.getByRole("radio", {
        name: "50 oportunidades",
      }) as HTMLInputElement;

      expect(radio10.disabled).toBe(false);
      expect(radio20.disabled).toBe(true);
      expect(radio50.disabled).toBe(true);
    });

    it("todas as opções habilitadas quando totalResults >= 50", () => {
      render(<PdfOptionsModal {...defaultModalProps} totalResults={50} />);

      const radio10 = screen.getByRole("radio", {
        name: "10 oportunidades",
      }) as HTMLInputElement;
      const radio20 = screen.getByRole("radio", {
        name: "20 oportunidades",
      }) as HTMLInputElement;
      const radio50 = screen.getByRole("radio", {
        name: "50 oportunidades",
      }) as HTMLInputElement;

      expect(radio10.disabled).toBe(false);
      expect(radio20.disabled).toBe(false);
      expect(radio50.disabled).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // Interações do usuário
  // -------------------------------------------------------------------------

  describe("Interações do usuário", () => {
    it("chama onGenerate com clientName e maxItems corretos ao clicar em Gerar PDF", () => {
      const onGenerate = jest.fn();
      render(
        <PdfOptionsModal
          {...defaultModalProps}
          onGenerate={onGenerate}
          totalResults={50}
        />,
      );

      const input = screen.getByLabelText(/Nome da empresa/);
      fireEvent.change(input, { target: { value: "Empresa ABC" } });

      const radio50 = screen.getByRole("radio", { name: "50 oportunidades" });
      fireEvent.click(radio50);

      const gerarBtn = screen.getByRole("button", { name: /Gerar PDF/ });
      fireEvent.click(gerarBtn);

      expect(onGenerate).toHaveBeenCalledTimes(1);
      expect(onGenerate).toHaveBeenCalledWith({
        clientName: "Empresa ABC",
        maxItems: 50,
      });
    });

    it("chama onGenerate com clientName vazio quando campo não preenchido", () => {
      const onGenerate = jest.fn();
      render(
        <PdfOptionsModal {...defaultModalProps} onGenerate={onGenerate} />,
      );

      const gerarBtn = screen.getByRole("button", { name: /Gerar PDF/ });
      fireEvent.click(gerarBtn);

      expect(onGenerate).toHaveBeenCalledWith({
        clientName: "",
        maxItems: 20,
      });
    });

    it("chama onClose ao clicar em Cancelar", () => {
      const onClose = jest.fn();
      render(<PdfOptionsModal {...defaultModalProps} onClose={onClose} />);

      const cancelarBtn = screen.getByRole("button", { name: "Cancelar" });
      fireEvent.click(cancelarBtn);

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("chama onClose ao clicar no botão X (fechar modal)", () => {
      const onClose = jest.fn();
      render(<PdfOptionsModal {...defaultModalProps} onClose={onClose} />);

      const closeBtn = screen.getByLabelText("Fechar modal");
      fireEvent.click(closeBtn);

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("chama onClose ao pressionar tecla Escape", () => {
      const onClose = jest.fn();
      render(<PdfOptionsModal {...defaultModalProps} onClose={onClose} />);

      fireEvent.keyDown(document, { key: "Escape" });

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("não chama onClose ao pressionar Escape quando isGenerating é true", () => {
      const onClose = jest.fn();
      render(
        <PdfOptionsModal
          {...defaultModalProps}
          onClose={onClose}
          isGenerating={true}
        />,
      );

      fireEvent.keyDown(document, { key: "Escape" });

      expect(onClose).not.toHaveBeenCalled();
    });

    it("chama onClose ao clicar no overlay fora do card", () => {
      const onClose = jest.fn();
      render(<PdfOptionsModal {...defaultModalProps} onClose={onClose} />);

      const overlay = screen.getByRole("dialog");
      fireEvent.click(overlay);

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("não chama onClose ao clicar dentro do card do modal", () => {
      const onClose = jest.fn();
      render(<PdfOptionsModal {...defaultModalProps} onClose={onClose} />);

      const title = screen.getByText("Gerar Relatório PDF");
      fireEvent.click(title);

      expect(onClose).not.toHaveBeenCalled();
    });

    it("trim no clientName antes de chamar onGenerate", () => {
      const onGenerate = jest.fn();
      render(
        <PdfOptionsModal {...defaultModalProps} onGenerate={onGenerate} />,
      );

      const input = screen.getByLabelText(/Nome da empresa/);
      fireEvent.change(input, { target: { value: "  Empresa XYZ  " } });

      const gerarBtn = screen.getByRole("button", { name: /Gerar PDF/ });
      fireEvent.click(gerarBtn);

      expect(onGenerate).toHaveBeenCalledWith({
        clientName: "Empresa XYZ",
        maxItems: 20,
      });
    });
  });

  // -------------------------------------------------------------------------
  // Estado de carregamento
  // -------------------------------------------------------------------------

  describe("Estado de carregamento (isGenerating)", () => {
    it("desabilita o botão Gerar PDF quando isGenerating é true", () => {
      render(
        <PdfOptionsModal {...defaultModalProps} isGenerating={true} />,
      );

      const gerarBtn = screen.getByRole("button", {
        name: /Gerando PDF, aguarde/,
      });
      expect(gerarBtn).toBeDisabled();
    });

    it("exibe spinner animado quando isGenerating é true", () => {
      const { container } = render(
        <PdfOptionsModal {...defaultModalProps} isGenerating={true} />,
      );

      const spinner = container.querySelector(".animate-spin");
      expect(spinner).toBeInTheDocument();
    });

    it("exibe texto 'Gerando...' no botão quando isGenerating é true", () => {
      render(
        <PdfOptionsModal {...defaultModalProps} isGenerating={true} />,
      );

      expect(screen.getByText("Gerando...")).toBeInTheDocument();
    });

    it("desabilita o botão Cancelar quando isGenerating é true", () => {
      render(
        <PdfOptionsModal {...defaultModalProps} isGenerating={true} />,
      );

      const cancelarBtn = screen.getByRole("button", { name: "Cancelar" });
      expect(cancelarBtn).toBeDisabled();
    });

    it("desabilita todas as opções de itens quando isGenerating é true", () => {
      render(
        <PdfOptionsModal
          {...defaultModalProps}
          isGenerating={true}
          totalResults={50}
        />,
      );

      const radio10 = screen.getByRole("radio", {
        name: "10 oportunidades",
      }) as HTMLInputElement;
      const radio20 = screen.getByRole("radio", {
        name: "20 oportunidades",
      }) as HTMLInputElement;
      const radio50 = screen.getByRole("radio", {
        name: "50 oportunidades",
      }) as HTMLInputElement;

      expect(radio10.disabled).toBe(true);
      expect(radio20.disabled).toBe(true);
      expect(radio50.disabled).toBe(true);
    });

    it("desabilita o input de nome da empresa quando isGenerating é true", () => {
      render(
        <PdfOptionsModal {...defaultModalProps} isGenerating={true} />,
      );

      const input = screen.getByLabelText(
        /Nome da empresa/,
      ) as HTMLInputElement;
      expect(input.disabled).toBe(true);
    });

    it("exibe texto 'Gerar PDF' quando isGenerating é false", () => {
      render(
        <PdfOptionsModal {...defaultModalProps} isGenerating={false} />,
      );

      expect(screen.getByText("Gerar PDF")).toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // Acessibilidade
  // -------------------------------------------------------------------------

  describe("Acessibilidade", () => {
    it("tem role='dialog' e aria-modal='true'", () => {
      render(<PdfOptionsModal {...defaultModalProps} />);

      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-modal", "true");
    });

    it("tem aria-labelledby apontando para o título", () => {
      render(<PdfOptionsModal {...defaultModalProps} />);

      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-labelledby", "pdf-modal-title");

      const title = document.getElementById("pdf-modal-title");
      expect(title).toBeInTheDocument();
      expect(title?.textContent).toBe("Gerar Relatório PDF");
    });

    it("input do nome da empresa tem id correto vinculado ao label", () => {
      render(<PdfOptionsModal {...defaultModalProps} />);

      const input = screen.getByLabelText(/Nome da empresa/);
      expect(input).toHaveAttribute("id", "pdf-client-name");
    });

    it("opções de itens têm aria-label descritivo", () => {
      render(<PdfOptionsModal {...defaultModalProps} />);

      expect(
        screen.getByRole("radio", { name: "10 oportunidades" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("radio", { name: "20 oportunidades" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("radio", { name: "50 oportunidades" }),
      ).toBeInTheDocument();
    });

    it("botão de fechar tem aria-label 'Fechar modal'", () => {
      render(<PdfOptionsModal {...defaultModalProps} />);

      expect(screen.getByLabelText("Fechar modal")).toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // Seleção de opções de itens
  // -------------------------------------------------------------------------

  describe("Seleção de número de oportunidades", () => {
    it("permite selecionar opção 10", () => {
      render(<PdfOptionsModal {...defaultModalProps} totalResults={50} />);

      const radio10 = screen.getByRole("radio", {
        name: "10 oportunidades",
      }) as HTMLInputElement;

      fireEvent.click(radio10);

      expect(radio10.checked).toBe(true);
    });

    it("permite selecionar opção 50 quando totalResults >= 50", () => {
      render(<PdfOptionsModal {...defaultModalProps} totalResults={50} />);

      const radio50 = screen.getByRole("radio", {
        name: "50 oportunidades",
      }) as HTMLInputElement;

      fireEvent.click(radio50);

      expect(radio50.checked).toBe(true);
    });

    it("chama onGenerate com maxItems=10 quando opção 10 está selecionada", () => {
      const onGenerate = jest.fn();
      render(
        <PdfOptionsModal
          {...defaultModalProps}
          onGenerate={onGenerate}
          totalResults={50}
        />,
      );

      const radio10 = screen.getByRole("radio", { name: "10 oportunidades" });
      fireEvent.click(radio10);

      const gerarBtn = screen.getByRole("button", { name: /Gerar PDF/ });
      fireEvent.click(gerarBtn);

      expect(onGenerate).toHaveBeenCalledWith(
        expect.objectContaining({ maxItems: 10 }),
      );
    });
  });

  // -------------------------------------------------------------------------
  // Estado de botão desabilitado por totalResults=0
  // -------------------------------------------------------------------------

  describe("Botão desabilitado por totalResults=0", () => {
    it("desabilita o botão Gerar PDF quando totalResults é 0", () => {
      render(<PdfOptionsModal {...defaultModalProps} totalResults={0} />);

      const gerarBtn = screen.getByRole("button", { name: /Gerar PDF/ });
      expect(gerarBtn).toBeDisabled();
    });
  });
});

// ===========================================================================
// SearchResults — Botão PDF (STORY-325)
// ===========================================================================

describe("SearchResults — Botão PDF", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renderiza botão PDF quando onGeneratePdf é fornecido e há resultado com sessão ativa", () => {
    const onGeneratePdf = jest.fn();
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult()}
        onGeneratePdf={onGeneratePdf}
      />,
    );

    const pdfBtn = screen.getByTestId("pdf-report-button");
    expect(pdfBtn).toBeInTheDocument();
  });

  it("não renderiza botão PDF quando onGeneratePdf não é fornecido", () => {
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult()}
      />,
    );

    expect(screen.queryByTestId("pdf-report-button")).not.toBeInTheDocument();
  });

  it("não renderiza botão PDF quando result é null", () => {
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={null}
        onGeneratePdf={jest.fn()}
      />,
    );

    expect(screen.queryByTestId("pdf-report-button")).not.toBeInTheDocument();
  });

  it("não renderiza botão PDF quando session é null (usuário não autenticado)", () => {
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult()}
        session={null}
        onGeneratePdf={jest.fn()}
      />,
    );

    expect(screen.queryByTestId("pdf-report-button")).not.toBeInTheDocument();
  });

  it("não renderiza botão PDF quando isTrialExpired é true", () => {
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult()}
        onGeneratePdf={jest.fn()}
        isTrialExpired={true}
      />,
    );

    expect(screen.queryByTestId("pdf-report-button")).not.toBeInTheDocument();
  });

  it("botão PDF exibe estado de carregamento quando pdfLoading é true", () => {
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult()}
        onGeneratePdf={jest.fn()}
        pdfLoading={true}
      />,
    );

    const pdfBtn = screen.getByTestId("pdf-report-button");
    expect(pdfBtn).toBeDisabled();
    expect(screen.getByText("Gerando PDF...")).toBeInTheDocument();
  });

  it("botão PDF não é desabilitado quando pdfLoading é false", () => {
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult()}
        onGeneratePdf={jest.fn()}
        pdfLoading={false}
      />,
    );

    const pdfBtn = screen.getByTestId("pdf-report-button");
    expect(pdfBtn).not.toBeDisabled();
  });

  it("exibe spinner animado no botão PDF quando pdfLoading é true", () => {
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult()}
        onGeneratePdf={jest.fn()}
        pdfLoading={true}
      />,
    );

    const spinner = document.querySelector('[aria-label="Gerando PDF"]');
    expect(spinner).toBeInTheDocument();
  });

  it("chama onGeneratePdf com clientName vazio e maxItems=20 ao clicar no botão", () => {
    const onGeneratePdf = jest.fn();
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult()}
        onGeneratePdf={onGeneratePdf}
        pdfLoading={false}
      />,
    );

    const pdfBtn = screen.getByTestId("pdf-report-button");
    fireEvent.click(pdfBtn);

    expect(onGeneratePdf).toHaveBeenCalledTimes(1);
    expect(onGeneratePdf).toHaveBeenCalledWith({
      clientName: "",
      maxItems: 20,
    });
  });

  it("exibe o total de oportunidades no texto do botão PDF", () => {
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult({
          resumo: {
            total_oportunidades: 7,
            valor_total: 0,
            texto: "Resumo de teste",
            resumo_executivo: "Resumo executivo de teste.",
          } as any,
        })}
        onGeneratePdf={jest.fn()}
        pdfLoading={false}
      />,
    );

    const pdfBtn = screen.getByTestId("pdf-report-button");
    expect(pdfBtn).toHaveTextContent("7 oportunidades");
  });

  it("usa singular 'oportunidade' quando total_oportunidades é 1", () => {
    render(
      <SearchResults
        {...DEFAULT_SEARCH_RESULTS_PROPS}
        result={makeResult({
          resumo: {
            total_oportunidades: 1,
            valor_total: 0,
            texto: "Resumo de teste",
            resumo_executivo: "Resumo executivo de teste.",
          } as any,
        })}
        onGeneratePdf={jest.fn()}
        pdfLoading={false}
      />,
    );

    const pdfBtn = screen.getByTestId("pdf-report-button");
    expect(pdfBtn).toHaveTextContent("1 oportunidade");
    expect(pdfBtn).not.toHaveTextContent("1 oportunidades");
  });
});
