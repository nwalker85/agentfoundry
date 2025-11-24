import NextAuth from 'next-auth';
import { JWT } from 'next-auth/jwt';

declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
      organizationId?: string;
      permissions?: string[];
      roles?: Array<{
        name: string;
        description?: string;
      }>;
      /** OIDC access token from Zitadel (RS256) */
      accessToken?: string;
      /** Authentication provider used (e.g., 'zitadel') */
      provider?: string;
    };
  }

  interface User {
    id: string;
    email: string;
    name?: string;
    image?: string;
    organizationId?: string;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id?: string;
    organizationId?: string;
    permissions?: string[];
    roles?: Array<{
      name: string;
      description?: string;
    }>;
    /** OIDC access token from provider */
    accessToken?: string;
    /** Authentication provider */
    provider?: string;
  }
}
