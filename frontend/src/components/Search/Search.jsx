/**
 * Composant Search - Page de recherche complète
 */
import React from 'react';
import SearchForm from './SearchForm';
import SearchResults from './SearchResults';

const Search = ({
  searchQuery,
  setSearchQuery,
  searchResults,
  searchLoading,
  suggestions,
  correctedQuery,
  onSearch,
  onAnalyzeJob
}) => {
  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Recherche d'Offres</h2>
        <p className="text-gray-600">
          Trouvez les offres d'emploi qui correspondent à vos compétences
        </p>
      </div>

      {/* Formulaire de recherche */}
      <SearchForm
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onSearch={onSearch}
        searchLoading={searchLoading}
        suggestions={suggestions}
        correctedQuery={correctedQuery}
      />

      {/* Résultats */}
      <SearchResults
        results={searchResults}
        loading={searchLoading}
        query={searchQuery}
        onAnalyzeJob={onAnalyzeJob}
      />
    </div>
  );
};

export default Search;