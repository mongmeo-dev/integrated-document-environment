"use client";

import { useQuery } from "@tanstack/react-query";

import { healthQueryOptions } from "./health-query";

export function useHealthQuery() {
  return useQuery(healthQueryOptions());
}
