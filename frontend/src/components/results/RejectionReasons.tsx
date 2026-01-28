/**
 * Rejection reasons summary component.
 */

interface RejectionReasonsProps {
  reasons: string[];
}

export function RejectionReasons({ reasons }: RejectionReasonsProps) {
  if (!reasons || reasons.length === 0) {
    return null;
  }

  return (
    <div className="mt-3">
      <h4 className="text-sm font-medium text-red-700">Rejection Reasons:</h4>
      <ul className="mt-1 list-disc list-inside text-sm text-red-600">
        {reasons.map((reason, index) => (
          <li key={index}>{reason}</li>
        ))}
      </ul>
    </div>
  );
}

export default RejectionReasons;
