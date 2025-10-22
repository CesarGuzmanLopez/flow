import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { FlowsService as ApiFlowsService } from '../api/api/flows.service';
import {
  ExecutionSnapshot,
  Flow,
  FlowVersion,
  Step,
  StepExecution,
} from '../api/model/models';

/**
 * Application service for flows domain.
 * Wraps generated API service with domain-specific logic.
 */
@Injectable({ providedIn: 'root' })
export class FlowsAppService {
  private readonly api = inject(ApiFlowsService);

  // ========== Flows ==========
  listFlows(): Observable<Flow[]> {
    return this.api
      .flowsFlowsList()
      .pipe(
        map((result) =>
          Array.isArray(result) ? result : (result as any).results ?? []
        )
      );
  }

  getFlow(id: number): Observable<Flow> {
    return this.api.flowsFlowsRetrieve(id);
  }

  createFlow(data: Partial<Flow>): Observable<Flow> {
    return this.api.flowsFlowsCreate(data as Flow);
  }

  updateFlow(id: number, data: Partial<Flow>): Observable<Flow> {
    return this.api.flowsFlowsPartialUpdate(id, data);
  }

  deleteFlow(id: number): Observable<void> {
    return this.api.flowsFlowsDestroy(id);
  }

  getMyFlows(): Observable<any> {
    return this.api
      .flowsFlowsList('body')
      .pipe(map((result) => (Array.isArray(result) ? result : [])));
  }

  // ========== Flow Definitions ==========
  listDefinitions(): Observable<any> {
    return this.api.flowsFlowsDefinitionsRetrieve();
  }

  createFromDefinition(
    key: string,
    name: string,
    paramsOverride?: any
  ): Observable<Flow> {
    const body: any = { key, name, params_override: paramsOverride };
    return this.api.flowsFlowsCreateFromDefinitionCreate(body);
  }

  // ========== Versions ==========
  getVersions(flowId: number): Observable<any> {
    return this.api.flowsFlowsVersionsRetrieve(flowId);
  }

  createVersion(flowId: number, data?: any): Observable<Flow> {
    return this.api.flowsFlowsCreateVersionCreate(flowId, data ?? {});
  }

  freezeVersion(versionId: number): Observable<FlowVersion> {
    return this.api.flowsVersionsFreezeCreate(versionId, {} as FlowVersion);
  }

  executeVersion(versionId: number): Observable<FlowVersion> {
    return this.api.flowsVersionsExecuteCreate(versionId, {} as FlowVersion);
  }

  // ========== Executions (Snapshots) ==========
  listExecutions(params?: {
    limit?: number;
    offset?: number;
  }): Observable<any> {
    const api = this.api as any;
    if (
      api.flowsExecutionsList &&
      typeof api.flowsExecutionsList === 'function'
    ) {
      return api
        .flowsExecutionsList(params?.limit, params?.offset)
        .pipe(
          map((result: any) =>
            Array.isArray(result) ? result : result?.results ?? []
          )
        );
    }
    // Fallback if method doesn't exist
    return new Observable((observer) => {
      observer.next([]);
      observer.complete();
    });
  }

  getExecution(id: number): Observable<ExecutionSnapshot> {
    const api = this.api as any;
    if (
      api.flowsExecutionsRetrieve &&
      typeof api.flowsExecutionsRetrieve === 'function'
    ) {
      return api.flowsExecutionsRetrieve(id);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  createExecution(
    data: Partial<ExecutionSnapshot>
  ): Observable<ExecutionSnapshot> {
    const api = this.api as any;
    if (
      api.flowsExecutionsCreate &&
      typeof api.flowsExecutionsCreate === 'function'
    ) {
      return api.flowsExecutionsCreate(data);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  // ========== Branches ==========
  getBranchPath(branchId: number): Observable<any> {
    return this.api.flowsBranchesPathRetrieve(branchId);
  }

  addStepToBranch(branchId: number, stepData: any): Observable<any> {
    return this.api.flowsBranchesAddStepCreate(branchId, stepData);
  }

  createBranch(flowId: number, data: any): Observable<Flow> {
    return this.api.flowsFlowsCreateBranchCreate(flowId, data);
  }

  updateBranch(branchId: number, data: any): Observable<any> {
    return this.api.flowsBranchesPartialUpdate(branchId, data);
  }

  listBranches(params?: any): Observable<any[]> {
    // Generated service likely supports pagination; normalize to array
    const api = this.api as any;
    if (api.flowsBranchesList && typeof api.flowsBranchesList === 'function') {
      return api
        .flowsBranchesList(params?.limit, params?.offset)
        .pipe(
          map((result: any) =>
            Array.isArray(result) ? result : result?.results ?? []
          )
        );
    }
    // Fallback if method doesn't exist
    return new Observable((observer) => {
      observer.next([]);
      observer.complete();
    });
  }

  getBranch(branchId: number): Observable<any> {
    const api = this.api as any;
    if (
      api.flowsBranchesRetrieve &&
      typeof api.flowsBranchesRetrieve === 'function'
    ) {
      return api.flowsBranchesRetrieve(branchId);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  createBranchGlobal(data: any): Observable<any> {
    const api = this.api as any;
    if (
      api.flowsBranchesCreate &&
      typeof api.flowsBranchesCreate === 'function'
    ) {
      return api.flowsBranchesCreate(data);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  deleteBranch(branchId: number): Observable<void> {
    const api = this.api as any;
    if (
      api.flowsBranchesDestroy &&
      typeof api.flowsBranchesDestroy === 'function'
    ) {
      return api.flowsBranchesDestroy(branchId);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  listNodes(params?: any): Observable<any[]> {
    const api = this.api as any;
    if (api.flowsNodesList && typeof api.flowsNodesList === 'function') {
      return api
        .flowsNodesList(params?.limit, params?.offset)
        .pipe(
          map((result: any) =>
            Array.isArray(result) ? result : result?.results ?? []
          )
        );
    }
    return new Observable((observer) => {
      observer.next([]);
      observer.complete();
    });
  }

  getNode(id: number): Observable<any> {
    const api = this.api as any;
    if (
      api.flowsNodesRetrieve &&
      typeof api.flowsNodesRetrieve === 'function'
    ) {
      return api.flowsNodesRetrieve(id);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  // ========== Steps ==========
  listSteps(params?: any): Observable<Step[]> {
    const api = this.api as any;
    if (api.flowsStepsList && typeof api.flowsStepsList === 'function') {
      return api
        .flowsStepsList(params?.limit, params?.offset)
        .pipe(
          map((result: any) =>
            Array.isArray(result) ? result : result?.results ?? []
          )
        );
    }
    return new Observable((observer) => {
      observer.next([]);
      observer.complete();
    });
  }

  getStep(id: number): Observable<Step> {
    const api = this.api as any;
    if (
      api.flowsStepsRetrieve &&
      typeof api.flowsStepsRetrieve === 'function'
    ) {
      return api.flowsStepsRetrieve(id);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  createStep(step: Step): Observable<Step> {
    const api = this.api as any;
    if (api.flowsStepsCreate && typeof api.flowsStepsCreate === 'function') {
      return api.flowsStepsCreate(step);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  updateStep(id: number, step: Partial<Step>): Observable<Step> {
    const api = this.api as any;
    if (
      api.flowsStepsPartialUpdate &&
      typeof api.flowsStepsPartialUpdate === 'function'
    ) {
      return api.flowsStepsPartialUpdate(id, step);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  deleteStep(id: number): Observable<void> {
    const api = this.api as any;
    if (api.flowsStepsDestroy && typeof api.flowsStepsDestroy === 'function') {
      return api.flowsStepsDestroy(id);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }
  getStepCatalog(): Observable<any> {
    return this.api.flowsStepsCatalogRetrieve();
  }

  executeStep(stepData: any): Observable<Step> {
    return this.api.flowsStepsExecuteCreate(stepData);
  }

  runStep(stepId: number, params?: any): Observable<Step> {
    return this.api.flowsStepsRunCreate(stepId, params ?? {});
  }

  // ========== Step Executions ==========
  createStepExecution(data: StepExecution): Observable<StepExecution> {
    return this.api.flowsStepExecutionsCreate(data);
  }

  // Compatibility wrapper: list step executions (paginated)
  listStepExecutions(params?: {
    limit?: number;
    offset?: number;
  }): Observable<any> {
    const api = this.api as any;
    if (
      api.flowsStepExecutionsList &&
      typeof api.flowsStepExecutionsList === 'function'
    ) {
      return api
        .flowsStepExecutionsList(params?.limit, params?.offset)
        .pipe(
          map((result: any) =>
            Array.isArray(result) ? result : result?.results ?? []
          )
        );
    }
    return new Observable((observer) => {
      observer.next([]);
      observer.complete();
    });
  }

  // Compatibility wrapper: retrieve single step execution
  getStepExecution(id: number): Observable<any> {
    const api = this.api as any;
    if (
      api.flowsStepExecutionsRetrieve &&
      typeof api.flowsStepExecutionsRetrieve === 'function'
    ) {
      return api.flowsStepExecutionsRetrieve(id);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  getStepExecutionStatus(executionId: number): Observable<StepExecution> {
    return this.api.flowsStepExecutionsStatusRetrieve(executionId);
  }

  cancelStepExecution(executionId: number): Observable<StepExecution> {
    return this.api.flowsStepExecutionsCancelCreate(
      executionId,
      {} as StepExecution
    );
  }

  updateStepExecution(
    executionId: number,
    data: Partial<StepExecution>
  ): Observable<StepExecution> {
    return this.api.flowsStepExecutionsPartialUpdate(executionId, data);
  }

  deleteStepExecution(executionId: number): Observable<void> {
    return this.api.flowsStepExecutionsDestroy(executionId);
  }

  // ========== Executions (Snapshots) ==========
  getExecutionSteps(executionId: number): Observable<ExecutionSnapshot> {
    return this.api.flowsExecutionsStepsRetrieve(executionId);
  }

  updateExecution(
    executionId: number,
    data: Partial<ExecutionSnapshot>
  ): Observable<ExecutionSnapshot> {
    return this.api.flowsExecutionsPartialUpdate(executionId, data);
  }

  deleteExecution(executionId: number): Observable<void> {
    return this.api.flowsExecutionsDestroy(executionId);
  }

  // ========== Artifacts ==========
  getArtifactDownloadUrl(artifactId: number): Observable<any> {
    return this.api.flowsArtifactsDownloadRetrieve(artifactId);
  }

  // Convenience wrappers matching previous frontend expectations
  getArtifacts(params?: any): Observable<any[]> {
    const api = this.api as any;
    if (
      api.flowsArtifactsList &&
      typeof api.flowsArtifactsList === 'function'
    ) {
      return api
        .flowsArtifactsList(params?.limit, params?.offset)
        .pipe(
          map((result: any) =>
            Array.isArray(result) ? result : result?.results ?? []
          )
        );
    }
    return new Observable((observer) => {
      observer.next([]);
      observer.complete();
    });
  }

  downloadArtifact(artifactId: number): Observable<Blob> {
    // The generated client may return an Artifact or a URL; prefer the download retrieve
    return this.api.flowsArtifactsDownloadRetrieve(
      artifactId
    ) as unknown as Observable<Blob>;
  }

  getArtifact(id: number): Observable<any> {
    const api = this.api as any;
    if (
      api.flowsArtifactsRetrieve &&
      typeof api.flowsArtifactsRetrieve === 'function'
    ) {
      return api.flowsArtifactsRetrieve(id);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  createArtifact(data: any): Observable<any> {
    const api = this.api as any;
    if (
      api.flowsArtifactsCreate &&
      typeof api.flowsArtifactsCreate === 'function'
    ) {
      return api.flowsArtifactsCreate(data);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  updateArtifact(id: number, data: any): Observable<any> {
    const api = this.api as any;
    if (
      api.flowsArtifactsPartialUpdate &&
      typeof api.flowsArtifactsPartialUpdate === 'function'
    ) {
      return api.flowsArtifactsPartialUpdate(id, data);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }

  deleteArtifact(id: number): Observable<void> {
    const api = this.api as any;
    if (
      api.flowsArtifactsDestroy &&
      typeof api.flowsArtifactsDestroy === 'function'
    ) {
      return api.flowsArtifactsDestroy(id);
    }
    return new Observable((observer) => {
      observer.error(new Error('Method not available'));
    });
  }
}
