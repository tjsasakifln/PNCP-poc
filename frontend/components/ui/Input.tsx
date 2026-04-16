import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const inputVariants = cva(
  /* STORY-2.5: disabled:opacity-50 → WCAG AA tokens (4.6:1 light / 4.5:1 dark) */
  "w-full border bg-surface-0 text-ink placeholder:text-ink-muted transition-colors focus:outline-none disabled:bg-surface-disabled disabled:text-ink-disabled disabled:cursor-not-allowed",
  {
    variants: {
      inputSize: {
        sm: "h-8 px-3 text-xs rounded-input",
        default: "h-10 px-4 py-2 text-sm rounded-input",
        lg: "h-12 px-4 py-3 text-base rounded-input",
      },
      state: {
        default:
          "border-DEFAULT focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20",
        error:
          "border-error focus:border-error focus:ring-2 focus:ring-error/20",
        success:
          "border-success focus:border-success focus:ring-2 focus:ring-success/20",
      },
    },
    defaultVariants: {
      inputSize: "default",
      state: "default",
    },
  }
);

/**
 * Accessible Input component with CVA variants, error/helper text, and WCAG AA contrast.
 * Wraps a native `<input>` with optional error message (role="alert") and helper text.
 * Supports size variants (sm/default/lg) and state variants (default/error/success).
 *
 * @param inputSize - Size variant: "sm" | "default" | "lg"
 * @param state - Visual state: "default" | "error" | "success" (auto-set to "error" when error prop present)
 * @param error - Error message shown below input with role="alert"; also sets aria-invalid
 * @param errorTestId - data-testid for the error message paragraph
 * @param helperText - Helper text shown below input when no error
 * @param id - Required for aria-describedby linkage between input and error/helper
 *
 * @example
 * // Basic usage
 * <Input placeholder="Digite seu CNPJ" />
 *
 * @example
 * // With error
 * <Input id="cnpj" error="CNPJ inválido" errorTestId="cnpj-error" />
 *
 * @example
 * // With helper text
 * <Input id="keyword" helperText="Separe palavras com vírgula" inputSize="sm" />
 */
export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size">,
    VariantProps<typeof inputVariants> {
  error?: string;
  errorTestId?: string;
  helperText?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    { className, inputSize, state, error, errorTestId, helperText, id, type, ...props },
    ref
  ) => {
    const effectiveState = error ? "error" : state;
    const descriptionId = id ? `${id}-description` : undefined;
    const errorId = id ? `${id}-error` : undefined;

    const ariaDescribedBy = [
      error && errorId,
      helperText && !error && descriptionId,
    ]
      .filter(Boolean)
      .join(" ") || undefined;

    return (
      <div className="w-full">
        <input
          ref={ref}
          id={id}
          type={type}
          className={cn(
            inputVariants({ inputSize, state: effectiveState }),
            className
          )}
          aria-invalid={!!error}
          aria-describedby={ariaDescribedBy}
          {...props}
        />
        {error && (
          <p id={errorId} className="mt-1 text-xs text-error" role="alert" data-testid={errorTestId}>
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={descriptionId} className="mt-1 text-xs text-ink-secondary">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input, inputVariants };
