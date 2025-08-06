import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

const spinnerVariants = cva(
  'animate-spin',
  {
    variants: {
      size: {
        sm: 'h-4 w-4',
        md: 'h-6 w-6',
        lg: 'h-8 w-8',
        xl: 'h-12 w-12',
      },
      color: {
        primary: 'text-primary-600',
        gray: 'text-gray-400',
        white: 'text-white',
        current: 'text-current',
      },
    },
    defaultVariants: {
      size: 'md',
      color: 'primary',
    },
  }
);

export interface LoadingSpinnerProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, 'color'>,
    VariantProps<typeof spinnerVariants> {
  text?: string;
  centered?: boolean;
}

export const LoadingSpinner = React.forwardRef<HTMLDivElement, LoadingSpinnerProps>(
  ({ className, size, color, text, centered, ...props }, ref) => {
    const Component = (
      <div
        ref={ref}
        className={clsx(
          'flex items-center',
          centered && 'justify-center',
          text ? 'gap-2' : '',
          className
        )}
        {...props}
      >
        <Loader2 className={spinnerVariants({ size, color })} />
        {text && <span className="text-sm text-gray-600">{text}</span>}
      </div>
    );

    if (centered) {
      return (
        <div className="flex items-center justify-center w-full h-full min-h-[100px]">
          {Component}
        </div>
      );
    }

    return Component;
  }
);

LoadingSpinner.displayName = 'LoadingSpinner';

// Page-level loading component
export interface PageLoadingProps {
  message?: string;
}

export const PageLoading: React.FC<PageLoadingProps> = ({ message = 'Loading...' }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
      <LoadingSpinner size="xl" />
      <p className="text-lg text-gray-600 animate-pulse">{message}</p>
    </div>
  );
};

// Inline loading component for buttons and small spaces
export interface InlineLoadingProps extends LoadingSpinnerProps {
  dots?: boolean;
}

export const InlineLoading: React.FC<InlineLoadingProps> = ({ 
  dots = false, 
  text, 
  ...props 
}) => {
  if (dots) {
    return (
      <span className="loading-dots">
        {text || 'Loading'}
      </span>
    );
  }

  return <LoadingSpinner text={text} {...props} />;
}; 