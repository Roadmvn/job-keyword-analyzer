/**
 * Composant Dashboard - Vue d'ensemble des statistiques
 */
import React from 'react';
import StatsCard from './StatsCard';
import TopKeywords from './TopKeywords';
import RecentJobs from './RecentJobs';

const Dashboard = ({ stats, keywords, jobs, loading, onPopulateTestData }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Chargement des données...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* En-tête avec actions */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-600">Vue d'ensemble de vos données d'emploi</p>
        </div>
        <button
          onClick={onPopulateTestData}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors flex items-center"
        >
          <span className="mr-2">🧪</span>
          Ajouter des données de test
        </button>
      </div>

      {/* Cartes de statistiques */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Offres"
          value={stats?.total_jobs}
          icon="💼"
          color="blue"
          trend="up"
          trendValue="+12%"
        />
        <StatsCard
          title="Mots-clés"
          value={stats?.total_keywords}
          icon="🏷️"
          color="green"
          trend="up"
          trendValue="+8%"
        />
        <StatsCard
          title="Nouvelles offres"
          value={stats?.new_jobs_today}
          icon="✨"
          color="purple"
          trend="up"
          trendValue="+24%"
        />
        <StatsCard
          title="Sources actives"
          value={stats?.active_sources}
          icon="🌐"
          color="orange"
        />
      </div>

      {/* Contenu principal */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top des mots-clés */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              🏆 Top Mots-clés
            </h3>
            <p className="text-sm text-gray-600">Les compétences les plus demandées</p>
          </div>
          <TopKeywords keywords={keywords} />
        </div>

        {/* Offres récentes */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              📋 Offres Récentes
            </h3>
            <p className="text-sm text-gray-600">Dernières offres scrapées</p>
          </div>
          <RecentJobs jobs={jobs} />
        </div>
      </div>

      {/* État du système */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          ⚡ État du Système
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Base de données</span>
            <span className="text-sm font-medium text-green-600">Opérationnelle</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Elasticsearch</span>
            <span className="text-sm font-medium text-green-600">Connecté</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Redis</span>
            <span className="text-sm font-medium text-green-600">Actif</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;