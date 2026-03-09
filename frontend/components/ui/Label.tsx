import * as React from "react";
import { cn } from "@/lib/utils";

export interface LabelProps
  extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, required, children, ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={cn(
          "block text-sm font-medium text-ink-secondary mb-1",
          required && "after:content-['*'] after:ml-0.5 after:text-error",
          className
        )}
        {...props}
      >
        {children}
      </label>
    );
  }
);
Label.displayName = "Label";

export { Label };
