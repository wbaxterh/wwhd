'use client';

import { AuthProvider } from '@/contexts/auth';
import { ThemeProvider } from '@/components/ThemeProvider';
import { ReactNode } from 'react';

interface ClientProvidersProps {
  children: ReactNode;
}

export function ClientProviders({ children }: ClientProvidersProps) {
  return (
    <ThemeProvider>
      <AuthProvider>
        {children}
      </AuthProvider>
    </ThemeProvider>
  );
}