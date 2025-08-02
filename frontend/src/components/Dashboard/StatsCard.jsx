/**
 * Composant StatsCard - Affiche une carte de statistique
 */
import React from 'react';

const StatsCard = ({ title, value, icon, trend, trendValue, color = 'blue' }) => {
  const colorClasses = {
    blue: 'bg-blue-500 text-blue-600 bg-blue-50',
    green: 'bg-green-500 text-green-600 bg-green-50',
    purple: 'bg-purple-500 text-purple-600 bg-purple-50',
    orange: 'bg-orange-500 text-orange-600 bg-orange-50',
    red: 'bg-red-500 text-red-600 bg-red-50'
  };

  const [iconBg, textColor, cardBg] = colorClasses[color].split(' ');

  return (
    <div className={`${cardBg} rounded-lg p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow`}>
      <div className="flex items-center">
        <div className={`${iconBg} p-3 rounded-lg`}>
          <span className="text-2xl text-white">{icon}</span>
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">
            {typeof value === 'number' ? value.toLocaleString() : value || '0'}
          </p>
          {trend && trendValue && (
            <div className="flex items-center mt-1">
              <span className={`
                text-xs font-medium
                ${trend === 'up' ? 'text-green-600' : 'text-red-600'}
              `}>
                {trend === 'up' ? '↗' : '↘'} {trendValue}
              </span>
              <span className="text-xs text-gray-500 ml-1">vs hier</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatsCard;