/**
 * Types for matching results.
 */

/**
 * Result of a single criterion evaluation.
 */
export interface CriterionResult {
  rule_name: string;
  passed: boolean;
  required_value: string;
  actual_value: string;
  message: string;
}

/**
 * A single lender match result.
 */
export interface LenderMatch {
  lender_id: string;
  lender_name: string;
  is_eligible: boolean;
  fit_score: number;
  rank: number | null;
  best_program: string | null;
  rejection_reasons: string[];
  criteria_results: CriterionResult[];
}

/**
 * Complete matching results for an application.
 */
export interface MatchingResults {
  application_id: string;
  total_evaluated: number;
  total_eligible: number;
  best_match: LenderMatch | null;
  matches: LenderMatch[];
}
