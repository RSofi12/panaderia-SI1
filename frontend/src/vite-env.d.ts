/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_STRIPE_PUBLISHABLE_KEY?: string;
}

declare module '*.svg' {
  const content: string;
  export default content;
}

declare module 'lucide-react';
