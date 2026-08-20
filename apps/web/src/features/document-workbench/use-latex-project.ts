"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { latexApi } from "@/api/client";
import {
  CompileStatus,
  type ConversionReviewCreate,
  type LatexSourceRevisionCreate,
} from "@/api/generated";

const projectKey = (documentId: string) =>
  ["latex-project", documentId] as const;
const previewKey = (documentId: string, revisionId: string) =>
  ["latex-preview", documentId, revisionId] as const;

export function useLatexProject(documentId: string) {
  return useQuery({
    queryKey: projectKey(documentId),
    queryFn: async () => (await latexApi.getLatexProject({ documentId })).data,
  });
}

export function useLatexPreview(
  documentId: string,
  revisionId: string | undefined,
  previewAvailable: boolean,
  compileStatus: CompileStatus | undefined,
) {
  return useQuery({
    queryKey: previewKey(documentId, revisionId ?? "unavailable"),
    queryFn: async () =>
      (await latexApi.getLatexPreview({ documentId }, { responseType: "blob" }))
        .data as Blob,
    enabled:
      Boolean(revisionId) &&
      previewAvailable &&
      compileStatus === CompileStatus.Succeeded,
  });
}

export function useCreateLatexSourceRevisionMutation(documentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (latexSourceRevisionCreate: LatexSourceRevisionCreate) =>
      (
        await latexApi.createLatexSourceRevision({
          documentId,
          latexSourceRevisionCreate,
        })
      ).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: projectKey(documentId),
        exact: true,
      });
    },
  });
}

export function useReviewLatexConversionMutation(documentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (conversionReviewCreate: ConversionReviewCreate) =>
      (
        await latexApi.reviewLatexConversion({
          documentId,
          conversionReviewCreate,
        })
      ).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: projectKey(documentId),
        exact: true,
      });
    },
  });
}
