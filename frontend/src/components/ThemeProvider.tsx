'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { ThemeProvider as NextThemeProvider } from 'next-themes';

export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemeProvider>) {
  return (
    <NextThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      {...props}
    >
      {children}
    </NextThemeProvider>
  );
}