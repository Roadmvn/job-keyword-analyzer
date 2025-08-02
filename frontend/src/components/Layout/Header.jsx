/**
 * Composant Header - Navigation principale de l'application
 */
import React from 'react';

const Header = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'search', label: '🔍 Recherche', icon: '🔍' },
    { id: 'jobs', label: '💼 Offres', icon: '💼' },
    { id: 'analysis', label: '📈 Analyse', icon: '📈' },
    { id: 'scraping', label: '🕷️ Scraping', icon: '🕷️' }
  ];

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo et titre */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                🚀 Job Keywords Analyzer
              </h1>
              <span className="ml-2 text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                v1.0.0
              </span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex space-x-8">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`
                  inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors duration-200
                  ${activeTab === item.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span className="mr-2">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </nav>

          {/* Actions */}
          <div className="flex items-center space-x-4">
            {/* Indicateur de statut */}
            <div className="flex items-center text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
              En ligne
            </div>

            {/* Bouton de rafraîchissement */}
            <button 
              onClick={() => window.location.reload()}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="Actualiser"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;