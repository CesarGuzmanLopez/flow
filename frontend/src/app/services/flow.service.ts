import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_PREFIX } from '../config';
import {
  Artifact,
  ExecutionSnapshot,
  Flow,
  FlowVersion,
  Step,
  StepExecution,
} from '../models';

@Injectable({
  providedIn: 'root',
})
export class FlowService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${API_PREFIX}/flows`;

  // Flow CRUD
  getFlows(params?: any): Observable<{ results: Flow[]; count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<{ results: Flow[]; count: number }>(
      `${this.apiUrl}/flows/`,
      { params: httpParams }
    );
  }

  getFlow(id: number): Observable<Flow> {
    return this.http.get<Flow>(`${this.apiUrl}/flows/${id}/`);
  }

  createBranch(flowId: number, payload: any = {}): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/flows/${flowId}/create-branch/`,
      payload
    );
  }

  createFlow(flow: Partial<Flow>): Observable<Flow> {
    return this.http.post<Flow>(`${this.apiUrl}/flows/`, flow);
  }

  updateFlow(id: number, flow: Partial<Flow>): Observable<Flow> {
    return this.http.patch<Flow>(`${this.apiUrl}/flows/${id}/`, flow);
  }

  deleteFlow(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/flows/${id}/`);
  }

  // Flow Version operations
  getFlowVersions(flowId: number): Observable<FlowVersion[]> {
    return this.http.get<FlowVersion[]>(
      `${this.apiUrl}/flows/${flowId}/versions/`
    );
  }

  getFlowVersion(flowId: number, versionId: number): Observable<FlowVersion> {
    return this.http.get<FlowVersion>(
      `${this.apiUrl}/flows/${flowId}/versions/${versionId}/`
    );
  }

  createFlowVersion(
    flowId: number,
    version: Partial<FlowVersion>
  ): Observable<FlowVersion> {
    return this.http.post<FlowVersion>(
      `${this.apiUrl}/flows/${flowId}/versions/`,
      version
    );
  }

  freezeFlowVersion(
    flowId: number,
    versionId: number
  ): Observable<FlowVersion> {
    return this.http.post<FlowVersion>(
      `${this.apiUrl}/flows/${flowId}/versions/${versionId}/freeze/`,
      {}
    );
  }

  // Step operations
  getSteps(flowId: number, versionId: number): Observable<Step[]> {
    return this.http.get<Step[]>(
      `${this.apiUrl}/flows/${flowId}/versions/${versionId}/steps/`
    );
  }

  // Steps (global)
  listSteps(params?: any): Observable<{ results: Step[]; count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(
        (k) => (httpParams = httpParams.set(k, params[k]))
      );
    }
    return this.http.get<{ results: Step[]; count: number }>(
      `${this.apiUrl}/steps/`,
      { params: httpParams }
    );
  }

  getStep(stepId: number): Observable<Step> {
    return this.http.get<Step>(`${this.apiUrl}/steps/${stepId}/`);
  }

  createStep(
    flowId: number,
    versionId: number,
    step: Partial<Step>
  ): Observable<Step> {
    return this.http.post<Step>(
      `${this.apiUrl}/flows/${flowId}/versions/${versionId}/steps/`,
      step
    );
  }

  updateStep(
    flowId: number,
    versionId: number,
    stepId: number,
    step: Partial<Step>
  ): Observable<Step> {
    return this.http.patch<Step>(
      `${this.apiUrl}/flows/${flowId}/versions/${versionId}/steps/${stepId}/`,
      step
    );
  }

  deleteStep(
    flowId: number,
    versionId: number,
    stepId: number
  ): Observable<void> {
    return this.http.delete<void>(
      `${this.apiUrl}/flows/${flowId}/versions/${versionId}/steps/${stepId}/`
    );
  }

  // Execution operations
  executeFlow(
    flowId: number,
    versionId: number,
    inputs?: Record<string, any>
  ): Observable<ExecutionSnapshot> {
    return this.http.post<ExecutionSnapshot>(
      `${this.apiUrl}/flows/${flowId}/versions/${versionId}/execute/`,
      { inputs }
    );
  }

  getExecutionSnapshot(snapshotId: number): Observable<ExecutionSnapshot> {
    return this.http.get<ExecutionSnapshot>(
      `${this.apiUrl}/executions/${snapshotId}/`
    );
  }

  getStepExecutions(snapshotId: number): Observable<StepExecution[]> {
    return this.http.get<StepExecution[]>(
      `${this.apiUrl}/executions/${snapshotId}/steps/`
    );
  }

  // Step Executions (global)
  listStepExecutions(
    params?: any
  ): Observable<{ results: StepExecution[]; count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(
        (k) => (httpParams = httpParams.set(k, params[k]))
      );
    }
    return this.http.get<{ results: StepExecution[]; count: number }>(
      `${this.apiUrl}/step-executions/`,
      { params: httpParams }
    );
  }

  getStepExecution(id: number): Observable<StepExecution> {
    return this.http.get<StepExecution>(
      `${this.apiUrl}/step-executions/${id}/`
    );
  }

  // Artifact operations
  getArtifacts(params?: any): Observable<Artifact[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<Artifact[]>(`${this.apiUrl}/artifacts/`, {
      params: httpParams,
    });
  }

  downloadArtifact(artifactId: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/artifacts/${artifactId}/download/`, {
      responseType: 'blob',
    });
  }

  // Additional endpoints from OpenAPI spec

  // Flows (mine)
  getMyFlows(): Observable<Flow[]> {
    return this.http.get<Flow[]>(`${this.apiUrl}/flows/mine/`);
  }

  // Branches
  listBranches(params?: any): Observable<{ results: any[]; count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(
        (k) => (httpParams = httpParams.set(k, params[k]))
      );
    }
    return this.http.get<{ results: any[]; count: number }>(
      `${this.apiUrl}/branches/`,
      { params: httpParams }
    );
  }

  getBranch(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/branches/${id}/`);
  }

  addStepToBranch(branchId: number, payload: any): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/branches/${branchId}/add-step/`,
      payload
    );
  }

  getBranchPath(branchId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/branches/${branchId}/path/`);
  }

  // Nodes
  listNodes(params?: any): Observable<{ results: any[]; count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(
        (k) => (httpParams = httpParams.set(k, params[k]))
      );
    }
    return this.http.get<{ results: any[]; count: number }>(
      `${this.apiUrl}/nodes/`,
      { params: httpParams }
    );
  }

  getNode(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/nodes/${id}/`);
  }

  // Artifacts (single)
  getArtifact(id: number): Observable<Artifact> {
    return this.http.get<Artifact>(`${this.apiUrl}/artifacts/${id}/`);
  }

  // Global versions endpoints
  listVersions(
    params?: any
  ): Observable<{ results: FlowVersion[]; count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(
        (k) => (httpParams = httpParams.set(k, params[k]))
      );
    }
    return this.http.get<{ results: FlowVersion[]; count: number }>(
      `${this.apiUrl}/versions/`,
      { params: httpParams }
    );
  }

  getVersion(versionId: number): Observable<FlowVersion> {
    return this.http.get<FlowVersion>(`${this.apiUrl}/versions/${versionId}/`);
  }

  executeVersion(
    versionId: number,
    inputs?: Record<string, any>
  ): Observable<ExecutionSnapshot> {
    return this.http.post<ExecutionSnapshot>(
      `${this.apiUrl}/versions/${versionId}/execute/`,
      { inputs }
    );
  }

  freezeVersion(versionId: number): Observable<FlowVersion> {
    return this.http.post<FlowVersion>(
      `${this.apiUrl}/versions/${versionId}/freeze/`,
      {}
    );
  }

  // Convenience: create version via create_version endpoint on flow
  createVersionForFlow(
    flowId: number,
    payload: any = {}
  ): Observable<FlowVersion> {
    return this.http.post<FlowVersion>(
      `${this.apiUrl}/flows/${flowId}/create_version/`,
      payload
    );
  }
}
