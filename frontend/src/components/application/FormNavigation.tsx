/**
 * Navigation buttons for the multi-step form.
 */

import { Button } from '../ui';

interface FormNavigationProps {
  currentStep: number;
  totalSteps: number;
  onPrevious: () => void;
  onNext: () => void;
  onSubmit: () => void;
  isSubmitting?: boolean;
  canGoNext?: boolean;
}

export function FormNavigation({
  currentStep,
  totalSteps,
  onPrevious,
  onNext,
  onSubmit,
  isSubmitting = false,
  canGoNext = true,
}: FormNavigationProps) {
  const isFirstStep = currentStep === 1;
  const isLastStep = currentStep === totalSteps;

  return (
    <div className="flex justify-between pt-6 border-t border-gray-200">
      <Button
        type="button"
        variant="secondary"
        onClick={onPrevious}
        disabled={isFirstStep || isSubmitting}
      >
        Previous
      </Button>

      {isLastStep ? (
        <Button
          type="button"
          onClick={onSubmit}
          isLoading={isSubmitting}
          disabled={!canGoNext || isSubmitting}
        >
          Submit Application
        </Button>
      ) : (
        <Button
          type="button"
          onClick={onNext}
          disabled={!canGoNext || isSubmitting}
        >
          Next
        </Button>
      )}
    </div>
  );
}

export default FormNavigation;
