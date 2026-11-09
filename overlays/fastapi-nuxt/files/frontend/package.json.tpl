{
  "name": "${PROJECT_SLUG}-frontend",
  "private": true,
  "version": "${PROJECT_VERSION}",
  "type": "module",
  "scripts": {
    "build": "nuxt build",
    "dev": "nuxt dev",
    "typecheck": "nuxt typecheck",
    "test": "vitest run"
  },
  "dependencies": {
    "@nuxt/ui": "^4.0.0",
    "nuxt": "^4.0.0",
    "vue": "^3.5.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "typescript": "^5.9.0",
    "vitest": "^3.0.0",
    "vue-tsc": "^3.0.0"
  }
}

