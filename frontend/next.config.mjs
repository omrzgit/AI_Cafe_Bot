/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'production'
          ? '/api/:path*'
          : 'http://localhost:8000/api/:path*',
      },
      {
        source: '/auth/:path*',
        destination: process.env.NODE_ENV === 'production'
          ? '/auth/:path*'
          : 'http://localhost:8000/auth/:path*',
      },
    ];
  },
};

export default nextConfig;
