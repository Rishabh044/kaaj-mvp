/**
 * Lender list table component.
 */

import { useNavigate } from 'react-router-dom';
import { Badge, Button } from '../ui';
import type { LenderSummary } from '../../types';

interface LenderTableProps {
  lenders: LenderSummary[];
  onToggleStatus?: (lenderId: string) => void;
}

export function LenderTable({ lenders, onToggleStatus }: LenderTableProps) {
  const navigate = useNavigate();

  if (lenders.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No lenders configured yet.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Lender
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Programs
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Version
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {lenders.map((lender) => (
            <tr
              key={lender.id}
              className="hover:bg-gray-50 cursor-pointer"
              onClick={() => navigate(`/admin/lenders/${lender.id}`)}
            >
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {lender.name}
                  </div>
                  <div className="text-sm text-gray-500">{lender.id}</div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="text-sm text-gray-900">
                  {lender.program_count}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="text-sm text-gray-500">v{lender.version}</span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <Badge variant={lender.is_active ? 'success' : 'default'}>
                  {lender.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleStatus?.(lender.id);
                  }}
                >
                  {lender.is_active ? 'Deactivate' : 'Activate'}
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default LenderTable;
