/**
 * Contexte d'authentification pour gérer l'état global de l'utilisateur
 */
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext();

// Actions pour le reducer
const AUTH_ACTIONS = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  SET_USER: 'SET_USER',
  CLEAR_ERROR: 'CLEAR_ERROR'
};

// État initial
const initialState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true,
  error: null
};

// Reducer pour gérer les états d'authentification
function authReducer(state, action) {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
      return {
        ...state,
        isLoading: true,
        error: null
      };
    
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null
      };
    
    case AUTH_ACTIONS.LOGIN_FAILURE:
      return {
        ...state,
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload
      };
    
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      };
    
    case AUTH_ACTIONS.SET_USER:
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isAuthenticated: true,
        isLoading: false
      };
    
    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };
    
    default:
      return state;
  }
}

// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Configuration Axios avec intercepteur pour les tokens
axios.defaults.baseURL = API_URL;

// Provider du contexte d'authentification
export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Intercepteur pour ajouter le token d'authentification
  useEffect(() => {
    const requestInterceptor = axios.interceptors.request.use(
      (config) => {
        if (state.tokens?.access_token) {
          config.headers.Authorization = `Bearer ${state.tokens.access_token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Intercepteur pour gérer les erreurs 401 (token expiré)
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401 && state.tokens?.refresh_token) {
          try {
            await refreshToken();
            // Retry la requête originale
            return axios.request(error.config);
          } catch (refreshError) {
            logout();
            return Promise.reject(refreshError);
          }
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, [state.tokens]);

  // Vérifier l'authentification au chargement
  useEffect(() => {
    checkAuthStatus();
  }, []);

  /**
   * Vérifie si l'utilisateur est déjà connecté (token en localStorage)
   */
  const checkAuthStatus = async () => {
    try {
      const storedTokens = localStorage.getItem('auth_tokens');
      const storedUser = localStorage.getItem('auth_user');

      if (storedTokens && storedUser) {
        const tokens = JSON.parse(storedTokens);
        const user = JSON.parse(storedUser);

        // Vérifier si le token n'est pas expiré
        if (tokens.access_token) {
          try {
            const decoded = jwtDecode(tokens.access_token);
            const currentTime = Date.now() / 1000;
            
            if (decoded.exp > currentTime) {
              // Token valide
              dispatch({
                type: AUTH_ACTIONS.SET_USER,
                payload: { user, tokens }
              });
              return;
            }
          } catch (decodeError) {
            console.error('Erreur décodage token:', decodeError);
          }
        }

        // Si le token est expiré, essayer de le rafraîchir
        if (tokens.refresh_token) {
          try {
            await refreshToken(tokens.refresh_token);
            return;
          } catch (refreshError) {
            console.error('Erreur refresh token:', refreshError);
          }
        }
      }

      // Aucun token valide trouvé
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    } catch (error) {
      console.error('Erreur vérification auth:', error);
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  };

  /**
   * Connexion avec email/username et mot de passe
   */
  const login = async (credentials) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_START });

    try {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await axios.post('/auth/login', formData);
      
      const { user, tokens } = response.data;

      // Sauvegarder dans localStorage
      localStorage.setItem('auth_tokens', JSON.stringify(tokens));
      localStorage.setItem('auth_user', JSON.stringify(user));

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: { user, tokens }
      });

      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Erreur de connexion';
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage
      });
      return { success: false, error: errorMessage };
    }
  };

  /**
   * Inscription d'un nouvel utilisateur
   */
  const register = async (userData) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_START });

    try {
      const response = await axios.post('/auth/register', userData);
      
      const { user, tokens } = response.data;

      // Sauvegarder dans localStorage
      localStorage.setItem('auth_tokens', JSON.stringify(tokens));
      localStorage.setItem('auth_user', JSON.stringify(user));

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: { user, tokens }
      });

      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Erreur lors de l\'inscription';
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage
      });
      return { success: false, error: errorMessage };
    }
  };

  /**
   * Rafraîchir le token d'accès
   */
  const refreshToken = async (refresh_token = null) => {
    try {
      const tokenToUse = refresh_token || state.tokens?.refresh_token;
      
      if (!tokenToUse) {
        throw new Error('Aucun refresh token disponible');
      }

      const response = await axios.post('/auth/refresh', {
        refresh_token: tokenToUse
      });

      const newTokens = response.data;

      // Mettre à jour les tokens stockés
      const storedUser = localStorage.getItem('auth_user');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        localStorage.setItem('auth_tokens', JSON.stringify(newTokens));

        dispatch({
          type: AUTH_ACTIONS.SET_USER,
          payload: { user, tokens: newTokens }
        });
      }

      return newTokens;
    } catch (error) {
      console.error('Erreur refresh token:', error);
      logout();
      throw error;
    }
  };

  /**
   * Déconnexion
   */
  const logout = async () => {
    try {
      // Révoquer le refresh token côté serveur
      if (state.tokens?.refresh_token) {
        await axios.post('/auth/logout', {
          refresh_token: state.tokens.refresh_token
        });
      }
    } catch (error) {
      console.error('Erreur lors de la déconnexion côté serveur:', error);
    } finally {
      // Nettoyer le localStorage et l'état local
      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('auth_user');
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  };

  /**
   * Effacer les erreurs
   */
  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  const contextValue = {
    ...state,
    login,
    register,
    logout,
    refreshToken,
    clearError
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook pour utiliser le contexte d'authentification
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth doit être utilisé dans un AuthProvider');
  }
  return context;
}

export default AuthContext;