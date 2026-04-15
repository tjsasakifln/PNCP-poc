/**
 * STORY-2.6 — Modal ARIA padronization tests.
 */
import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { Modal } from '@/components/Modal';

function ModalHarness({
  initialOpen = true,
  ...props
}: Partial<React.ComponentProps<typeof Modal>> & { initialOpen?: boolean }) {
  const [open, setOpen] = React.useState(initialOpen);
  return (
    <Modal
      isOpen={open}
      onClose={() => setOpen(false)}
      title="Confirmação"
      description="Tem certeza desta operação?"
      {...props}
    >
      <button>Confirmar</button>
    </Modal>
  );
}

describe('STORY-2.6 — <Modal> canônico (AC1+AC3)', () => {
  it('renderiza com role="dialog" e aria-modal="true"', () => {
    render(<ModalHarness />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('aceita role="alertdialog"', () => {
    render(<ModalHarness role="alertdialog" />);
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });

  it('tem aria-labelledby apontando para o título', () => {
    render(<ModalHarness />);
    const dialog = screen.getByRole('dialog');
    const titleId = dialog.getAttribute('aria-labelledby');
    expect(titleId).toBeTruthy();
    expect(document.getElementById(titleId!)).toHaveTextContent('Confirmação');
  });

  it('tem aria-describedby quando description fornecida', () => {
    render(<ModalHarness />);
    const dialog = screen.getByRole('dialog');
    const descId = dialog.getAttribute('aria-describedby');
    expect(descId).toBeTruthy();
    expect(document.getElementById(descId!)).toHaveTextContent('Tem certeza desta operação?');
  });

  it('aria-describedby ausente quando description vazia', () => {
    render(<ModalHarness description={undefined} />);
    expect(screen.getByRole('dialog').hasAttribute('aria-describedby')).toBe(false);
  });

  it('não renderiza quando isOpen=false', () => {
    render(<Modal isOpen={false} onClose={() => {}} title="X">conteudo</Modal>);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('Escape dispara onClose quando closeOnEsc=true', () => {
    const onClose = jest.fn();
    render(<Modal isOpen onClose={onClose} title="X"><button>x</button></Modal>);
    act(() => {
      fireEvent.keyDown(window, { key: 'Escape' });
    });
    expect(onClose).toHaveBeenCalled();
  });

  it('Escape NÃO dispara onClose quando closeOnEsc=false', () => {
    const onClose = jest.fn();
    render(
      <Modal isOpen onClose={onClose} title="X" closeOnEsc={false}>
        <button>x</button>
      </Modal>
    );
    act(() => {
      fireEvent.keyDown(window, { key: 'Escape' });
    });
    expect(onClose).not.toHaveBeenCalled();
  });

  it('click no overlay dispara onClose por padrão', () => {
    const onClose = jest.fn();
    render(<Modal isOpen onClose={onClose} title="X"><button>x</button></Modal>);
    fireEvent.click(screen.getByTestId('modal-overlay'));
    expect(onClose).toHaveBeenCalled();
  });

  it('click no overlay NÃO dispara onClose quando closeOnOverlayClick=false', () => {
    const onClose = jest.fn();
    render(
      <Modal isOpen onClose={onClose} title="X" closeOnOverlayClick={false}>
        <button>x</button>
      </Modal>
    );
    fireEvent.click(screen.getByTestId('modal-overlay'));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('botão de fechar tem aria-label e dispara onClose', () => {
    const onClose = jest.fn();
    render(<Modal isOpen onClose={onClose} title="X"><button>x</button></Modal>);
    fireEvent.click(screen.getByLabelText('Fechar modal'));
    expect(onClose).toHaveBeenCalled();
  });

  it('hideCloseButton omite o botão X', () => {
    render(
      <Modal isOpen onClose={() => {}} title="X" hideCloseButton>
        <button>x</button>
      </Modal>
    );
    expect(screen.queryByLabelText('Fechar modal')).not.toBeInTheDocument();
  });

  it('body overflow=hidden quando aberto', () => {
    const { rerender } = render(<ModalHarness />);
    expect(document.body.style.overflow).toBe('hidden');
    rerender(<Modal isOpen={false} onClose={() => {}} title="X">x</Modal>);
    expect(document.body.style.overflow).not.toBe('hidden');
  });
});

describe('STORY-2.6 — Modais existentes têm ARIA padronizado (AC2)', () => {
  it('PaymentRecoveryModal markup tem aria-modal+aria-labelledby+aria-describedby', () => {
    // Static check via source — não importamos para evitar useAuth deps.
    const fs = jest.requireActual('fs') as typeof import('fs');
    const path = jest.requireActual('path') as typeof import('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../components/billing/PaymentRecoveryModal.tsx'),
      'utf-8'
    );
    expect(src).toContain('role="alertdialog"');
    expect(src).toContain('aria-modal="true"');
    expect(src).toContain('aria-labelledby="payment-recovery-title"');
    expect(src).toContain('aria-describedby="payment-recovery-desc"');
  });

  it('CancelSubscriptionModal markup tem aria-modal', () => {
    const fs = jest.requireActual('fs') as typeof import('fs');
    const path = jest.requireActual('path') as typeof import('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../components/account/CancelSubscriptionModal.tsx'),
      'utf-8'
    );
    expect(src).toContain('aria-modal="true"');
    expect(src).toContain('aria-labelledby="cancel-title"');
  });

  it('DeepAnalysisModal markup tem role+aria-modal', () => {
    const fs = jest.requireActual('fs') as typeof import('fs');
    const path = jest.requireActual('path') as typeof import('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../components/DeepAnalysisModal.tsx'),
      'utf-8'
    );
    expect(src).toContain('role="dialog"');
    expect(src).toContain('aria-modal="true"');
  });
});
