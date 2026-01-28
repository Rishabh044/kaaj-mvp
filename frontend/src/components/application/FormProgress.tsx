/**
 * Progress indicator for the multi-step application form.
 */

interface FormProgressProps {
  currentStep: number;
  totalSteps: number;
  steps: { title: string; description?: string }[];
}

export function FormProgress({ currentStep, totalSteps, steps }: FormProgressProps) {
  return (
    <nav aria-label="Progress">
      <ol className="flex items-center">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;
          const isLast = stepNumber === totalSteps;

          return (
            <li
              key={step.title}
              className={`relative ${isLast ? '' : 'flex-1'}`}
            >
              <div className="flex items-center">
                <span
                  className={`
                    relative flex h-8 w-8 items-center justify-center rounded-full
                    ${
                      isCompleted
                        ? 'bg-primary-600'
                        : isCurrent
                          ? 'border-2 border-primary-600 bg-white'
                          : 'border-2 border-gray-300 bg-white'
                    }
                  `}
                >
                  {isCompleted ? (
                    <svg
                      className="h-5 w-5 text-white"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <span
                      className={`text-sm font-medium ${
                        isCurrent ? 'text-primary-600' : 'text-gray-500'
                      }`}
                    >
                      {stepNumber}
                    </span>
                  )}
                </span>
                {!isLast && (
                  <div
                    className={`ml-4 h-0.5 w-full ${
                      isCompleted ? 'bg-primary-600' : 'bg-gray-300'
                    }`}
                  />
                )}
              </div>
              <span
                className={`
                  absolute -bottom-6 left-0 w-max text-xs font-medium
                  ${isCurrent ? 'text-primary-600' : 'text-gray-500'}
                `}
              >
                {step.title}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export default FormProgress;
