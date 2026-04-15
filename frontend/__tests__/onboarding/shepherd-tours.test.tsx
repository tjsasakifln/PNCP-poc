/**
 * STORY-4.2: Tour Component & OnboardingTourButton Tests
 *
 * Migrado de shepherd-tours (useShepherdTour) → Tour component WCAG 2.1 AA.
 *
 * Cobre:
 * AC1: renders steps with ARIA attributes
 * AC2: não inicia se localStorage marcado como completado
 * AC3: navegação Próximo / Voltar / Pular
 * AC4: localStorage persistence por tourId
 * AC5: callbacks onComplete e onSkip
 * AC6: onStepChange callback
 * AC7: ESC fecha o tour
 * AC8: showOn pula steps condicionalmente
 * AC9: beforeShow chamado antes de exibir step
 */

import "@testing-library/jest-dom";
import React from "react";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react";

// Mock focus-trap-react para evitar erros de jsdom (sem layout real)
jest.mock("focus-trap-react", () => {
  return function FocusTrap({ children }: { children: React.ReactNode }) {
    return <>{children}</>;
  };
});

import { Tour, type TourStepDef } from "../../components/tour/Tour";
import { OnboardingTourButton } from "../../components/OnboardingTourButton";

// ============================================================================
// Mocks compartilhados
// ============================================================================

const mockPush = jest.fn();
let currentPathname = "/buscar";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => currentPathname,
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

global.fetch = jest.fn(() =>
  Promise.resolve(new Response(null, { status: 204 }))
) as jest.Mock;

// ============================================================================
// Helpers
// ============================================================================

const SAMPLE_STEPS: TourStepDef[] = [
  { id: "step-1", title: "Passo Um", text: "Primeiro passo" },
  { id: "step-2", title: "Passo Dois", text: "Segundo passo" },
  { id: "step-3", title: "Passo Três", text: "Terceiro passo" },
];

function renderTour(props: Partial<React.ComponentProps<typeof Tour>> = {}) {
  return render(
    <Tour
      tourId="test"
      steps={SAMPLE_STEPS}
      active={true}
      {...props}
    />
  );
}

beforeEach(() => {
  localStorage.clear();
  mockPush.mockClear();
  currentPathname = "/buscar";
});

// ============================================================================
// AC1: ARIA + render
// ============================================================================

describe("Tour component — ARIA e render (AC1)", () => {
  it("renderiza null quando active=false", () => {
    const { container } = render(
      <Tour tourId="t" steps={SAMPLE_STEPS} active={false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renderiza null quando steps=[]", () => {
    const { container } = render(
      <Tour tourId="t" steps={[]} active={true} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renderiza dialog com role='dialog' quando active=true", () => {
    renderTour();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("aria-modal é 'false' — tour não bloqueia a árvore a11y", () => {
    renderTour();
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "false");
  });

  it("aria-labelledby aponta para o título do step", () => {
    renderTour();
    const dialog = screen.getByRole("dialog");
    const labelledBy = dialog.getAttribute("aria-labelledby");
    expect(labelledBy).toBeTruthy();
    const titleEl = document.getElementById(labelledBy!);
    expect(titleEl).toBeInTheDocument();
    expect(titleEl!.textContent).toBe("Passo Um");
  });

  it("aria-live='polite' para screen readers", () => {
    renderTour();
    const liveRegion = document.querySelector("[aria-live='polite']");
    expect(liveRegion).toBeInTheDocument();
    expect(liveRegion!.textContent).toContain("Passo Um");
  });

  it("exibe título e texto do step atual", () => {
    renderTour();
    expect(screen.getByText("Passo Um")).toBeInTheDocument();
    expect(screen.getByText("Primeiro passo")).toBeInTheDocument();
  });

  it("exibe contador '1 / 3'", () => {
    renderTour();
    expect(screen.getByText("1 / 3")).toBeInTheDocument();
  });
});

// ============================================================================
// AC2: localStorage — não repetir tour já completado
// ============================================================================

describe("Tour component — localStorage permanent dismiss (AC2)", () => {
  it("renderiza null se tourId foi permanentemente descartado", () => {
    localStorage.setItem("smartlic_tour_test_dismissed_permanent", "true");
    const { container } = renderTour();
    expect(container.firstChild).toBeNull();
  });

  it("botão 'Não mostrar novamente' persiste dismiss permanente", () => {
    renderTour();
    fireEvent.click(screen.getByText("Não mostrar novamente"));
    expect(
      localStorage.getItem("smartlic_tour_test_dismissed_permanent")
    ).toBe("true");
  });

  it("storageKey custom override funciona", () => {
    localStorage.setItem("custom_key", "true");
    const { container } = renderTour({ storageKey: "custom_key" });
    expect(container.firstChild).toBeNull();
  });
});

// ============================================================================
// AC3: Navegação Próximo / Voltar / Pular
// ============================================================================

describe("Tour component — navegação (AC3)", () => {
  it("primeiro step não tem botão Voltar", () => {
    renderTour();
    expect(screen.queryByText("Voltar")).not.toBeInTheDocument();
  });

  it("primeiro step mostra botão 'Próximo'", () => {
    renderTour();
    expect(screen.getByText("Próximo")).toBeInTheDocument();
  });

  it("último step mostra botão 'Concluir'", () => {
    const single: TourStepDef[] = [{ id: "s", title: "T", text: "X" }];
    render(<Tour tourId="t" steps={single} active={true} />);
    expect(screen.getByText("Concluir")).toBeInTheDocument();
  });

  it("Próximo avança para o segundo step", async () => {
    renderTour();
    fireEvent.click(screen.getByText("Próximo"));
    await waitFor(() => {
      expect(screen.getByText("Passo Dois")).toBeInTheDocument();
    });
  });

  it("Voltar retorna ao step anterior", async () => {
    renderTour();
    fireEvent.click(screen.getByText("Próximo"));
    await waitFor(() => expect(screen.getByText("Passo Dois")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Voltar"));
    await waitFor(() => expect(screen.getByText("Passo Um")).toBeInTheDocument());
  });

  it("Pular chama onSkip com índice atual", () => {
    const onSkip = jest.fn();
    renderTour({ onSkip });
    fireEvent.click(screen.getByText("Pular"));
    expect(onSkip).toHaveBeenCalledWith(0);
  });

  it("Concluir no último step chama onComplete", async () => {
    const onComplete = jest.fn();
    renderTour({ onComplete });
    fireEvent.click(screen.getByText("Próximo")); // → step 2
    await waitFor(() => expect(screen.getByText("Passo Dois")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Próximo")); // → step 3
    await waitFor(() => expect(screen.getByText("Passo Três")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Concluir"));
    expect(onComplete).toHaveBeenCalledWith(3);
  });
});

// ============================================================================
// AC4: Storage key única por tourId
// ============================================================================

describe("Tour component — storage key por tourId (AC4)", () => {
  it("tourId diferente usa chave de storage diferente", () => {
    localStorage.setItem("smartlic_tour_tour-a_dismissed_permanent", "true");
    // tour-b não deve ser afetado
    const { container } = render(
      <Tour tourId="tour-b" steps={SAMPLE_STEPS} active={true} />
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });
});

// ============================================================================
// AC5: Callbacks onComplete e onSkip
// ============================================================================

describe("Tour component — callbacks (AC5)", () => {
  it("onSkip recebe índice do step ao pular no primeiro", () => {
    const onSkip = jest.fn();
    renderTour({ onSkip });
    fireEvent.click(screen.getByText("Pular"));
    expect(onSkip).toHaveBeenCalledWith(0);
  });

  it("onComplete recebe contagem de steps vistos ao concluir", async () => {
    const single: TourStepDef[] = [{ id: "s1", title: "T1", text: "X1" }];
    const onComplete = jest.fn();
    render(<Tour tourId="t" steps={single} active={true} onComplete={onComplete} />);
    fireEvent.click(screen.getByText("Concluir"));
    expect(onComplete).toHaveBeenCalledWith(1);
  });
});

// ============================================================================
// AC6: onStepChange
// ============================================================================

describe("Tour component — onStepChange (AC6)", () => {
  it("chama onStepChange com step inicial ao abrir", () => {
    const onStepChange = jest.fn();
    renderTour({ onStepChange });
    expect(onStepChange).toHaveBeenCalledWith(0, SAMPLE_STEPS[0]);
  });

  it("chama onStepChange ao navegar para próximo step", async () => {
    const onStepChange = jest.fn();
    renderTour({ onStepChange });
    fireEvent.click(screen.getByText("Próximo"));
    await waitFor(() => {
      expect(onStepChange).toHaveBeenCalledWith(1, SAMPLE_STEPS[1]);
    });
  });
});

// ============================================================================
// AC7: ESC fecha o tour
// ============================================================================

describe("Tour component — teclado ESC (AC7)", () => {
  it("ESC chama onSkip com índice atual", () => {
    const onSkip = jest.fn();
    renderTour({ onSkip });
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onSkip).toHaveBeenCalledWith(0);
  });
});

// ============================================================================
// AC8: showOn — pula steps condicionalmente
// ============================================================================

describe("Tour component — showOn condicional (AC8)", () => {
  it("pula steps onde showOn retorna false", async () => {
    const steps: TourStepDef[] = [
      { id: "s1", title: "Step 1", text: "X1" },
      { id: "s2", title: "Step 2", text: "X2", showOn: () => false },
      { id: "s3", title: "Step 3", text: "X3" },
    ];
    render(<Tour tourId="t" steps={steps} active={true} />);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Próximo"));
    await waitFor(() => {
      // Step 2 deve ser pulado, ir direto pro Step 3
      expect(screen.getByText("Step 3")).toBeInTheDocument();
    });
  });

  it("se todos os steps têm showOn=false, chama onComplete imediatamente", async () => {
    const onComplete = jest.fn();
    const steps: TourStepDef[] = [
      { id: "s1", title: "T", text: "X", showOn: () => false },
    ];
    render(
      <Tour tourId="t" steps={steps} active={true} onComplete={onComplete} />
    );
    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith(0);
    });
  });
});

// ============================================================================
// AC9: beforeShow callback
// ============================================================================

describe("Tour component — beforeShow (AC9)", () => {
  it("chama beforeShow ao navegar para um step", async () => {
    const beforeShow = jest.fn().mockResolvedValue(undefined);
    const steps: TourStepDef[] = [
      { id: "s1", title: "Step 1", text: "X1" },
      { id: "s2", title: "Step 2", text: "X2", beforeShow },
    ];
    render(<Tour tourId="t" steps={steps} active={true} />);
    fireEvent.click(screen.getByText("Próximo"));
    await waitFor(() => {
      expect(beforeShow).toHaveBeenCalled();
    });
  });
});

// ============================================================================
// OnboardingTourButton Component Tests (AC15-17)
// ============================================================================

describe("OnboardingTourButton (AC15-17)", () => {
  it("renderiza o botão '?' flutuante", () => {
    render(<OnboardingTourButton />);
    expect(screen.getByTestId("tour-trigger-button")).toBeInTheDocument();
    expect(screen.getByLabelText("Guia interativo")).toBeInTheDocument();
  });

  it("botão exibe texto '?'", () => {
    render(<OnboardingTourButton />);
    expect(screen.getByTestId("tour-trigger-button")).toHaveTextContent("?");
  });

  it("exibe menu com 3 opções ao clicar (AC16)", () => {
    render(<OnboardingTourButton />);
    expect(screen.queryByTestId("tour-menu")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    expect(screen.getByTestId("tour-menu")).toBeInTheDocument();
    expect(screen.getByTestId("tour-option-search")).toBeInTheDocument();
    expect(screen.getByTestId("tour-option-results")).toBeInTheDocument();
    expect(screen.getByTestId("tour-option-pipeline")).toBeInTheDocument();
  });

  it("exibe labels corretos em português", () => {
    render(<OnboardingTourButton />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    expect(screen.getByText("Tour de busca")).toBeInTheDocument();
    expect(screen.getByText("Tour de resultados")).toBeInTheDocument();
    expect(screen.getByText("Tour de pipeline")).toBeInTheDocument();
  });

  it("exibe badges numerados (1, 2, 3)", () => {
    render(<OnboardingTourButton />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("alterna menu abrir/fechar no clique", () => {
    render(<OnboardingTourButton />);
    const btn = screen.getByTestId("tour-trigger-button");
    fireEvent.click(btn);
    expect(screen.getByTestId("tour-menu")).toBeInTheDocument();
    fireEvent.click(btn);
    expect(screen.queryByTestId("tour-menu")).not.toBeInTheDocument();
  });

  it("tem atributo aria-expanded correto", () => {
    render(<OnboardingTourButton />);
    const btn = screen.getByTestId("tour-trigger-button");
    expect(btn).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
  });

  it("fecha menu ao pressionar Escape", () => {
    render(<OnboardingTourButton />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    expect(screen.getByTestId("tour-menu")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByTestId("tour-menu")).not.toBeInTheDocument();
  });

  it("chama callback ao clicar em opção disponível (AC17)", () => {
    const mockRestart = jest.fn();
    render(<OnboardingTourButton availableTours={{ search: mockRestart }} />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    fireEvent.click(screen.getByTestId("tour-option-search"));
    expect(mockRestart).toHaveBeenCalled();
  });

  it("navega para página correta quando tour está em outra página", () => {
    currentPathname = "/dashboard";
    render(<OnboardingTourButton availableTours={{}} />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    fireEvent.click(screen.getByTestId("tour-option-pipeline"));
    expect(mockPush).toHaveBeenCalledWith("/pipeline?tour=pipeline");
  });

  it("não navega quando já está na página correta", () => {
    currentPathname = "/buscar";
    render(<OnboardingTourButton availableTours={{}} />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    fireEvent.click(screen.getByTestId("tour-option-search"));
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("fecha menu após clicar em uma opção", () => {
    render(<OnboardingTourButton availableTours={{ search: jest.fn() }} />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    expect(screen.getByTestId("tour-menu")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("tour-option-search"));
    expect(screen.queryByTestId("tour-menu")).not.toBeInTheDocument();
  });
});

// ============================================================================
// localStorage persistence por tourId (AC4 — storage keys únicas)
// ============================================================================

describe("localStorage — chaves únicas por tourId", () => {
  it("completar tour 'search' não afeta tour 'results'", () => {
    localStorage.setItem("smartlic_tour_search_dismissed_permanent", "true");
    // results não deve ser afetado
    const { container } = render(
      <Tour tourId="results" steps={SAMPLE_STEPS} active={true} />
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("tour não ativo quando mesmo tourId foi permanentemente dispensado", () => {
    localStorage.setItem("smartlic_tour_persist-test_dismissed_permanent", "true");
    const { container } = render(
      <Tour tourId="persist-test" steps={SAMPLE_STEPS} active={true} />
    );
    expect(container.firstChild).toBeNull();
  });
});
