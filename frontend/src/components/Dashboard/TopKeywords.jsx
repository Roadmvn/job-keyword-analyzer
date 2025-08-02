/**
 * Composant TopKeywords - Liste des mots-clés les plus fréquents
 */
import React from 'react';

const TopKeywords = ({ keywords = [] }) => {
  if (!keywords.length) {
    return (
      <div className="p-6 text-center text-gray-500">
        <div className="text-4xl mb-2">📝</div>
        <p>Aucun mot-clé disponible</p>
        <p className="text-sm">Lancez un scraping pour voir les données</p>
      </div>
    );
  }

  // Couleurs pour les badges de catégories
  const categoryColors = {
    'langage': 'bg-blue-100 text-blue-800',
    'framework': 'bg-green-100 text-green-800',
    'outil': 'bg-purple-100 text-purple-800',
    'méthode': 'bg-orange-100 text-orange-800',
    'base_donnees': 'bg-red-100 text-red-800',
    'default': 'bg-gray-100 text-gray-800'
  };

  const getMaxFrequency = () => {
    return Math.max(...keywords.map(k => k.frequency || 0));
  };

  const maxFreq = getMaxFrequency();

  return (
    <div className="p-6 space-y-4">
      {keywords.slice(0, 10).map((keyword, index) => (
        <div key={keyword.id || index} className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            {/* Rang */}
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
              ${index < 3 
                ? 'bg-yellow-100 text-yellow-800' 
                : 'bg-gray-100 text-gray-600'
              }
            `}>
              {index + 1}
            </div>

            {/* Nom du mot-clé */}
            <div className="flex-1">
              <p className="font-medium text-gray-900">{keyword.name}</p>
              {keyword.category && (
                <span className={`
                  inline-block px-2 py-1 text-xs rounded-full mt-1
                  ${categoryColors[keyword.category] || categoryColors.default}
                `}>
                  {keyword.category}
                </span>
              )}
            </div>

            {/* Barre de progression */}
            <div className="w-24 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${(keyword.frequency / maxFreq) * 100}%`
                }}
              ></div>
            </div>

            {/* Fréquence */}
            <div className="text-right">
              <p className="text-sm font-semibold text-gray-900">
                {keyword.frequency || 0}
              </p>
              <p className="text-xs text-gray-500">
                {keyword.confidence ? `${(keyword.confidence * 100).toFixed(0)}%` : '-'}
              </p>
            </div>
          </div>
        </div>
      ))}

      {keywords.length > 10 && (
        <div className="pt-4 border-t border-gray-200 text-center">
          <button className="text-blue-500 hover:text-blue-600 text-sm font-medium">
            Voir tous les {keywords.length} mots-clés →
          </button>
        </div>
      )}
    </div>
  );
};

export default TopKeywords;