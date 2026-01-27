/**
 * Multi-step application form container.
 * Orchestrates form sections and handles submission.
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { Card } from '../ui';
import { FormProgress } from './FormProgress';
import { FormNavigation } from './FormNavigation';
import { ApplicantSection } from './ApplicantSection';
import { BusinessSection } from './BusinessSection';
import { EquipmentSection } from './EquipmentSection';
import { CreditHistorySection } from './CreditHistorySection';
import { LoanRequestSection } from './LoanRequestSection';

import { submitApplication } from '../../api';
import type {
  ApplicationFormState,
  LoanApplicationInput,
  ApplicantInfo,
  BusinessInfo,
  EquipmentInfo,
  CreditHistoryInfo,
  LoanRequestInfo,
} from '../../types';
import { DEFAULT_FORM_STATE } from '../../types';

const FORM_STEPS = [
  { title: 'Applicant', description: 'Credit and personal info' },
  { title: 'Business', description: 'Business details' },
  { title: 'Equipment', description: 'Equipment info' },
  { title: 'Credit History', description: 'Derogatory items' },
  { title: 'Loan Request', description: 'Financing details' },
];

type ValidationErrors = Record<string, string>;

function validateStep(step: number, formData: ApplicationFormState): ValidationErrors {
  const errors: ValidationErrors = {};

  switch (step) {
    case 1: // Applicant
      if (!formData.applicant.fico_score) {
        errors.fico_score = 'FICO score is required';
      } else if (
        formData.applicant.fico_score < 300 ||
        formData.applicant.fico_score > 850
      ) {
        errors.fico_score = 'FICO score must be between 300 and 850';
      }
      break;

    case 2: // Business
      if (!formData.business.name?.trim()) {
        errors.name = 'Business name is required';
      }
      if (!formData.business.state) {
        errors.state = 'State is required';
      }
      if (
        formData.business.years_in_business === undefined ||
        formData.business.years_in_business < 0
      ) {
        errors.years_in_business = 'Years in business is required';
      }
      break;

    case 3: // Equipment
      if (!formData.equipment.category) {
        errors.category = 'Equipment category is required';
      }
      if (!formData.equipment.year) {
        errors.year = 'Equipment year is required';
      }
      break;

    case 4: // Credit History
      // No required fields, but validate conditional fields
      if (
        formData.credit_history.has_bankruptcy &&
        formData.credit_history.bankruptcy_discharge_years !== undefined &&
        formData.credit_history.bankruptcy_discharge_years < 0
      ) {
        errors.bankruptcy_discharge_years = 'Years must be positive';
      }
      break;

    case 5: // Loan Request
      if (!formData.loan_request.amount || formData.loan_request.amount <= 0) {
        errors.amount = 'Loan amount is required';
      }
      break;
  }

  return errors;
}

function buildApplicationInput(formData: ApplicationFormState): LoanApplicationInput {
  return {
    applicant: formData.applicant as ApplicantInfo,
    business: formData.business as BusinessInfo,
    credit_history: formData.credit_history as CreditHistoryInfo,
    equipment: formData.equipment as EquipmentInfo,
    loan_request: formData.loan_request as LoanRequestInfo,
    business_credit:
      formData.business_credit &&
      Object.keys(formData.business_credit).length > 0
        ? formData.business_credit
        : undefined,
  };
}

export function ApplicationForm() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<ApplicationFormState>(DEFAULT_FORM_STATE);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const updateFormData = useCallback(
    <K extends keyof ApplicationFormState>(
      section: K,
      data: ApplicationFormState[K]
    ) => {
      setFormData((prev) => ({
        ...prev,
        [section]: data,
      }));
      // Clear errors when user makes changes
      setErrors({});
      setSubmitError(null);
    },
    []
  );

  const handleNext = useCallback(() => {
    const validationErrors = validateStep(currentStep, formData);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setCurrentStep((prev) => Math.min(prev + 1, FORM_STEPS.length));
  }, [currentStep, formData]);

  const handlePrevious = useCallback(() => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
    setErrors({});
  }, []);

  const handleSubmit = useCallback(async () => {
    // Validate final step
    const validationErrors = validateStep(currentStep, formData);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const input = buildApplicationInput(formData);
      const response = await submitApplication(input);

      // Navigate to results page
      navigate(`/results/${response.id}`);
    } catch (error) {
      setSubmitError(
        error instanceof Error
          ? error.message
          : 'Failed to submit application. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  }, [currentStep, formData, navigate]);

  const renderCurrentSection = () => {
    switch (currentStep) {
      case 1:
        return (
          <ApplicantSection
            data={formData.applicant}
            onChange={(data) => updateFormData('applicant', data)}
            errors={errors}
          />
        );
      case 2:
        return (
          <BusinessSection
            data={formData.business}
            onChange={(data) => updateFormData('business', data)}
            errors={errors}
          />
        );
      case 3:
        return (
          <EquipmentSection
            data={formData.equipment}
            onChange={(data) => updateFormData('equipment', data)}
            errors={errors}
          />
        );
      case 4:
        return (
          <CreditHistorySection
            data={formData.credit_history}
            onChange={(data) => updateFormData('credit_history', data)}
            errors={errors}
          />
        );
      case 5:
        return (
          <LoanRequestSection
            data={formData.loan_request}
            onChange={(data) => updateFormData('loan_request', data)}
            errors={errors}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress Indicator */}
      <div className="mb-12">
        <FormProgress
          currentStep={currentStep}
          totalSteps={FORM_STEPS.length}
          steps={FORM_STEPS}
        />
      </div>

      {/* Form Content */}
      <Card padding="lg">
        {/* Submit Error */}
        {submitError && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-red-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{submitError}</p>
              </div>
            </div>
          </div>
        )}

        {/* Current Section */}
        {renderCurrentSection()}

        {/* Navigation */}
        <FormNavigation
          currentStep={currentStep}
          totalSteps={FORM_STEPS.length}
          onPrevious={handlePrevious}
          onNext={handleNext}
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
          canGoNext={Object.keys(errors).length === 0}
        />
      </Card>
    </div>
  );
}

export default ApplicationForm;
