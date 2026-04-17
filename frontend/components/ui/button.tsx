import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  /* STORY-2.5: disabled:opacity-50 → WCAG AA tokens (4.6:1 light / 4.5:1 dark) */
  "inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-2 disabled:pointer-events-none disabled:bg-surface-disabled disabled:text-ink-disabled disabled:cursor-not-allowed",
  {
    variants: {
      variant: {
        primary:
          "bg-brand-navy text-white hover:bg-brand-blue-hover rounded-button",
        secondary:
          "bg-surface-1 text-ink-secondary hover:text-ink hover:bg-surface-2 rounded-button border border-DEFAULT",
        destructive:
          "bg-error text-white hover:bg-red-700 rounded-button",
        ghost:
          "text-ink-secondary hover:text-ink hover:bg-surface-1 rounded-button",
        link:
          "text-brand-blue underline-offset-4 hover:underline",
        outline:
          "border border-DEFAULT bg-transparent text-ink hover:bg-surface-1 rounded-button",
      },
      size: {
        sm: "h-8 px-3 text-xs gap-1.5",
        default: "h-10 px-4 py-2 text-sm gap-2",
        lg: "h-12 px-6 text-base gap-2.5",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
);

/**
 * Reusable Button component with variants, sizes, loading state, and accessibility built-in.
 * Supports icon-only mode (enforces aria-label at type level), asChild pattern via Radix Slot,
 * and disabled/loading states with WCAG AA contrast tokens.
 *
 * @param variant - Visual style: "primary" | "secondary" | "destructive" | "ghost" | "outline" | "link"
 * @param size - Button size: "sm" | "default" | "lg" | "icon"
 * @param loading - Shows animated spinner and disables interaction when true
 * @param disabled - Disables the button (also triggered by loading)
 * @param asChild - Renders as the child element via Radix Slot (useful for Link wrappers)
 * @param children - Button label or content
 * @param aria-label - Required when size="icon" (enforced by TypeScript)
 *
 * @example
 * // Primary button
 * <Button variant="primary">Buscar Licitações</Button>
 *
 * @example
 * // Loading state
 * <Button loading>Salvando...</Button>
 *
 * @example
 * // Icon-only (aria-label required)
 * <Button size="icon" aria-label="Fechar"><X className="h-4 w-4" /></Button>
 *
 * @example
 * // As link (asChild)
 * <Button asChild variant="outline"><Link href="/planos">Ver planos</Link></Button>
 */
interface BaseButtonProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "aria-label">,
    Omit<VariantProps<typeof buttonVariants>, "size"> {
  asChild?: boolean;
  loading?: boolean;
}

/**
 * Icon-only buttons MUST provide an aria-label for accessibility (AC3).
 * TypeScript will error at compile time if aria-label is missing when size="icon".
 */
type IconButtonProps = BaseButtonProps & {
  size: "icon";
  "aria-label": string;
};

type StandardButtonProps = BaseButtonProps & {
  size?: "sm" | "default" | "lg" | null;
  "aria-label"?: string;
};

export type ButtonProps = IconButtonProps | StandardButtonProps;

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, disabled, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4 shrink-0"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {children}
      </Comp>
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
