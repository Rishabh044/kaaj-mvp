/**
 * Lender detail page for viewing and editing.
 */

import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Badge } from '../../components/ui';
import { ProgramCard } from '../../components/admin';
import { getLender, updateLender, deleteLender, toggleLenderStatus } from '../../api';
import type { LenderDetail, LenderUpdate } from '../../types';

export function LenderDetailPage() {
  const { lenderId } = useParams<{ lenderId: string }>();
  const navigate = useNavigate();
  const [lender, setLender] = useState<LenderDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<LenderUpdate>({});

  useEffect(() => {
    if (lenderId) {
      fetchLender();
    }
  }, [lenderId]);

  const fetchLender = async () => {
    if (!lenderId) return;

    try {
      setIsLoading(true);
      const data = await getLender(lenderId);
      setLender(data);
      setEditData({
        name: data.name,
        description: data.description || undefined,
        contact_email: data.contact_email || undefined,
        contact_phone: data.contact_phone || undefined,
      });
      setError(null);
    } catch (err) {
      setError('Failed to load lender details.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!lenderId) return;

    try {
      await updateLender(lenderId, editData);
      setIsEditing(false);
      fetchLender();
    } catch (err) {
      setError('Failed to save changes.');
    }
  };

  const handleDelete = async () => {
    if (!lenderId) return;
    if (!confirm('Are you sure you want to delete this lender?')) return;

    try {
      await deleteLender(lenderId);
      navigate('/admin/lenders');
    } catch (err) {
      setError('Failed to delete lender.');
    }
  };

  const handleToggleStatus = async () => {
    if (!lenderId) return;

    try {
      await toggleLenderStatus(lenderId);
      fetchLender();
    } catch (err) {
      setError('Failed to toggle status.');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">Loading lender details...</p>
        </div>
      </div>
    );
  }

  if (!lender) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Lender Not Found</h1>
          <Link
            to="/admin/lenders"
            className="mt-4 inline-block text-primary-600 hover:text-primary-700"
          >
            Back to Lenders
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <Link
                to="/admin/lenders"
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                &larr; Back to Lenders
              </Link>
              <div className="mt-2 flex items-center space-x-3">
                <h1 className="text-2xl font-bold tracking-tight text-gray-900">
                  {lender.name}
                </h1>
                <Badge variant={lender.is_active ? 'success' : 'default'}>
                  {lender.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                ID: {lender.id} | Version: {lender.version}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="secondary" onClick={handleToggleStatus}>
                {lender.is_active ? 'Deactivate' : 'Activate'}
              </Button>
              {isEditing ? (
                <>
                  <Button variant="secondary" onClick={() => setIsEditing(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleSave}>Save</Button>
                </>
              ) : (
                <>
                  <Button variant="secondary" onClick={() => setIsEditing(true)}>
                    Edit
                  </Button>
                  <Button variant="danger" onClick={handleDelete}>
                    Delete
                  </Button>
                </>
              )}
            </div>
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

          {/* Lender Info */}
          <Card padding="lg" className="mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Lender Information
            </h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Description</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {lender.description || 'No description'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Contact Email</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {lender.contact_email || 'N/A'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Contact Phone</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {lender.contact_phone || 'N/A'}
                </dd>
              </div>
            </dl>
          </Card>

          {/* Programs */}
          <div className="mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Programs ({lender.programs.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {lender.programs.map((program) => (
                <ProgramCard key={program.id} program={program} />
              ))}
            </div>
          </div>

          {/* Restrictions */}
          {lender.restrictions && (
            <Card padding="lg">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Global Restrictions
              </h2>
              <pre className="text-xs bg-gray-50 p-4 rounded overflow-x-auto">
                {JSON.stringify(lender.restrictions, null, 2)}
              </pre>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}

export default LenderDetailPage;
