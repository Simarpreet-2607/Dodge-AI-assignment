import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Graph-Based Data Modeling and Query System',
  description: 'Transform structured business data into a graph and query it using natural language.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <main style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
          {children}
        </main>
      </body>
    </html>
  );
}
