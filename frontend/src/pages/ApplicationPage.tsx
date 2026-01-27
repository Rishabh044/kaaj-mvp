/**
 * Application form page.
 * Contains the multi-step loan application form.
 */

import { Link } from 'react-router-dom';
import { ApplicationForm } from '../components/application';

export function ApplicationPage() {
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
                New Loan Application
              </h1>
            </div>
          </div>
        </div>
      </header>

      <main className="py-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <ApplicationForm />
        </div>
      </main>
    </div>
  );
}

export default ApplicationPage;
