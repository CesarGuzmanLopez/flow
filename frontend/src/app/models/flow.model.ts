export interface Flow {
  id: number;
  name: string;
  description?: string;
  owner: number;
  created_at: string;
  updated_at: string;
  current_version?: FlowVersion;
  versions: FlowVersion[];
}

export interface FlowVersion {
  id: number;
  flow: number;
  version_number: number;
  parent_version?: number;
  created_at: string;
  created_by: number;
  metadata: Record<string, any>;
  steps: Step[];
  is_frozen: boolean;
}

export interface Step {
  id: number;
  flow_version: number;
  name: string;
  description?: string;
  step_type: string;
  order: number;
  config: Record<string, any>;
  inputs: StepInput[];
  outputs: StepOutput[];
  dependencies: number[]; // IDs of steps this depends on
}

export interface StepInput {
  name: string;
  type: string;
  required: boolean;
  default_value?: any;
}

export interface StepOutput {
  name: string;
  type: string;
}

export interface StepExecution {
  id: number;
  step: number;
  execution_snapshot: number;
  started_at: string;
  completed_at?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  inputs: Record<string, any>;
  outputs?: Record<string, any>;
  artifacts: Artifact[];
  error_message?: string;
}

export interface ExecutionSnapshot {
  id: number;
  flow_version: number;
  created_at: string;
  triggered_by: number;
  metadata: Record<string, any>;
  step_executions: StepExecution[];
  status: 'running' | 'completed' | 'failed' | 'partial';
}

export interface Artifact {
  id: number;
  sha256: string;
  filename: string;
  content_type: string;
  size: number;
  created_at: string;
  created_by: number;
  metadata: Record<string, any>;
  storage_path: string;
}
