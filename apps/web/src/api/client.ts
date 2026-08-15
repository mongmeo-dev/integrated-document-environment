import { Configuration, SystemApi } from "@/api/generated";

const configuration = new Configuration({
  basePath: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  baseOptions: {
    withCredentials: true,
  },
});

export const systemApi = new SystemApi(configuration);
