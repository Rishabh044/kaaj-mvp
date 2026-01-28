/**
 * Credit history information form section.
 * Collects derogatory credit history items.
 */

import { Input, Toggle, Select } from '../ui';
import type { CreditHistoryInfo, BankruptcyChapter } from '../../types';

interface CreditHistorySectionProps {
  data: Partial<CreditHistoryInfo>;
  onChange: (data: Partial<CreditHistoryInfo>) => void;
  errors?: Record<string, string>;
}

const bankruptcyChapterOptions = [
  { value: '7', label: 'Chapter 7' },
  { value: '11', label: 'Chapter 11' },
  { value: '13', label: 'Chapter 13' },
];

export function CreditHistorySection({
  data,
  onChange,
  errors = {},
}: CreditHistorySectionProps) {
  const handleChange = (field: keyof CreditHistoryInfo, value: unknown) => {
    onChange({ ...data, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900">Credit History</h2>
        <p className="mt-1 text-sm text-gray-500">
          Provide information about any credit history issues.
        </p>
      </div>

      {/* Bankruptcy */}
      <div className="space-y-4">
        <Toggle
          label="Bankruptcy"
          description="Has the applicant filed for bankruptcy?"
          checked={data.has_bankruptcy ?? false}
          onChange={(e) => {
            handleChange('has_bankruptcy', e.target.checked);
            if (!e.target.checked) {
              handleChange('bankruptcy_discharge_years', undefined);
              handleChange('bankruptcy_chapter', undefined);
            }
          }}
          data-testid="has-bankruptcy"
        />

        {data.has_bankruptcy && (
          <div className="ml-6 grid grid-cols-1 gap-4 sm:grid-cols-2 pl-4 border-l-2 border-gray-200">
            <Input
              label="Years Since Discharge"
              type="number"
              min={0}
              step={0.5}
              value={data.bankruptcy_discharge_years ?? ''}
              onChange={(e) =>
                handleChange(
                  'bankruptcy_discharge_years',
                  e.target.value ? parseFloat(e.target.value) : undefined
                )
              }
              error={errors.bankruptcy_discharge_years}
              helperText="Leave blank if not yet discharged"
            />

            <Select
              label="Bankruptcy Chapter"
              options={bankruptcyChapterOptions}
              value={data.bankruptcy_chapter ?? ''}
              onChange={(e) =>
                handleChange('bankruptcy_chapter', (e.target.value || undefined) as BankruptcyChapter)
              }
              error={errors.bankruptcy_chapter}
              placeholder="Select chapter..."
            />
          </div>
        )}
      </div>

      {/* Judgements */}
      <div className="space-y-4 pt-4 border-t border-gray-200">
        <Toggle
          label="Open Judgements"
          description="Are there any open judgements against the applicant?"
          checked={data.has_open_judgements ?? false}
          onChange={(e) => {
            handleChange('has_open_judgements', e.target.checked);
            if (!e.target.checked) {
              handleChange('judgement_amount', undefined);
            }
          }}
        />

        {data.has_open_judgements && (
          <div className="ml-6 pl-4 border-l-2 border-gray-200">
            <Input
              label="Total Judgement Amount"
              type="number"
              min={0}
              value={data.judgement_amount ?? ''}
              onChange={(e) =>
                handleChange(
                  'judgement_amount',
                  e.target.value ? parseInt(e.target.value) : undefined
                )
              }
              error={errors.judgement_amount}
              helperText="Total amount in dollars"
            />
          </div>
        )}
      </div>

      {/* Other Derogatory Items */}
      <div className="space-y-4 pt-4 border-t border-gray-200">
        <Toggle
          label="Foreclosure"
          description="Has the applicant had a foreclosure?"
          checked={data.has_foreclosure ?? false}
          onChange={(e) => handleChange('has_foreclosure', e.target.checked)}
        />

        <Toggle
          label="Repossession"
          description="Has the applicant had a repossession?"
          checked={data.has_repossession ?? false}
          onChange={(e) => handleChange('has_repossession', e.target.checked)}
        />
      </div>

      {/* Tax Liens */}
      <div className="space-y-4 pt-4 border-t border-gray-200">
        <Toggle
          label="Tax Liens"
          description="Are there any outstanding tax liens?"
          checked={data.has_tax_liens ?? false}
          onChange={(e) => {
            handleChange('has_tax_liens', e.target.checked);
            if (!e.target.checked) {
              handleChange('tax_lien_amount', undefined);
            }
          }}
        />

        {data.has_tax_liens && (
          <div className="ml-6 pl-4 border-l-2 border-gray-200">
            <Input
              label="Total Tax Lien Amount"
              type="number"
              min={0}
              value={data.tax_lien_amount ?? ''}
              onChange={(e) =>
                handleChange(
                  'tax_lien_amount',
                  e.target.value ? parseInt(e.target.value) : undefined
                )
              }
              error={errors.tax_lien_amount}
              helperText="Total amount in dollars"
            />
          </div>
        )}
      </div>

      {/* Clean History Notice */}
      {!data.has_bankruptcy &&
        !data.has_open_judgements &&
        !data.has_foreclosure &&
        !data.has_repossession &&
        !data.has_tax_liens && (
          <div className="rounded-md bg-green-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-green-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-green-700">
                  No derogatory credit history items reported.
                </p>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}

export default CreditHistorySection;
