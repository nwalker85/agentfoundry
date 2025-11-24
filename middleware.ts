import { withAuth } from 'next-auth/middleware';

// Protect the authenticated application surface
export default withAuth({
  pages: {
    signIn: '/login',
  },
});

export const config = {
  matcher: ['/app/:path*'],
};
