"use client";

import { Badge, Container, Heading, Stack, Text } from "@chakra-ui/react";

import { useHealthQuery } from "@/features/system/use-health-query";

export default function Home() {
  const health = useHealthQuery();

  return (
    <Container as="main" maxW="4xl" py={{ base: "10", md: "16" }}>
      <Stack gap="6">
        <Stack gap="2">
          <Text color="fg.muted" fontWeight="medium">
            뉴다이브
          </Text>
          <Heading size="3xl">Integrated Document Environment</Heading>
          <Text color="fg.muted">
            GMP 문서 변경 요청, 영향 검토와 승인을 위한 내부 작업 환경
          </Text>
        </Stack>

        <Stack align="start" gap="2">
          <Text fontWeight="semibold">API 상태</Text>
          {health.isPending && <Badge colorPalette="gray">확인 중</Badge>}
          {health.isSuccess && <Badge colorPalette="green">정상</Badge>}
          {health.isError && <Badge colorPalette="red">연결 실패</Badge>}
        </Stack>
      </Stack>
    </Container>
  );
}
