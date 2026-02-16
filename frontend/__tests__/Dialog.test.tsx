import { render, screen, fireEvent, act } from "@testing-library/react";
import { Dialog } from "../app/components/Dialog";

// Helper to render an open dialog with focusable elements
function renderDialog(props: Partial<React.ComponentProps<typeof Dialog>> = {}) {
  const onClose = jest.fn();
  const result = render(
    <Dialog isOpen={true} onClose={onClose} title="Test Dialog" {...props}>
      <input data-testid="input-1" placeholder="First" />
      <button data-testid="btn-1">Action</button>
      <button data-testid="btn-2">Cancel</button>
    </Dialog>
  );
  return { onClose, ...result };
}

describe("Dialog component", () => {
  describe("ARIA attributes (A11Y-02)", () => {
    it('has role="dialog"', () => {
      renderDialog();
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("has aria-modal=true", () => {
      renderDialog();
      expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
    });

    it("has aria-labelledby pointing to title", () => {
      renderDialog({ id: "my-dialog" });
      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-labelledby", "my-dialog-title");
      expect(screen.getByText("Test Dialog")).toHaveAttribute("id", "my-dialog-title");
    });

    it("renders the title text", () => {
      renderDialog({ title: "Custom Title" });
      expect(screen.getByText("Custom Title")).toBeInTheDocument();
    });
  });

  describe("Visibility", () => {
    it("renders children when open", () => {
      renderDialog();
      expect(screen.getByTestId("input-1")).toBeInTheDocument();
    });

    it("returns null when closed", () => {
      const { container } = render(
        <Dialog isOpen={false} onClose={jest.fn()} title="Hidden">
          <p>Should not render</p>
        </Dialog>
      );
      expect(container.innerHTML).toBe("");
    });
  });

  describe("Escape key handling (UX-02)", () => {
    it("calls onClose when Escape is pressed", () => {
      const { onClose } = renderDialog();
      act(() => {
        fireEvent.keyDown(document, { key: "Escape" });
      });
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("does not call onClose for other keys", () => {
      const { onClose } = renderDialog();
      act(() => {
        fireEvent.keyDown(document, { key: "Enter" });
      });
      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe("Backdrop click", () => {
    it("calls onClose when backdrop is clicked (default)", () => {
      const { onClose } = renderDialog();
      const backdrop = screen.getByRole("dialog");
      fireEvent.click(backdrop);
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("does not call onClose when closeOnBackdropClick=false", () => {
      const { onClose } = renderDialog({ closeOnBackdropClick: false });
      const backdrop = screen.getByRole("dialog");
      fireEvent.click(backdrop);
      expect(onClose).not.toHaveBeenCalled();
    });

    it("does not close when clicking inside the panel", () => {
      const { onClose } = renderDialog();
      fireEvent.click(screen.getByTestId("input-1"));
      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe("Close button", () => {
    it('renders a close button with aria-label="Fechar"', () => {
      renderDialog();
      const closeBtn = screen.getByLabelText("Fechar");
      expect(closeBtn).toBeInTheDocument();
    });

    it("calls onClose when close button is clicked", () => {
      const { onClose } = renderDialog();
      fireEvent.click(screen.getByLabelText("Fechar"));
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("Focus trap (A11Y-01, WCAG 2.4.3)", () => {
    it("traps Tab at the last focusable element", () => {
      renderDialog();
      const lastBtn = screen.getByTestId("btn-2");
      lastBtn.focus();
      expect(document.activeElement).toBe(lastBtn);

      // Tab from last element should wrap to first
      const panel = lastBtn.closest('[tabindex="-1"]')!;
      fireEvent.keyDown(panel, { key: "Tab" });

      // The focus trap should have moved focus to the close button (first focusable)
      const closeBtn = screen.getByLabelText("Fechar");
      expect(document.activeElement).toBe(closeBtn);
    });

    it("traps Shift+Tab at the first focusable element", () => {
      renderDialog();
      const closeBtn = screen.getByLabelText("Fechar");
      closeBtn.focus();

      const panel = closeBtn.closest('[tabindex="-1"]')!;
      fireEvent.keyDown(panel, { key: "Tab", shiftKey: true });

      const lastBtn = screen.getByTestId("btn-2");
      expect(document.activeElement).toBe(lastBtn);
    });
  });

  describe("Body scroll lock", () => {
    it("sets body overflow to hidden when open", () => {
      renderDialog();
      expect(document.body.style.overflow).toBe("hidden");
    });

    it("restores body overflow when closed", () => {
      const { rerender } = render(
        <Dialog isOpen={true} onClose={jest.fn()} title="Test">
          <p>Content</p>
        </Dialog>
      );
      expect(document.body.style.overflow).toBe("hidden");

      rerender(
        <Dialog isOpen={false} onClose={jest.fn()} title="Test">
          <p>Content</p>
        </Dialog>
      );
      expect(document.body.style.overflow).not.toBe("hidden");
    });
  });

  describe("Focus restoration", () => {
    it("restores focus to trigger element on close", () => {
      const trigger = document.createElement("button");
      trigger.textContent = "Open";
      document.body.appendChild(trigger);
      trigger.focus();

      const { rerender } = render(
        <Dialog isOpen={true} onClose={jest.fn()} title="Test">
          <p>Content</p>
        </Dialog>
      );

      rerender(
        <Dialog isOpen={false} onClose={jest.fn()} title="Test">
          <p>Content</p>
        </Dialog>
      );

      expect(document.activeElement).toBe(trigger);
      document.body.removeChild(trigger);
    });
  });

  describe("Custom className", () => {
    it("applies className to the panel", () => {
      renderDialog({ className: "max-w-md custom-class" });
      const panel = screen.getByRole("dialog").firstElementChild;
      expect(panel).toHaveClass("max-w-md");
      expect(panel).toHaveClass("custom-class");
    });
  });
});
