/**
 * Layout pour les utilisateurs authentifiés
 */
import React from 'react';
import Header from './Header';
import { useAuth } from '../../contexts/AuthContext';

const AuthenticatedLayout = ({ activeTab, setActiveTab, children }) => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    if (window.confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
      await logout();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header avec navigation */}
      <div className="relative">
        <Header activeTab={activeTab} setActiveTab={setActiveTab} />
        
        {/* Menu utilisateur */}
        <div className="absolute top-0 right-0 mt-4 mr-4">
          <div className="flex items-center space-x-4">
            {/* Informations utilisateur */}
            <div className="text-sm text-gray-600">
              Bonjour, <span className="font-medium">{user?.first_name || user?.email}</span>
            </div>
            
            {/* Bouton de déconnexion */}
            <button
              onClick={handleLogout}
              className="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1 rounded-md text-sm font-medium transition-colors duration-200 flex items-center"
              title="Se déconnecter"
            >
              <span className="mr-1">🚪</span>
              Déconnexion
            </button>
          </div>
        </div>
      </div>

      {/* Contenu principal */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <div>
              © 2024 Job Keywords Analyzer - Analysez les tendances du marché de l'emploi
            </div>
            <div className="flex space-x-4">
              <a href="#" className="hover:text-gray-700">API Docs</a>
              <a href="#" className="hover:text-gray-700">Support</a>
              <a href="#" className="hover:text-gray-700">Version 1.0.0</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AuthenticatedLayout;