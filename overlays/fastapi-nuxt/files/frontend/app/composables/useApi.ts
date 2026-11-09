export function useApi<T>(path: string) {
  const config = useRuntimeConfig()
  return useFetch<T>(`$${config.public.apiBase}$${path}`)
}

