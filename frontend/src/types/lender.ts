/**
 * Types for lender data and policies.
 */

/**
 * Lender summary for list views.
 */
export interface LenderSummary {
  id: string;
  name: string;
  version: number;
  program_count: number;
  is_active: boolean;
}

/**
 * Program summary information.
 */
export interface ProgramSummary {
  id: string;
  name: string;
  is_app_only: boolean;
  min_amount: number | null;
  max_amount: number | null;
}

/**
 * Detailed criteria configuration.
 */
export interface CriteriaDetail {
  credit_score?: Record<string, unknown>;
  business?: Record<string, unknown>;
  credit_history?: Record<string, unknown>;
  equipment?: Record<string, unknown>;
  geographic?: Record<string, unknown>;
  industry?: Record<string, unknown>;
  transaction?: Record<string, unknown>;
}

/**
 * Detailed program information.
 */
export interface ProgramDetail {
  id: string;
  name: string;
  description: string | null;
  is_app_only: boolean;
  min_amount: number | null;
  max_amount: number | null;
  max_term_months: number | null;
  criteria: CriteriaDetail | null;
}

/**
 * Restrictions detail.
 */
export interface RestrictionsDetail {
  geographic?: Record<string, unknown>;
  industry?: Record<string, unknown>;
  transaction?: Record<string, unknown>;
  equipment?: Record<string, unknown>;
}

/**
 * Detailed lender information with full policy.
 */
export interface LenderDetail {
  id: string;
  name: string;
  version: number;
  description: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  programs: ProgramDetail[];
  restrictions: RestrictionsDetail | null;
  is_active: boolean;
}

/**
 * Input for creating a new lender.
 */
export interface LenderCreate {
  id: string;
  name: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
}

/**
 * Input for updating a lender.
 */
export interface LenderUpdate {
  name?: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active?: boolean;
}
