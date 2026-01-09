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
    <>
      {children}
    </>
  );
}