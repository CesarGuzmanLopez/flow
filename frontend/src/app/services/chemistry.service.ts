import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_PREFIX } from '../config';
import { Molecule, Protocol, Reaction } from '../models';

@Injectable({
  providedIn: 'root',
})
export class ChemistryService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${API_PREFIX}/chemistry`;

  // Molecule operations
  getMolecules(
    params?: any
  ): Observable<{ results: Molecule[]; count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<{ results: Molecule[]; count: number }>(
      `${this.apiUrl}/molecules/`,
      { params: httpParams }
    );
  }

  getMolecule(id: number): Observable<Molecule> {
    return this.http.get<Molecule>(`${this.apiUrl}/molecules/${id}/`);
  }

  createMolecule(molecule: Partial<Molecule>): Observable<Molecule> {
    return this.http.post<Molecule>(`${this.apiUrl}/molecules/`, molecule);
  }

  updateMolecule(
    id: number,
    molecule: Partial<Molecule>
  ): Observable<Molecule> {
    return this.http.patch<Molecule>(
      `${this.apiUrl}/molecules/${id}/`,
      molecule
    );
  }

  deleteMolecule(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/molecules/${id}/`);
  }

  // Molecules mine
  getMyMolecules(): Observable<Molecule[]> {
    return this.http.get<Molecule[]>(`${this.apiUrl}/molecules/mine/`);
  }

  // Reaction operations
  getReactions(
    params?: any
  ): Observable<{ results: Reaction[]; count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<{ results: Reaction[]; count: number }>(
      `${this.apiUrl}/reactions/`,
      { params: httpParams }
    );
  }

  getReaction(id: number): Observable<Reaction> {
    return this.http.get<Reaction>(`${this.apiUrl}/reactions/${id}/`);
  }

  createReaction(reaction: Partial<Reaction>): Observable<Reaction> {
    return this.http.post<Reaction>(`${this.apiUrl}/reactions/`, reaction);
  }

  updateReaction(
    id: number,
    reaction: Partial<Reaction>
  ): Observable<Reaction> {
    return this.http.patch<Reaction>(
      `${this.apiUrl}/reactions/${id}/`,
      reaction
    );
  }

  deleteReaction(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/reactions/${id}/`);
  }

  // Protocol operations
  getProtocols(
    params?: any
  ): Observable<{ results: Protocol[]; count: number }> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<{ results: Protocol[]; count: number }>(
      `${this.apiUrl}/protocols/`,
      { params: httpParams }
    );
  }

  getProtocol(id: number): Observable<Protocol> {
    return this.http.get<Protocol>(`${this.apiUrl}/protocols/${id}/`);
  }

  createProtocol(protocol: Partial<Protocol>): Observable<Protocol> {
    return this.http.post<Protocol>(`${this.apiUrl}/protocols/`, protocol);
  }

  updateProtocol(
    id: number,
    protocol: Partial<Protocol>
  ): Observable<Protocol> {
    return this.http.patch<Protocol>(
      `${this.apiUrl}/protocols/${id}/`,
      protocol
    );
  }

  deleteProtocol(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/protocols/${id}/`);
  }

  // Families
  getFamilies(params?: any): Observable<any> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<any>(`${this.apiUrl}/families/`, {
      params: httpParams,
    });
  }

  getFamily(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/families/${id}/`);
  }

  getMyFamilies(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/families/mine/`);
  }

  // Family Members
  getFamilyMembers(params?: any): Observable<any> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<any>(`${this.apiUrl}/family-members/`, {
      params: httpParams,
    });
  }

  getFamilyMember(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/family-members/${id}/`);
  }

  // Family Properties
  getFamilyProperties(params?: any): Observable<any> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<any>(`${this.apiUrl}/family-properties/`, {
      params: httpParams,
    });
  }

  getFamilyProperty(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/family-properties/${id}/`);
  }

  // Molecular Properties
  getMolecularProperties(params?: any): Observable<any> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        httpParams = httpParams.set(key, params[key]);
      });
    }
    return this.http.get<any>(`${this.apiUrl}/molecular-properties/`, {
      params: httpParams,
    });
  }

  getMolecularProperty(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/molecular-properties/${id}/`);
  }
}
