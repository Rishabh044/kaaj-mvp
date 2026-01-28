/**
 * Create new lender page.
 */

import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { LenderForm } from '../../components/admin';
import { createLender } from '../../api';
import type { LenderCreate, LenderUpdate } from '../../types';

export function LenderCreatePage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: LenderCreate | LenderUpdate) => {
    try {
      setError(null);
      // In create mode, data will always be LenderCreate
      await createLender(data as LenderCreate);
      navigate('/admin/lenders');
    } catch (err) {
      if (err && typeof err === 'object' && 'message' in err) {
        setError((err as { message: string }).message);
      } else {
        setError('Failed to create lender. Please try again.');
      }
      throw err; // Re-throw to keep form in submitting state
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div>
            <Link
              to="/admin/lenders"
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              &larr; Back to Lenders
            </Link>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-gray-900">
              Add New Lender
            </h1>
          </div>
        </div>
      </header>

      <main className="py-10">
        <div className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8">
          {error && (
            <div className="mb-6 rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <LenderForm
            onSubmit={handleSubmit}
            onCancel={() => navigate('/admin/lenders')}
          />
        </div>
      </main>
    </div>
  );
}

export default LenderCreatePage;
