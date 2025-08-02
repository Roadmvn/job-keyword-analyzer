/**
 * Composant RecentJobs - Liste des offres d'emploi récentes
 */
import React from 'react';

const RecentJobs = ({ jobs = [] }) => {
  if (!jobs.length) {
    return (
      <div className="p-6 text-center text-gray-500">
        <div className="text-4xl mb-2">💼</div>
        <p>Aucune offre disponible</p>
        <p className="text-sm">Lancez un scraping pour voir les offres</p>
      </div>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
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

  const getSourceColor = (source) => {
    const colors = {
      'indeed': 'bg-blue-100 text-blue-800',
      'linkedin': 'bg-blue-600 text-white',
      'pole-emploi': 'bg-red-100 text-red-800',
      'default': 'bg-gray-100 text-gray-800'
    };
    return colors[source] || colors.default;
  };

  return (
    <div className="divide-y divide-gray-200">
      {jobs.slice(0, 8).map((job, index) => (
        <div key={job.id || index} className="p-4 hover:bg-gray-50 transition-colors">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              {/* Titre et entreprise */}
              <div className="flex items-start space-x-3">
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {job.title || 'Titre non disponible'}
                  </h4>
                  <p className="text-sm text-gray-600 truncate">
                    {job.company || 'Entreprise non spécifiée'}
                  </p>
                </div>
                
                {/* Source */}
                <span className={`
                  inline-flex items-center px-2 py-1 text-xs font-medium rounded-full
                  ${getSourceColor(job.source)}
                `}>
                  {getSourceIcon(job.source)} {job.source}
                </span>
              </div>

              {/* Localisation et détails */}
              <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
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
              </div>

              {/* Date de scraping */}
              <div className="mt-2 text-xs text-gray-400">
                Scrapé le {formatDate(job.scraped_at || job.created_at)}
              </div>
            </div>

            {/* Actions */}
            <div className="ml-4 flex items-center space-x-2">
              {job.url && (
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-blue-500 transition-colors"
                  title="Voir l'offre"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
              
              <button 
                className="text-gray-400 hover:text-green-500 transition-colors"
                title="Analyser les mots-clés"
                onClick={() => {
                  // TODO: Implémenter l'analyse
                  console.log('Analyser job:', job.id);
                }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      ))}

      {jobs.length > 8 && (
        <div className="p-4 bg-gray-50 text-center">
          <button className="text-blue-500 hover:text-blue-600 text-sm font-medium">
            Voir toutes les {jobs.length} offres →
          </button>
        </div>
      )}
    </div>
  );
};

export default RecentJobs;