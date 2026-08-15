import { queryOptions } from "@tanstack/react-query";

import { systemApi } from "@/api/client";

export const systemQueryKeys = {
  all: ["system"] as const,
  health: () => [...systemQueryKeys.all, "health"] as const,
};

export type HealthStatus = "ok";

export function healthQueryOptions() {
  return queryOptions({
    queryKey: systemQueryKeys.health(),
    queryFn: async (): Promise<HealthStatus> => {
      const response = await systemApi.getHealth();
      return response.data.status;
    },
  });
}
