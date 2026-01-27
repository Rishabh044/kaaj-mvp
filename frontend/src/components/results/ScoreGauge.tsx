/**
 * Visual score display component.
 */

interface ScoreGaugeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

const sizeStyles = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-12 w-12 text-sm',
  lg: 'h-16 w-16 text-base',
};

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600 bg-green-100';
  if (score >= 60) return 'text-blue-600 bg-blue-100';
  if (score >= 40) return 'text-yellow-600 bg-yellow-100';
  if (score > 0) return 'text-orange-600 bg-orange-100';
  return 'text-gray-400 bg-gray-100';
}

export function ScoreGauge({ score, size = 'md' }: ScoreGaugeProps) {
  const colorClasses = getScoreColor(score);
  // Round to whole number for display
  const displayScore = Math.round(score);

  return (
    <div
      className={`
        ${sizeStyles[size]}
        ${colorClasses}
        rounded-full flex items-center justify-center font-semibold flex-shrink-0
      `}
      title={`Fit Score: ${score.toFixed(1)}`}
    >
      {displayScore}
    </div>
  );
}

export default ScoreGauge;
