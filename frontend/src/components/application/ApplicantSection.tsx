/**
 * Applicant information form section.
 * Collects credit scores and personal information.
 */

import { Input, Toggle } from '../ui';
import type { ApplicantInfo } from '../../types';

interface ApplicantSectionProps {
  data: Partial<ApplicantInfo>;
  onChange: (data: Partial<ApplicantInfo>) => void;
  errors?: Record<string, string>;
}

export function ApplicantSection({
  data,
  onChange,
  errors = {},
}: ApplicantSectionProps) {
  const handleChange = (field: keyof ApplicantInfo, value: unknown) => {
    onChange({ ...data, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900">Applicant Information</h2>
        <p className="mt-1 text-sm text-gray-500">
          Enter the personal guarantor&apos;s credit and personal information.
        </p>
      </div>

      {/* Credit Scores */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <Input
          label="FICO Score"
          type="number"
          min={300}
          max={850}
          value={data.fico_score ?? ''}
          onChange={(e) => handleChange('fico_score', parseInt(e.target.value) || 0)}
          error={errors.fico_score}
          helperText="Primary credit score (300-850)"
          required
          data-testid="fico-score"
        />

        <Input
          label="TransUnion Score"
          type="number"
          min={300}
          max={850}
          value={data.transunion_score ?? ''}
          onChange={(e) =>
            handleChange('transunion_score', e.target.value ? parseInt(e.target.value) : undefined)
          }
          error={errors.transunion_score}
          helperText="Optional (300-850)"
        />

        <Input
          label="Experian Score"
          type="number"
          min={300}
          max={850}
          value={data.experian_score ?? ''}
          onChange={(e) =>
            handleChange('experian_score', e.target.value ? parseInt(e.target.value) : undefined)
          }
          error={errors.experian_score}
          helperText="Optional (300-850)"
        />

        <Input
          label="Equifax Score"
          type="number"
          min={300}
          max={850}
          value={data.equifax_score ?? ''}
          onChange={(e) =>
            handleChange('equifax_score', e.target.value ? parseInt(e.target.value) : undefined)
          }
          error={errors.equifax_score}
          helperText="Optional (300-850)"
        />
      </div>

      {/* Personal Flags */}
      <div className="space-y-4 pt-4 border-t border-gray-200">
        <Toggle
          label="Homeowner"
          description="Does the applicant own their home?"
          checked={data.is_homeowner ?? false}
          onChange={(e) => handleChange('is_homeowner', e.target.checked)}
          data-testid="is-homeowner"
        />

        <Toggle
          label="US Citizen"
          description="Is the applicant a US citizen?"
          checked={data.is_us_citizen ?? true}
          onChange={(e) => handleChange('is_us_citizen', e.target.checked)}
        />

        <Toggle
          label="Has CDL"
          description="Does the applicant have a Commercial Driver&apos;s License?"
          checked={data.has_cdl ?? false}
          onChange={(e) => handleChange('has_cdl', e.target.checked)}
        />
      </div>

      {/* CDL and Experience (shown when relevant) */}
      {data.has_cdl && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 pt-4">
          <Input
            label="CDL Years"
            type="number"
            min={0}
            value={data.cdl_years ?? ''}
            onChange={(e) =>
              handleChange('cdl_years', e.target.value ? parseInt(e.target.value) : undefined)
            }
            error={errors.cdl_years}
            helperText="Years holding CDL"
          />

          <Input
            label="Industry Experience (Years)"
            type="number"
            min={0}
            value={data.industry_experience_years ?? ''}
            onChange={(e) =>
              handleChange(
                'industry_experience_years',
                e.target.value ? parseInt(e.target.value) : undefined
              )
            }
            error={errors.industry_experience_years}
            helperText="Years of trucking/industry experience"
          />
        </div>
      )}
    </div>
  );
}

export default ApplicantSection;
