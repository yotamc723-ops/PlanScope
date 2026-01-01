import React from 'react';
// CSS is handled via Tailwind CDN and inline styles below

export const metadata = {
  title: 'Municipal Dashboard',
  description: 'A Google-style SaaS dashboard for viewing municipal meetings and construction permits.',
};

export default function RootLayout({
  children,
}: {
  children?: React.ReactNode;
}) {
  return (
    <html lang="he" dir="rtl">
      <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&display=swap" rel="stylesheet" />
        <script dangerouslySetInnerHTML={{__html: `
          tailwind.config = {
            theme: {
              extend: {
                fontFamily: {
                  sans: ['Assistant', 'sans-serif'],
                },
                colors: {
                  primary: '#1a73e8',
                  primaryHover: '#1557b0',
                  surface: '#ffffff',
                  background: '#f8f9fa',
                  textPrimary: '#202124',
                  textSecondary: '#5f6368',
                  border: '#dadce0',
                }
              }
            }
          }
        `}} />
        <style>{`
          body {
            background-color: #f8f9fa;
            color: #202124;
          }
          ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
          }
          ::-webkit-scrollbar-track {
            background: #f1f1f1; 
          }
          ::-webkit-scrollbar-thumb {
            background: #dadce0; 
            border-radius: 4px;
          }
          ::-webkit-scrollbar-thumb:hover {
            background: #bdc1c6; 
          }
        `}</style>
      </head>
      <body>{children}</body>
    </html>
  );
}