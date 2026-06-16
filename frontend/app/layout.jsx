# frontend/app/layout.jsx
'use client';

import './globals.css';
import { Inter } from '@next/font/google';
import Head from 'next/head';

// If using Google Fonts, configure them here
// const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Taiwan Stock Monopoly',
  description: 'Simulate wealth accumulation and become the richest!',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      {/* <body className={inter.className}> */}
      <body>
        {children}
      </body>
    </html>
  );
}
