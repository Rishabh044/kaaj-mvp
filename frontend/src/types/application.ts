/**
 * Types for loan application data and API responses.
 */

import type {
  EquipmentCategory,
  TransactionType,
  EquipmentCondition,
  BankruptcyChapter,
} from './common';

/**
 * Applicant (personal guarantor) information.
 */
export interface ApplicantInfo {
  fico_score: number;
  transunion_score?: number;
  experian_score?: number;
  equifax_score?: number;
  is_homeowner: boolean;
  is_us_citizen: boolean;
  has_cdl: boolean;
  cdl_years?: number;
  industry_experience_years?: number;
}

/**
 * Business information.
 */
export interface BusinessInfo {
  name: string;
  state: string;
  industry_code?: string;
  industry_name?: string;
  years_in_business: number;
  annual_revenue?: number;
  fleet_size?: number;
}

/**
 * Credit history information.
 */
export interface CreditHistoryInfo {
  has_bankruptcy: boolean;
  bankruptcy_discharge_years?: number;
  bankruptcy_chapter?: BankruptcyChapter;
  has_open_judgements: boolean;
  judgement_amount?: number;
  has_foreclosure: boolean;
  has_repossession: boolean;
  has_tax_liens: boolean;
  tax_lien_amount?: number;
}

/**
 * Equipment information.
 */
export interface EquipmentInfo {
  category: EquipmentCategory;
  type?: string;
  year: number;
  mileage?: number;
  hours?: number;
  condition: EquipmentCondition;
}

/**
 * Loan request information.
 */
export interface LoanRequestInfo {
  amount: number;
  requested_term_months?: number;
  down_payment_percent?: number;
  transaction_type: TransactionType;
  is_private_party: boolean;
}

/**
 * Business credit information.
 */
export interface BusinessCreditInfo {
  paynet_score?: number;
  paynet_master_score?: number;
  paydex_score?: number;
}

/**
 * Complete loan application input.
 */
export interface LoanApplicationInput {
  applicant: ApplicantInfo;
  business: BusinessInfo;
  credit_history: CreditHistoryInfo;
  equipment: EquipmentInfo;
  loan_request: LoanRequestInfo;
  business_credit?: BusinessCreditInfo;
}

/**
 * Application submission response.
 */
export interface ApplicationResponse {
  id: string;
  application_number: string;
  status: string;
  workflow_run_id?: string;
  message: string;
}

/**
 * Application status response.
 */
export interface ApplicationStatus {
  application_id: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  workflow_run_id?: string;
  total_evaluated?: number;
  total_eligible?: number;
  best_match?: string;
  processed_at?: string;
}

/**
 * Form state for the multi-step application form.
 */
export interface ApplicationFormState {
  applicant: Partial<ApplicantInfo>;
  business: Partial<BusinessInfo>;
  credit_history: Partial<CreditHistoryInfo>;
  equipment: Partial<EquipmentInfo>;
  loan_request: Partial<LoanRequestInfo>;
  business_credit: Partial<BusinessCreditInfo>;
}

/**
 * Default initial state for the application form.
 */
export const DEFAULT_FORM_STATE: ApplicationFormState = {
  applicant: {
    is_homeowner: false,
    is_us_citizen: true,
    has_cdl: false,
  },
  business: {
    years_in_business: 0,
  },
  credit_history: {
    has_bankruptcy: false,
    has_open_judgements: false,
    has_foreclosure: false,
    has_repossession: false,
    has_tax_liens: false,
  },
  equipment: {
    condition: 'used',
    year: new Date().getFullYear(),
  },
  loan_request: {
    transaction_type: 'purchase',
    is_private_party: false,
  },
  business_credit: {},
};
