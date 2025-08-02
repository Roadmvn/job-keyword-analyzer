/**
 * Composant SearchForm - Formulaire de recherche d'offres
 */
import React from 'react';

const SearchForm = ({ 
  searchQuery, 
  setSearchQuery, 
  onSearch, 
  searchLoading,
  suggestions = [],
  correctedQuery 
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onSearch();
    }
  };

  const applySuggestion = (suggestion) => {
    setSearchQuery(suggestion);
    onSearch(suggestion);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          🔍 Recherche d'Offres
        </h3>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Champ de recherche principal */}
        <div className="flex space-x-3">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Rechercher des offres d'emploi... (ex: développeur Python)"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              disabled={searchLoading}
            />
          </div>
          
          <button
            type="submit"
            disabled={searchLoading || !searchQuery.trim()}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
          >
            {searchLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                Recherche...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Rechercher
              </>
            )}
          </button>
        </div>

        {/* Requête corrigée */}
        {correctedQuery && correctedQuery !== searchQuery && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              🔧 Recherche corrigée : 
              <button
                onClick={() => applySuggestion(correctedQuery)}
                className="ml-1 font-medium underline hover:no-underline"
              >
                "{correctedQuery}"
              </button>
            </p>
          </div>
        )}

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">💡 Suggestions :</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.slice(0, 6).map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => applySuggestion(suggestion)}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Exemples de recherche */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">🎯 Exemples de recherche :</p>
          <div className="flex flex-wrap gap-2">
            {[
              'développeur Python',
              'data scientist',
              'React JavaScript',
              'DevOps Docker',
              'UI/UX designer'
            ].map((example, index) => (
              <button
                key={index}
                onClick={() => applySuggestion(example)}
                className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
};

export default SearchForm;