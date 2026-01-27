/**
 * Business information form section.
 * Collects business details like name, state, and industry.
 */

import { Input, Select } from '../ui';
import type { BusinessInfo } from '../../types';
import { US_STATES } from '../../types';

interface BusinessSectionProps {
  data: Partial<BusinessInfo>;
  onChange: (data: Partial<BusinessInfo>) => void;
  errors?: Record<string, string>;
}

const stateOptions = US_STATES.map((s) => ({ value: s.code, label: s.name }));

export function BusinessSection({
  data,
  onChange,
  errors = {},
}: BusinessSectionProps) {
  const handleChange = (field: keyof BusinessInfo, value: unknown) => {
    onChange({ ...data, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900">Business Information</h2>
        <p className="mt-1 text-sm text-gray-500">
          Enter information about the business applying for financing.
        </p>
      </div>

      {/* Basic Business Info */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Input
            label="Business Name"
            type="text"
            value={data.name ?? ''}
            onChange={(e) => handleChange('name', e.target.value)}
            error={errors.name}
            required
            data-testid="business-name"
          />
        </div>

        <Select
          label="State"
          options={stateOptions}
          value={data.state ?? ''}
          onChange={(e) => handleChange('state', e.target.value)}
          error={errors.state}
          placeholder="Select state..."
          required
          data-testid="business-state"
        />

        <Input
          label="Years in Business"
          type="number"
          min={0}
          step={0.5}
          value={data.years_in_business ?? ''}
          onChange={(e) =>
            handleChange('years_in_business', parseFloat(e.target.value) || 0)
          }
          error={errors.years_in_business}
          helperText="Can include partial years (e.g., 2.5)"
          required
          data-testid="years-in-business"
        />
      </div>

      {/* Industry Information */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 pt-4 border-t border-gray-200">
        <Input
          label="Industry Code"
          type="text"
          value={data.industry_code ?? ''}
          onChange={(e) => handleChange('industry_code', e.target.value || undefined)}
          error={errors.industry_code}
          helperText="NAICS or SIC code (optional)"
        />

        <Input
          label="Industry Name"
          type="text"
          value={data.industry_name ?? ''}
          onChange={(e) => handleChange('industry_name', e.target.value || undefined)}
          error={errors.industry_name}
          helperText="e.g., Trucking, Construction"
        />
      </div>

      {/* Financial Information */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 pt-4 border-t border-gray-200">
        <Input
          label="Annual Revenue"
          type="number"
          min={0}
          value={data.annual_revenue ?? ''}
          onChange={(e) =>
            handleChange('annual_revenue', e.target.value ? parseInt(e.target.value) : undefined)
          }
          error={errors.annual_revenue}
          helperText="Annual revenue in dollars (optional)"
        />

        <Input
          label="Fleet Size"
          type="number"
          min={0}
          value={data.fleet_size ?? ''}
          onChange={(e) =>
            handleChange('fleet_size', e.target.value ? parseInt(e.target.value) : undefined)
          }
          error={errors.fleet_size}
          helperText="Number of vehicles in fleet (optional)"
        />
      </div>
    </div>
  );
}

export default BusinessSection;
