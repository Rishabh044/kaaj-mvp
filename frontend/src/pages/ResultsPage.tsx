/**
 * Results display page.
 * Shows matching results for an application.
 */

import { Link, useParams } from 'react-router-dom';
import { MatchingResults } from '../components/results';

export function ResultsPage() {
  const { applicationId } = useParams<{ applicationId: string }>();

  if (!applicationId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Application Not Found
          </h1>
          <p className="mt-2 text-gray-500">
            No application ID was provided.
          </p>
          <Link
            to="/apply"
            className="mt-4 inline-block text-primary-600 hover:text-primary-700"
          >
            Start New Application
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
              <Link to="/" className="text-sm text-gray-500 hover:text-gray-700">
                &larr; Back to Home
              </Link>
              <h1 className="mt-2 text-2xl font-bold tracking-tight text-gray-900">
                Matching Results
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Application ID: {applicationId}
              </p>
            </div>
            <Link
              to="/apply"
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              New Application
            </Link>
          </div>
        </div>
      </header>

      <main className="py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <MatchingResults applicationId={applicationId} />
        </div>
      </main>
    </div>
  );
}

export default ResultsPage;
