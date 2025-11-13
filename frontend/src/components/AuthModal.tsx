'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/auth';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleTestUser = async () => {
    setIsLoading(true);
    try {
      // Use the existing test user credentials
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'username=testuser&password=testpass123',
      });

      if (!response.ok) {
        throw new Error('Failed to authenticate');
      }

      const data = await response.json();

      // Create user object from token response (backend includes user info in token response)
      const userData = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com'
      };

      login(data.access_token, userData);
      onClose();
    } catch (error) {
      console.error('Authentication error:', error);
      alert('Failed to authenticate. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md mx-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-foreground mb-2">Welcome to W.W.H.D.</h2>
          <p className="text-muted-foreground">Choose how you'd like to proceed</p>
        </div>

        <div className="space-y-4">
          <button
            onClick={handleTestUser}
            disabled={isLoading}
            className="w-full px-4 py-3 bg-white text-slate-900 rounded-md hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg"
          >
            {isLoading ? 'Connecting...' : 'Try Test Chat'}
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-card px-2 text-muted-foreground">or</span>
            </div>
          </div>

          <button
            className="w-full px-4 py-3 border border-border text-foreground rounded-md hover:bg-muted/50 transition-colors"
            disabled
          >
            Register Account (Coming Soon)
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-muted-foreground">
            Test chat uses a demo account to explore Herman's wisdom
          </p>
        </div>
      </div>
    </div>
  );
}