/**
 * Composant de route protégée - Vérifie l'authentification
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  // Affichage de chargement pendant la vérification
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Vérification de l'authentification...</p>
        </div>
      </div>
    );
  }

  // Si non authentifié, retourner null (l'App gérera l'affichage du login)
  if (!isAuthenticated) {
    return null;
  }

  // Si authentifié, afficher le contenu protégé
  return children;
};

export default ProtectedRoute;