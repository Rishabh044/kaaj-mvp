/**
 * Loan request information form section.
 * Collects loan amount, term, and transaction details.
 */

import { Input, Select, Toggle } from '../ui';
import type { LoanRequestInfo, TransactionType } from '../../types';
import { TRANSACTION_TYPES } from '../../types';

interface LoanRequestSectionProps {
  data: Partial<LoanRequestInfo>;
  onChange: (data: Partial<LoanRequestInfo>) => void;
  errors?: Record<string, string>;
}

const transactionTypeOptions = TRANSACTION_TYPES.map((t) => ({
  value: t.value,
  label: t.label,
}));

export function LoanRequestSection({
  data,
  onChange,
  errors = {},
}: LoanRequestSectionProps) {
  const handleChange = (field: keyof LoanRequestInfo, value: unknown) => {
    onChange({ ...data, [field]: value });
  };

  // Format amount as currency for display
  const formatCurrency = (value: number | undefined) => {
    if (value === undefined) return '';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value / 100);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900">Loan Request</h2>
        <p className="mt-1 text-sm text-gray-500">
          Enter the financing details for this application.
        </p>
      </div>

      {/* Loan Amount and Term */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <Input
          label="Loan Amount"
          type="number"
          min={1000}
          max={50000000}
          value={data.amount ? data.amount / 100 : ''}
          onChange={(e) => {
            const dollars = parseFloat(e.target.value) || 0;
            handleChange('amount', Math.round(dollars * 100));
          }}
          error={errors.amount}
          helperText="Enter amount in dollars"
          required
          data-testid="loan-amount"
        />

        <Input
          label="Requested Term (Months)"
          type="number"
          min={12}
          max={84}
          value={data.requested_term_months ?? ''}
          onChange={(e) =>
            handleChange(
              'requested_term_months',
              e.target.value ? parseInt(e.target.value) : undefined
            )
          }
          error={errors.requested_term_months}
          helperText="12-84 months (optional)"
        />
      </div>

      {/* Loan Amount Display */}
      {data.amount && data.amount > 0 && (
        <div className="rounded-md bg-blue-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-blue-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                Requested amount: <strong>{formatCurrency(data.amount)}</strong>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Transaction Type */}
      <div className="pt-4 border-t border-gray-200">
        <Select
          label="Transaction Type"
          options={transactionTypeOptions}
          value={data.transaction_type ?? 'purchase'}
          onChange={(e) =>
            handleChange('transaction_type', e.target.value as TransactionType)
          }
          error={errors.transaction_type}
          data-testid="transaction-type"
        />
      </div>

      {/* Private Party and Down Payment */}
      <div className="space-y-4 pt-4 border-t border-gray-200">
        <Toggle
          label="Private Party Sale"
          description="Is this a private party transaction (not from a dealer)?"
          checked={data.is_private_party ?? false}
          onChange={(e) => handleChange('is_private_party', e.target.checked)}
          data-testid="is-private-party"
        />

        <Input
          label="Down Payment Percentage"
          type="number"
          min={0}
          max={100}
          step={0.5}
          value={data.down_payment_percent ?? ''}
          onChange={(e) =>
            handleChange(
              'down_payment_percent',
              e.target.value ? parseFloat(e.target.value) : undefined
            )
          }
          error={errors.down_payment_percent}
          helperText="Percentage of total (optional)"
        />
      </div>

      {/* Summary */}
      {data.amount && data.down_payment_percent && (
        <div className="rounded-md bg-gray-50 p-4">
          <h4 className="text-sm font-medium text-gray-900">Financing Summary</h4>
          <dl className="mt-2 grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Down Payment</dt>
              <dd className="font-medium text-gray-900">
                {formatCurrency(Math.round(data.amount * (data.down_payment_percent / 100)))}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Amount to Finance</dt>
              <dd className="font-medium text-gray-900">
                {formatCurrency(
                  Math.round(data.amount * (1 - data.down_payment_percent / 100))
                )}
              </dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}

export default LoanRequestSection;
