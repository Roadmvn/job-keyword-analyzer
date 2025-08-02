/**
 * Composant SearchResults - Affichage des résultats de recherche
 */
import React from 'react';

const SearchResults = ({ results = [], loading, query, onAnalyzeJob }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mr-3"></div>
          <span className="text-gray-600">Recherche en cours...</span>
        </div>
      </div>
    );
  }

  if (!results.length && query) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <div className="text-6xl mb-4">🔍</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Aucun résultat trouvé
        </h3>
        <p className="text-gray-600">
          Essayez avec d'autres mots-clés ou utilisez les suggestions ci-dessus.
        </p>
      </div>
    );
  }

  if (!query) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <div className="text-6xl mb-4">💼</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Rechercher des offres d'emploi
        </h3>
        <p className="text-gray-600">
          Entrez des mots-clés dans le champ de recherche pour commencer.
        </p>
      </div>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleDateString('fr-FR');
    } catch (e) {
      return dateString;
    }
  };

  const getSourceIcon = (source) => {
    const icons = {
      'indeed': '🔍',
      'linkedin': '💼',
      'pole-emploi': '🇫🇷',
      'default': '🌐'
    };
    return icons[source] || icons.default;
  };

  const highlightText = (text, query) => {
    if (!text || !query) return text;
    
    const words = query.toLowerCase().split(' ').filter(w => w.length > 2);
    let highlightedText = text;
    
    words.forEach(word => {
      const regex = new RegExp(`(${word})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
    });
    
    return { __html: highlightedText };
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* En-tête des résultats */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              📋 Résultats de recherche
            </h3>
            <p className="text-sm text-gray-600">
              {results.length} offre{results.length > 1 ? 's' : ''} trouvée{results.length > 1 ? 's' : ''} pour "{query}"
            </p>
          </div>
          
          {/* Options d'affichage */}
          <div className="flex items-center space-x-2">
            <button className="p-2 text-gray-400 hover:text-gray-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Liste des résultats */}
      <div className="divide-y divide-gray-200">
        {results.map((job, index) => (
          <div key={job.id || index} className="p-6 hover:bg-gray-50 transition-colors">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                {/* Titre et entreprise */}
                <div className="flex items-start space-x-3">
                  <div className="flex-1">
                    <h4 
                      className="text-lg font-medium text-gray-900 mb-1"
                      dangerouslySetInnerHTML={highlightText(job.title, query)}
                    />
                    <p className="text-blue-600 font-medium">
                      {job.company}
                    </p>
                  </div>
                  
                  {/* Source */}
                  <span className="inline-flex items-center px-3 py-1 text-sm font-medium bg-gray-100 text-gray-800 rounded-full">
                    {getSourceIcon(job.source)} {job.source}
                  </span>
                </div>

                {/* Détails */}
                <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-gray-600">
                  {job.location && (
                    <span className="flex items-center">
                      📍 {job.location}
                    </span>
                  )}
                  {job.contract_type && (
                    <span className="flex items-center">
                      📄 {job.contract_type}
                    </span>
                  )}
                  {job.salary_min && job.salary_max && (
                    <span className="flex items-center">
                      💰 {job.salary_min}k - {job.salary_max}k €
                    </span>
                  )}
                  {job.remote_work && (
                    <span className="flex items-center text-green-600">
                      🏠 Télétravail
                    </span>
                  )}
                </div>

                {/* Description (extrait) */}
                {job.description && (
                  <div className="mt-3">
                    <p 
                      className="text-sm text-gray-700 line-clamp-3"
                      dangerouslySetInnerHTML={highlightText(
                        job.description.substring(0, 300) + (job.description.length > 300 ? '...' : ''),
                        query
                      )}
                    />
                  </div>
                )}

                {/* Métadonnées */}
                <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
                  <span>
                    Publié le {formatDate(job.posted_date)} • Scrapé le {formatDate(job.scraped_at)}
                  </span>
                  {job.score && (
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                      Score: {(job.score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="ml-6 flex flex-col space-y-2">
                {job.url && (
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    Voir l'offre
                  </a>
                )}
                
                <button 
                  onClick={() => onAnalyzeJob && onAnalyzeJob(job.id)}
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-green-600 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Analyser
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination (si nécessaire) */}
      {results.length >= 20 && (
        <div className="p-6 border-t border-gray-200 flex justify-center">
          <button className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
            Charger plus de résultats
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchResults;