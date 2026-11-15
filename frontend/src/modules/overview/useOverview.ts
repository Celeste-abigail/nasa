import { useQuery } from "@tanstack/react-query";

import { api } from "../../lib/api";
import type { Site } from "../../lib/types";

export function useOverview(astronaut: string, site: Site, lang: string) {
  const enabled = astronaut !== "";

  const bone = useQuery({
    queryKey: ["monitoring", astronaut, site, lang],
    queryFn: () => api.monitoring(astronaut, site, lang),
    enabled,
  });

  const cortisol = useQuery({
    queryKey: ["cortisol", astronaut, lang],
    queryFn: () => api.cortisol(astronaut, lang),
    enabled,
  });

  const radiation = useQuery({
    queryKey: ["radiation", astronaut, lang],
    queryFn: () => api.radiation(astronaut, lang),
    enabled,
  });

  const mental = useQuery({
    queryKey: ["mental", astronaut, lang],
    queryFn: () => api.mental(astronaut, lang),
    enabled,
  });

  return { bone, cortisol, radiation, mental };
}
