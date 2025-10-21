import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { Artifact, ExecutionSnapshot, Flow, FlowVersion, Step, StepExecution } from '../models';

@Injectable({
  providedIn: 'root'
})
export class FlowService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api/flows';

  // Flow CRUD
  getFlows(params?: any): Observable<{ results: Flow[], count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(key => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<{ results: Flow[], count: number }>(`${this.apiUrl}/flows/`, { params: httpParams });
  }

  getFlow(id: number): Observable<Flow> {
    return this.http.get<Flow>(`${this.apiUrl}/flows/${id}/`);
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
    return this.http.get<FlowVersion[]>(`${this.apiUrl}/flows/${flowId}/versions/`);
  }

  getFlowVersion(flowId: number, versionId: number): Observable<FlowVersion> {
    return this.http.get<FlowVersion>(`${this.apiUrl}/flows/${flowId}/versions/${versionId}/`);
  }

  createFlowVersion(flowId: number, version: Partial<FlowVersion>): Observable<FlowVersion> {
    return this.http.post<FlowVersion>(`${this.apiUrl}/flows/${flowId}/versions/`, version);
  }

  freezeFlowVersion(flowId: number, versionId: number): Observable<FlowVersion> {
    return this.http.post<FlowVersion>(`${this.apiUrl}/flows/${flowId}/versions/${versionId}/freeze/`, {});
  }

  // Step operations
  getSteps(flowId: number, versionId: number): Observable<Step[]> {
    return this.http.get<Step[]>(`${this.apiUrl}/flows/${flowId}/versions/${versionId}/steps/`);
  }

  createStep(flowId: number, versionId: number, step: Partial<Step>): Observable<Step> {
    return this.http.post<Step>(`${this.apiUrl}/flows/${flowId}/versions/${versionId}/steps/`, step);
  }

  updateStep(flowId: number, versionId: number, stepId: number, step: Partial<Step>): Observable<Step> {
    return this.http.patch<Step>(`${this.apiUrl}/flows/${flowId}/versions/${versionId}/steps/${stepId}/`, step);
  }

  deleteStep(flowId: number, versionId: number, stepId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/flows/${flowId}/versions/${versionId}/steps/${stepId}/`);
  }

  // Execution operations
  executeFlow(flowId: number, versionId: number, inputs?: Record<string, any>): Observable<ExecutionSnapshot> {
    return this.http.post<ExecutionSnapshot>(`${this.apiUrl}/flows/${flowId}/versions/${versionId}/execute/`, { inputs });
  }

  getExecutionSnapshot(snapshotId: number): Observable<ExecutionSnapshot> {
    return this.http.get<ExecutionSnapshot>(`${this.apiUrl}/executions/${snapshotId}/`);
  }

  getStepExecutions(snapshotId: number): Observable<StepExecution[]> {
    return this.http.get<StepExecution[]>(`${this.apiUrl}/executions/${snapshotId}/steps/`);
  }

  // Artifact operations
  getArtifacts(params?: any): Observable<Artifact[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(key => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<Artifact[]>(`${this.apiUrl}/artifacts/`, { params: httpParams });
  }

  downloadArtifact(artifactId: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/artifacts/${artifactId}/download/`, { responseType: 'blob' });
  }
}
