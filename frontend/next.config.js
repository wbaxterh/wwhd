/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  // Disable static export for now since we're using API routes
  // We can enable this later when we remove the proxy API routes
}

module.exports = nextConfig