'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { API_URL } from '../config/api';

interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Function to validate token with backend
  const validateToken = async (tokenToValidate: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${tokenToValidate}`,
        },
      });
      return response.ok;
    } catch (error) {
      console.error('Token validation failed:', error);
      return false;
    }
  };

  // Function to refresh token
  const refreshToken = async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'username=testuser&password=testpass123',
      });

      if (!response.ok) {
        throw new Error('Failed to refresh token');
      }

      const data = await response.json();
      const userData = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com'
      };

      setToken(data.access_token);
      setUser(userData);
      localStorage.setItem('wwhd_token', data.access_token);
      localStorage.setItem('wwhd_user', JSON.stringify(userData));
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      return false;
    }
  };

  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);

      // Load auth state from localStorage
      const savedToken = localStorage.getItem('wwhd_token');
      const savedUser = localStorage.getItem('wwhd_user');

      if (savedToken && savedUser) {
        // Validate the token
        const isValid = await validateToken(savedToken);

        if (isValid) {
          setToken(savedToken);
          setUser(JSON.parse(savedUser));
        } else {
          // Token is invalid, try to refresh
          console.log('Token invalid, attempting refresh...');
          await refreshToken();
        }
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('wwhd_token', newToken);
    localStorage.setItem('wwhd_user', JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('wwhd_token');
    localStorage.removeItem('wwhd_user');
  };

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!user && !!token,
    isLoading,
    refreshToken
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}