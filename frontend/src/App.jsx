/**
 * Application principale Job Keywords Analyzer - Avec Authentification
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Contexte d'authentification
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Composants d'authentification
import AuthContainer from './components/Auth/AuthContainer';
import ProtectedRoute from './components/Auth/ProtectedRoute';

// Layout authentifié
import AuthenticatedLayout from './components/Layout/AuthenticatedLayout';

// Composants métier
import Dashboard from './components/Dashboard/Dashboard';
import Search from './components/Search/Search';

// Configuration API
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Composant principal de l'application (à l'intérieur du AuthProvider)
function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  
  // États globaux
  const [stats, setStats] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // États pour la recherche
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [correctedQuery, setCorrectedQuery] = useState('');
  
  // États pour l'analyse
  const [analysisResults, setAnalysisResults] = useState(null);
  const [userSkills, setUserSkills] = useState('');
  const [cvSuggestions, setCvSuggestions] = useState(null);

  // États pour le scraping
  const [scrapingJobs, setScrapingJobs] = useState([]);
  const [scrapingLoading, setScrapingLoading] = useState(false);

  // Chargement initial des données (seulement si authentifié)
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      fetchData();
    }
  }, [isAuthenticated, isLoading]);

  /**
   * Récupère les données principales de l'application
   */
  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, jobsRes, keywordsRes] = await Promise.all([
        axios.get(`${API_URL}/api/stats`),
        axios.get(`${API_URL}/api/jobs?limit=5`),
        axios.get(`${API_URL}/api/keywords?limit=10`)
      ]);
      
      setStats(statsRes.data);
      setJobs(jobsRes.data);
      setKeywords(keywordsRes.data);
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      // TODO: Afficher une notification d'erreur utilisateur-friendly
    } finally {
      setLoading(false);
    }
  };

  /**
   * Ajoute des données de test
   */
  const populateTestData = async () => {
    try {
      await axios.post(`${API_URL}/api/test/populate`);
      // TODO: Remplacer par une notification moderne
      alert('✅ Données de test ajoutées!');
      fetchData();
    } catch (error) {
      console.error('Erreur lors de l\'ajout des données de test:', error);
      alert('❌ Erreur lors de l\'ajout des données de test');
    }
  };

  /**
   * Effectue une recherche d'offres d'emploi
   */
  const searchJobs = async (query = searchQuery) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      setSearchLoading(true);
      const response = await axios.get(`${API_URL}/api/search`, {
        params: { q: query, limit: 20 }
      });
      
      setSearchResults(response.data.results || []);
      setCorrectedQuery(response.data.corrected_query);
      setSuggestions(response.data.suggestions || []);
      
      if (response.data.corrected_query !== query) {
        console.log(`🔧 Requête corrigée: "${query}" → "${response.data.corrected_query}"`);
      }
    } catch (error) {
      console.error('Erreur de recherche:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  /**
   * Analyse les mots-clés d'une offre
   */
  const analyzeJobKeywords = async (jobId) => {
    try {
      const response = await axios.post(`${API_URL}/api/analyze/job/${jobId}`);
      setAnalysisResults(response.data);
      alert('✅ Analyse terminée! Consultez l\'onglet Analyse.');
    } catch (error) {
      console.error('Erreur d\'analyse:', error);
      alert('❌ Erreur lors de l\'analyse');
    }
  };

  /**
   * Génère des suggestions pour améliorer le CV
   */
  const getCvSuggestions = async () => {
    if (!userSkills.trim()) {
      alert('Veuillez entrer vos compétences');
      return;
    }

    try {
      const skillsList = userSkills.split(',').map(s => s.trim()).filter(s => s);
      const response = await axios.post(`${API_URL}/api/cv/suggestions`, {
        skills: skillsList
      });
      setCvSuggestions(response.data);
    } catch (error) {
      console.error('Erreur suggestions CV:', error);
      alert('❌ Erreur lors de la génération des suggestions');
    }
  };

  /**
   * Récupère la liste des jobs de scraping
   */
  const fetchScrapingJobs = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/scraper/jobs`);
      setScrapingJobs(response.data);
    } catch (error) {
      console.error('Erreur lors du chargement des jobs de scraping:', error);
    }
  };

  // Chargement initial des jobs de scraping
  useEffect(() => {
    if (activeTab === 'scraping' && isAuthenticated) {
      fetchScrapingJobs();
    }
  }, [activeTab, isAuthenticated]);

  /**
   * Rendu du contenu principal selon l'onglet actif
   */
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard
            stats={stats}
            keywords={keywords}
            jobs={jobs}
            loading={loading}
            onPopulateTestData={populateTestData}
          />
        );

      case 'search':
        return (
          <Search
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            searchResults={searchResults}
            searchLoading={searchLoading}
            suggestions={suggestions}
            correctedQuery={correctedQuery}
            onSearch={searchJobs}
            onAnalyzeJob={analyzeJobKeywords}
          />
        );

      case 'jobs':
        return (
          <div className="text-center p-8">
            <div className="text-6xl mb-4">💼</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Liste des Offres d'Emploi
            </h3>
            <p className="text-gray-600 mb-4">
              Explorez toutes les offres d'emploi collectées et analysées.
            </p>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              {jobs.length > 0 ? (
                <div className="space-y-4">
                  {jobs.map((job) => (
                    <div key={job.id} className="border-b border-gray-200 pb-4 last:border-b-0">
                      <h4 className="font-medium text-gray-900">{job.title}</h4>
                      <p className="text-gray-600">{job.company} - {job.location}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {job.description?.substring(0, 150)}...
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">Aucune offre disponible. Utilisez le bouton "Ajouter données test" pour commencer.</p>
              )}
            </div>
          </div>
        );

      case 'analysis':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🧠 Analyse NLP des Offres</h3>
            {analysisResults ? (
              <div>
                <h4 className="font-medium text-green-600 mb-4">✅ Analyse de l'offre #{analysisResults.job_id}</h4>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h5 className="font-medium text-gray-900 mb-3">🏷️ Mots-clés extraits ({analysisResults.analysis.total_tech_skills})</h5>
                    <div className="max-h-64 overflow-y-auto space-y-2">
                      {analysisResults.analysis.keywords.map((kw, index) => (
                        <div key={index} className="flex justify-between items-center bg-gray-50 p-2 rounded">
                          <span className="font-medium">{kw.keyword}</span>
                          <span className="text-xs text-gray-500">
                            {kw.category} - {(kw.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h5 className="font-medium text-gray-900 mb-3">📊 Résumé par catégorie</h5>
                    <div className="space-y-3">
                      {Object.entries(analysisResults.analysis.categories_summary).map(([category, keywords]) => (
                        <div key={category}>
                          <h6 className="text-sm font-medium text-blue-600 mb-1">{category}</h6>
                          <div className="flex flex-wrap gap-1">
                            {keywords.map((keyword, idx) => (
                              <span key={idx} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">📋 Informations détectées</h5>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Niveau de séniorité :</span>
                      <span className="ml-2">{analysisResults.analysis.seniority_level}</span>
                    </div>
                    <div>
                      <span className="font-medium">Expérience requise :</span>
                      <span className="ml-2">{analysisResults.analysis.experience_required || 'Non spécifiée'}</span>
                    </div>
                    <div>
                      <span className="font-medium">Catégorie principale :</span>
                      <span className="ml-2">{analysisResults.analysis.top_category || 'N/A'}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">🔍</div>
                <p className="text-gray-600 mb-2">Allez dans l'onglet "Recherche" et cliquez sur "🧠 Analyser" sur une offre pour voir l'analyse NLP complète.</p>
                <p className="text-sm text-gray-500">
                  L'analyse extrait automatiquement les mots-clés techniques, détecte le niveau de séniorité, 
                  et identifie les compétences requises.
                </p>
              </div>
            )}
          </div>
        );

      case 'scraping':
        return (
          <div className="text-center p-8">
            <div className="text-6xl mb-4">🕷️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Scraping d'Offres
            </h3>
            <p className="text-gray-600">
              Fonctionnalité de scraping automatique en cours de développement.
            </p>
          </div>
        );

      default:
        return (
          <div className="text-center p-8">
            <div className="text-4xl mb-4">🚧</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Page en construction
            </h3>
            <p className="text-gray-600">
              Cette fonctionnalité sera bientôt disponible.
            </p>
          </div>
        );
    }
  };

  // Si en cours de chargement de l'authentification
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement de l'application...</p>
        </div>
      </div>
    );
  }

  // Si non authentifié, afficher les formulaires de connexion/inscription
  if (!isAuthenticated) {
    return <AuthContainer />;
  }

  // Si authentifié, afficher l'application avec le layout
  return (
    <AuthenticatedLayout activeTab={activeTab} setActiveTab={setActiveTab}>
      <ProtectedRoute>
        {renderContent()}
      </ProtectedRoute>
    </AuthenticatedLayout>
  );
}

// Composant racine avec le provider d'authentification
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;