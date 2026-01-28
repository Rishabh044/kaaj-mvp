/**
 * Lender list page for admin.
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Card } from '../../components/ui';
import { LenderTable } from '../../components/admin';
import { listLenders, toggleLenderStatus } from '../../api';
import type { LenderSummary } from '../../types';

export function LenderListPage() {
  const navigate = useNavigate();
  const [lenders, setLenders] = useState<LenderSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLenders();
  }, []);

  const fetchLenders = async () => {
    try {
      setIsLoading(true);
      const data = await listLenders();
      setLenders(data);
      setError(null);
    } catch (err) {
      setError('Failed to load lenders. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleStatus = async (lenderId: string) => {
    try {
      await toggleLenderStatus(lenderId);
      // Refresh the list
      fetchLenders();
    } catch (err) {
      setError('Failed to toggle lender status.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <Link to="/" className="text-sm text-gray-500 hover:text-gray-700">
                &larr; Back to Home
              </Link>
              <h1 className="mt-2 text-2xl font-bold tracking-tight text-gray-900">
                Lender Policies
              </h1>
            </div>
            <Button onClick={() => navigate('/admin/lenders/new')}>
              Add New Lender
            </Button>
          </div>
        </div>
      </header>

      <main className="py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {error && (
            <div className="mb-6 rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent"></div>
              <p className="mt-4 text-gray-600">Loading lenders...</p>
            </div>
          ) : (
            <Card padding="none">
              <LenderTable
                lenders={lenders}
                onToggleStatus={handleToggleStatus}
              />
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}

export default LenderListPage;
