import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import {
  ApplicationPage,
  ResultsPage,
  LenderListPage,
  LenderDetailPage,
  LenderCreatePage,
} from './pages';
import { Button } from './components/ui';

function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            Lender Matching Platform
          </h1>
        </div>
      </header>
      <main>
        <div className="mx-auto max-w-7xl py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="rounded-lg border-4 border-dashed border-gray-200 p-8 text-center">
              <h2 className="text-xl font-semibold text-gray-700">
                Welcome to the Lender Matching Platform
              </h2>
              <p className="mt-2 text-gray-500">
                Match loan applications with the best lender policies.
              </p>
              <div className="mt-6 flex justify-center gap-4">
                <Link to="/apply">
                  <Button size="lg">Start New Application</Button>
                </Link>
                <Link to="/admin/lenders">
                  <Button size="lg" variant="secondary">
                    Manage Lenders
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/apply" element={<ApplicationPage />} />
        <Route path="/results/:applicationId" element={<ResultsPage />} />
        <Route path="/admin/lenders" element={<LenderListPage />} />
        <Route path="/admin/lenders/new" element={<LenderCreatePage />} />
        <Route path="/admin/lenders/:lenderId" element={<LenderDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
