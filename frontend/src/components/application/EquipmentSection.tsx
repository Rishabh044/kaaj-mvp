/**
 * Equipment information form section.
 * Collects details about the equipment being financed.
 */

import { Input, Select } from '../ui';
import type { EquipmentInfo, EquipmentCategory } from '../../types';
import { EQUIPMENT_CATEGORIES, EQUIPMENT_CONDITIONS } from '../../types';

interface EquipmentSectionProps {
  data: Partial<EquipmentInfo>;
  onChange: (data: Partial<EquipmentInfo>) => void;
  errors?: Record<string, string>;
}

const categoryOptions = EQUIPMENT_CATEGORIES.map((c) => ({
  value: c.value,
  label: c.label,
}));

const conditionOptions = EQUIPMENT_CONDITIONS.map((c) => ({
  value: c.value,
  label: c.label,
}));

const currentYear = new Date().getFullYear();

export function EquipmentSection({
  data,
  onChange,
  errors = {},
}: EquipmentSectionProps) {
  const handleChange = (field: keyof EquipmentInfo, value: unknown) => {
    onChange({ ...data, [field]: value });
  };

  const isTrucking = data.category === 'class_8_truck' || data.category === 'trailer';
  const isConstruction = data.category === 'construction';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900">Equipment Information</h2>
        <p className="mt-1 text-sm text-gray-500">
          Enter details about the equipment to be financed.
        </p>
      </div>

      {/* Basic Equipment Info */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <Select
          label="Equipment Category"
          options={categoryOptions}
          value={data.category ?? ''}
          onChange={(e) => handleChange('category', e.target.value as EquipmentCategory)}
          error={errors.category}
          placeholder="Select category..."
          required
          data-testid="equipment-category"
        />

        <Input
          label="Equipment Type"
          type="text"
          value={data.type ?? ''}
          onChange={(e) => handleChange('type', e.target.value || undefined)}
          error={errors.type}
          helperText="e.g., Freightliner Cascadia, CAT 320"
        />

        <Input
          label="Year"
          type="number"
          min={1980}
          max={currentYear + 1}
          value={data.year ?? currentYear}
          onChange={(e) => handleChange('year', parseInt(e.target.value) || currentYear)}
          error={errors.year}
          required
          data-testid="equipment-year"
        />

        <Select
          label="Condition"
          options={conditionOptions}
          value={data.condition ?? 'used'}
          onChange={(e) => handleChange('condition', e.target.value)}
          error={errors.condition}
          data-testid="equipment-condition"
        />
      </div>

      {/* Trucking-specific: Mileage */}
      {isTrucking && (
        <div className="pt-4 border-t border-gray-200">
          <Input
            label="Mileage"
            type="number"
            min={0}
            value={data.mileage ?? ''}
            onChange={(e) =>
              handleChange('mileage', e.target.value ? parseInt(e.target.value) : undefined)
            }
            error={errors.mileage}
            helperText="Current odometer reading"
            data-testid="equipment-mileage"
          />
        </div>
      )}

      {/* Construction-specific: Hours */}
      {isConstruction && (
        <div className="pt-4 border-t border-gray-200">
          <Input
            label="Hours"
            type="number"
            min={0}
            value={data.hours ?? ''}
            onChange={(e) =>
              handleChange('hours', e.target.value ? parseInt(e.target.value) : undefined)
            }
            error={errors.hours}
            helperText="Current hour meter reading"
            data-testid="equipment-hours"
          />
        </div>
      )}

      {/* Equipment Age Info */}
      {data.year && (
        <div className="rounded-md bg-blue-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-blue-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                Equipment age: <strong>{currentYear - data.year} years</strong>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default EquipmentSection;
