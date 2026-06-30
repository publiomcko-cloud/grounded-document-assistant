export type HealthCheck = {
  status: string;
  latency_ms: number;
  detail?: string;
};

export type HealthResponse = {
  status: string;
  environment: string;
  timestamp: string;
  checks: {
    database: HealthCheck;
    redis: HealthCheck;
  };
};
