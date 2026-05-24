/** @type {import('next').NextConfig} */
const { PHASE_DEVELOPMENT_SERVER } = require('next/constants')

module.exports = (phase) => {
  const isDev = phase === PHASE_DEVELOPMENT_SERVER

  const nextConfig = {
    images: {
      remotePatterns: [
        { protocol: 'https', hostname: 'softwaresalao.onrender.com' },
      ],
    },
  }

  if (isDev) return nextConfig

  const withSerwist = require('@serwist/next').default({
    swSrc: 'app/sw.ts',
    swDest: 'public/sw.js',
  })

  return withSerwist(nextConfig)
}