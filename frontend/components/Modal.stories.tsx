import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { Modal } from "./Modal";
import { Button } from "./ui/button";

const meta: Meta<typeof Modal> = {
  title: "Feedback/Modal",
  component: Modal,
  tags: ["autodocs"],
  argTypes: {
    size: { control: "select", options: ["sm", "md", "lg", "xl"] },
    role: { control: "select", options: ["dialog", "alertdialog"] },
  },
};
export default meta;
type Story = StoryObj<typeof Modal>;

export const Default: Story = {
  args: {
    isOpen: true,
    title: "Confirmar ação",
    description: "Deseja realmente excluir este item?",
    children: <p className="text-sm text-ink-secondary">Esta ação não pode ser desfeita.</p>,
    onClose: () => {},
  },
};

export const Small: Story = {
  args: { ...Default.args, size: "sm", title: "Aviso rápido" },
};

export const Large: Story = {
  args: { ...Default.args, size: "lg", title: "Detalhes da licitação" },
};

export const AlertDialog: Story = {
  args: { ...Default.args, role: "alertdialog", title: "Cancelar assinatura?" },
};

function InteractiveDemo() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button onClick={() => setOpen(true)}>Abrir Modal</Button>
      <Modal isOpen={open} onClose={() => setOpen(false)} title="Modal interativo">
        <p className="text-sm text-ink-secondary mb-4">Conteúdo do modal.</p>
        <Button onClick={() => setOpen(false)} variant="primary">Fechar</Button>
      </Modal>
    </>
  );
}

export const Interactive: Story = {
  render: () => <InteractiveDemo />,
};
