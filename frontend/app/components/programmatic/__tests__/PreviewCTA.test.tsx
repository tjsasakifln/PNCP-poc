/**
 * Tests for PreviewCTA (#1009 COPY-PSEO-CTA-010).
 *
 * Covers:
 *  - CTA button renders below main CTA
 *  - Click reveals 3 visible bid cards
 *  - Premium (blurred) bid cards show with blurred state
 *  - Signup banner shows correct remaining count
 *  - Loading skeleton state
 *  - Error state with retry
 *  - Mobile responsive (grid columns)
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import PreviewCTA from "../PreviewCTA";

/* ------------------------------------------------------------------ */
/*  Test data                                                         */
/* ------------------------------------------------------------------ */

const MOCK_ITEMS = [
  {
    orgao: "Prefeitura de Joinville",
    objeto: "Pavimentação asfáltica da Rua XV de Novembro - trecho 1",
    valor_estimado: 450000,
    data_limite: "2026-06-15",
    data_publicacao: "2026-05-01",
    link_interno: "/licitacoes/pavimentacao-asfaltica?query=Prefeitura%20de%20Joinville",
  },
  {
    orgao: "Prefeitura de Florianópolis",
    objeto: "Recapeamento asfáltico da Av. Beira Mar Norte",
    valor_estimado: 1200000,
    data_limite: "2026-06-20",
    data_publicacao: "2026-05-02",
    link_interno: "/licitacoes/pavimentacao-asfaltica?query=Prefeitura%20de%20Florian%C3%B3polis",
  },
  {
    orgao: "DER SC",
    objeto: "Manutenção de pavimento asfáltico BR-101 trecho sul",
    valor_estimado: 2800000,
    data_limite: "2026-07-01",
    data_publicacao: "2026-05-03",
    link_interno: "/licitacoes/pavimentacao-asfaltica?query=DER%20SC",
  },
  {
    orgao: "Prefeitura de Blumenau",
    objeto: "Sinalização viária e recapeamento centro",
    valor_estimado: 380000,
    data_limite: "2026-06-25",
    data_publicacao: "2026-05-04",
    link_interno: "/licitacoes/pavimentacao-asfaltica?query=Prefeitura%20de%20Blumenau",
  },
  {
    orgao: "Prefeitura de São José",
    objeto: "Recapeamento asfáltico do bairro Kobrasol",
    valor_estimado: 520000,
    data_limite: "2026-06-30",
    data_publicacao: "2026-05-05",
    link_interno: "/licitacoes/pavimentacao-asfaltica?query=Prefeitura%20de%20S%C3%A3o%20Jos%C3%A9",
  },
  {
    orgao: "Prefeitura de Palhoça",
    objeto: "Pavimentação asfáltica da Rua do Comércio",
    valor_estimado: 290000,
    data_limite: "2026-07-05",
    data_publicacao: "2026-05-06",
    link_interno: "/licitacoes/pavimentacao-asfaltica?query=Prefeitura%20de%20Palho%C3%A7a",
  },
];

const MOCK_RESPONSE = {
  items: MOCK_ITEMS,
  total: 47,
};

const BASE_PROPS = {
  setor: "pavimentacao-asfaltica",
  uf: "SC",
  setorLabel: "Pavimentação asfáltica",
  ufLabel: "Santa Catarina",
  totalOpen: 47,
};

/* ------------------------------------------------------------------ */
/*  Setup                                                              */
/* ------------------------------------------------------------------ */

let mockFetch: jest.Mock;

beforeEach(() => {
  mockFetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => MOCK_RESPONSE,
  } as unknown as Response);
  global.fetch = mockFetch;
});

afterEach(() => {
  jest.clearAllMocks();
});

/* ------------------------------------------------------------------ */
/*  Tests                                                              */
/* ------------------------------------------------------------------ */

describe("PreviewCTA — CTA button (closed state)", () => {
  it("renderiza botão CTA abaixo da CTA principal", () => {
    render(<PreviewCTA {...BASE_PROPS} />);

    expect(
      screen.getByTestId("preview-cta-button")
    ).toBeInTheDocument();

    expect(
      screen.getByText(/Ver 3 editais grátis/)
    ).toBeInTheDocument();

    expect(
      screen.getByText(/Só quero ver os dados/)
    ).toBeInTheDocument();
  });

  it("não renderiza preview section antes do clique", () => {
    render(<PreviewCTA {...BASE_PROPS} />);

    expect(screen.queryByTestId("preview-section")).not.toBeInTheDocument();
  });
});

describe("PreviewCTA — click reveals preview", () => {
  it("abre preview e carrega dados ao clicar no CTA", async () => {
    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    // Deve mostrar loading primeiro
    expect(screen.getByTestId("preview-section")).toBeInTheDocument();

    // Aguarda os dados carregarem
    await waitFor(() => {
      expect(screen.getByText(/Últimos editais de/)).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/pseo/recent-editais"),
      expect.objectContaining({ signal: expect.anything() })
    );
  });

  it("mostra 3 cards visíveis com dados completos", async () => {
    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    await waitFor(() => {
      // Os 3 primeiros órgãos devem estar visíveis (não-blurred)
      expect(screen.getByText("Prefeitura de Joinville")).toBeInTheDocument();
      expect(screen.getByText("Prefeitura de Florianópolis")).toBeInTheDocument();
      expect(screen.getByText("DER SC")).toBeInTheDocument();
    });

    // Links "Ver detalhes" dos cards visíveis existem
    const visibleLinks = screen.getAllByText("Ver detalhes →");
    expect(visibleLinks).toHaveLength(3);
  });

  it("mostra 3 cards premium com blur", async () => {
    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    await waitFor(() => {
      // Os 3 últimos órgãos devem estar presentes no DOM (mesmo com blur)
      expect(screen.getByText("Prefeitura de Blumenau")).toBeInTheDocument();
      expect(screen.getByText("Prefeitura de São José")).toBeInTheDocument();
      expect(screen.getByText("Prefeitura de Palhoça")).toBeInTheDocument();
    });
  });

  it("mostra banner de cadastro com contagem correta de restantes", async () => {
    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    await waitFor(() => {
      expect(screen.getByTestId("preview-signup-banner")).toBeInTheDocument();
    });

    // totalOpen=47, VISIBLE_COUNT=3 => remaining=44
    expect(
      screen.getByText(/Peça à CONFENGE a leitura dos 44 editais restantes/)
    ).toBeInTheDocument();

    const consultoriaLink = screen.getByText("Pedir leitura à CONFENGE →");
    const href = consultoriaLink.getAttribute("href") || "";
    expect(href).toContain("/consultoria-b2g");
    expect(href).not.toContain("/signup");
    expect(href).toContain("ref=pseo-preview-pavimentacao-asfaltica-sc");
  });

  it("chama fetch com setor e uf corretos", async () => {
    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("setor=pavimentacao-asfaltica"),
        expect.objectContaining({ signal: expect.anything() })
      );
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("uf=SC"),
      expect.objectContaining({ signal: expect.anything() })
    );
  });
});

describe("PreviewCTA — loading state", () => {
  it("mostra skeleton durante carregamento", async () => {
    // Não resolve o fetch imediatamente
    mockFetch.mockReturnValueOnce(new Promise(() => {}));

    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    // Verifica que a seção de preview está visível
    expect(screen.getByTestId("preview-section")).toBeInTheDocument();

    // Verifica que skeletons estão sendo renderizados (via animate-pulse class)
    await waitFor(() => {
      const skeletons = document.querySelectorAll(".animate-pulse");
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });
});

describe("PreviewCTA — error state", () => {
  it("mostra mensagem de erro quando fetch falha", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    await waitFor(() => {
      expect(screen.getByTestId("preview-error")).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Não foi possível carregar os editais/)
    ).toBeInTheDocument();
  });

  it("botão de retry no erro tenta novamente", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    await waitFor(() => {
      expect(screen.getByTestId("preview-error")).toBeInTheDocument();
    });

    // Mock resolve agora
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_RESPONSE,
    } as unknown as Response);

    fireEvent.click(screen.getByText(/Tentar novamente/));

    await waitFor(() => {
      expect(screen.queryByTestId("preview-error")).not.toBeInTheDocument();
      expect(screen.getByText(/Últimos editais de/)).toBeInTheDocument();
    });
  });

  it("mostra CTA CONFENGE como fallback no estado de erro", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    await waitFor(() => {
      expect(screen.getByTestId("preview-error")).toBeInTheDocument();
    });

    const fallback = screen.getByText(/Pedir leitura à CONFENGE/);
    expect(fallback).toBeInTheDocument();
    expect(fallback.closest("a")).toHaveAttribute(
      "href",
      expect.stringContaining("/consultoria-b2g"),
    );
  });
});

describe("PreviewCTA — mobile responsive", () => {
  it("usa grid responsivo 1/2/3 colunas", async () => {
    render(<PreviewCTA {...BASE_PROPS} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    await waitFor(() => {
      expect(screen.getByText(/Últimos editais de/)).toBeInTheDocument();
    });

    // O grid container deve ter as classes responsivas
    const previewSection = screen.getByTestId("preview-section");
    const grids = previewSection.querySelectorAll(".grid");
    expect(grids.length).toBeGreaterThan(0);

    // Verifica se há pelo menos um elemento com classes de grid responsivo
    const hasResponsiveGrid = previewSection.innerHTML.includes(
      "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
    );
    expect(hasResponsiveGrid).toBe(true);
  });
});

describe("PreviewCTA — sem UF (apenas setor)", () => {
  const propsSemUf = {
    setor: "pavimentacao-asfaltica",
    setorLabel: "Pavimentação asfáltica",
    ufLabel: "",
    totalOpen: 10,
  };

  it("funciona sem UF", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        items: MOCK_ITEMS.slice(0, 4),
        total: 10,
      }),
    } as unknown as Response);

    render(<PreviewCTA {...propsSemUf} />);

    fireEvent.click(screen.getByTestId("preview-cta-button"));

    await waitFor(() => {
      expect(screen.getByText(/Últimos editais de/)).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.not.stringContaining("uf="),
      expect.objectContaining({ signal: expect.anything() })
    );

    // remaining: totalOpen=10 - VISIBLE_COUNT=3 = 7
    expect(
      screen.getByText(/Peça à CONFENGE a leitura dos 7 editais restantes/)
    ).toBeInTheDocument();
  });
});
