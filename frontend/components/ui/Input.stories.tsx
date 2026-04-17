import type { Meta, StoryObj } from "@storybook/react";
import { Input } from "./Input";

const meta: Meta<typeof Input> = {
  title: "UI/Input",
  component: Input,
  tags: ["autodocs"],
  argTypes: {
    inputSize: { control: "select", options: ["sm", "default", "lg"] },
    state: { control: "select", options: ["default", "error", "success"] },
    disabled: { control: "boolean" },
  },
};
export default meta;
type Story = StoryObj<typeof Input>;

export const Default: Story = {
  args: { placeholder: "Digite seu email", id: "email-input" },
};
export const WithError: Story = {
  args: { placeholder: "Email inválido", state: "error", error: "Formato de email inválido", id: "email-err" },
};
export const Success: Story = {
  args: { placeholder: "Email válido", state: "success", id: "email-ok" },
};
export const Small: Story = {
  args: { placeholder: "Busca rápida", inputSize: "sm", id: "sm-input" },
};
export const Large: Story = {
  args: { placeholder: "Pesquisar licitações...", inputSize: "lg", id: "lg-input" },
};
export const Disabled: Story = {
  args: { placeholder: "Campo desabilitado", disabled: true, id: "dis-input" },
};
export const WithHelper: Story = {
  args: { placeholder: "CNPJ da empresa", helperText: "Formato: 00.000.000/0000-00", id: "cnpj-input" },
};
