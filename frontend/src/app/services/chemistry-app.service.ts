import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { ChemistryService as ApiChemistryService } from '../api/api/chemistry.service';
import { ChemistryFamiliesService } from '../api/api/chemistryFamilies.service';
import { ChemistryMoleculesService } from '../api/api/chemistryMolecules.service';
import { ChemistryPropertiesService } from '../api/api/chemistryProperties.service';
import {
  Family,
  FamilyMember,
  FamilyProperty,
  MolecularProperty,
  Molecule,
} from '../api/model/models';

/**
 * Application service for chemistry domain.
 * Wraps generated API services with domain logic.
 */
@Injectable({ providedIn: 'root' })
export class ChemistryAppService {
  private readonly chemApi = inject(ApiChemistryService);
  private readonly moleculesApi = inject(ChemistryMoleculesService);
  private readonly familiesApi = inject(ChemistryFamiliesService);
  private readonly propertiesApi = inject(ChemistryPropertiesService);

  // ========== Molecules ==========
  listMolecules(params?: any): Observable<Molecule[]> {
    return this.moleculesApi
      .chemistryMoleculesList(params?.mine, params?.ordering, params?.search)
      .pipe(
        map((result) =>
          Array.isArray(result) ? result : (result as any).results ?? []
        )
      );
  }

  getMolecule(id: number): Observable<Molecule> {
    return this.moleculesApi.chemistryMoleculesRetrieve(id);
  }

  createMolecule(molecule: Molecule): Observable<Molecule> {
    return this.moleculesApi.chemistryMoleculesCreate(molecule);
  }

  updateMolecule(id: number, molecule: Molecule): Observable<Molecule> {
    return this.moleculesApi.chemistryMoleculesUpdate(id, molecule);
  }

  deleteMolecule(id: number): Observable<void> {
    return this.moleculesApi.chemistryMoleculesDestroy(id);
  }

  getMyMolecules(): Observable<any> {
    return this.chemApi.chemistryMoleculesMineRetrieve();
  }

  // ========== Families ==========
  listFamilies(params?: any): Observable<Family[]> {
    return this.familiesApi
      .chemistryFamiliesList(params?.mine, params?.ordering, params?.search)
      .pipe(
        map((result) =>
          Array.isArray(result) ? result : (result as any).results ?? []
        )
      );
  }

  getFamily(id: number): Observable<Family> {
    return this.familiesApi.chemistryFamiliesRetrieve(id);
  }

  createFamily(family: Family): Observable<Family> {
    return this.familiesApi.chemistryFamiliesCreate(family);
  }

  updateFamily(id: number, family: Family): Observable<Family> {
    return this.familiesApi.chemistryFamiliesUpdate(id, family);
  }

  deleteFamily(id: number): Observable<void> {
    return this.familiesApi.chemistryFamiliesDestroy(id);
  }

  getMyFamilies(): Observable<any> {
    return this.chemApi.chemistryFamiliesMineRetrieve();
  }

  // ========== Family Members ==========
  listFamilyMembers(params?: any): Observable<FamilyMember[]> {
    return this.familiesApi
      .chemistryFamilyMembersList()
      .pipe(
        map((result) =>
          Array.isArray(result) ? result : (result as any).results ?? []
        )
      );
  }

  getFamilyMember(id: number): Observable<FamilyMember> {
    return this.familiesApi.chemistryFamilyMembersRetrieve(id);
  }

  createFamilyMember(data: FamilyMember): Observable<FamilyMember> {
    return this.familiesApi.chemistryFamilyMembersCreate(data);
  }

  updateFamilyMember(
    id: number,
    data: Partial<FamilyMember>
  ): Observable<FamilyMember> {
    return (this.familiesApi as any).chemistryFamilyMembersPartialUpdate?.(
      id,
      data
    );
  }

  deleteFamilyMember(id: number): Observable<void> {
    return this.familiesApi.chemistryFamilyMembersDestroy(
      id
    ) as unknown as Observable<void>;
  }

  // ========== Molecular Properties ==========
  listMolecularProperties(params?: any): Observable<MolecularProperty[]> {
    return this.propertiesApi
      .chemistryMolecularPropertiesList(
        params?.mine,
        params?.ordering,
        params?.search
      )
      .pipe(
        map((result) =>
          Array.isArray(result) ? result : (result as any).results ?? []
        )
      );
  }

  getMolecularProperty(id: number): Observable<MolecularProperty> {
    return this.propertiesApi.chemistryMolecularPropertiesRetrieve(id);
  }

  createMolecularProperty(
    data: MolecularProperty
  ): Observable<MolecularProperty> {
    return this.propertiesApi.chemistryMolecularPropertiesCreate(data);
  }

  updateMolecularProperty(
    id: number,
    data: Partial<MolecularProperty>
  ): Observable<MolecularProperty> {
    return (
      this.propertiesApi as any
    ).chemistryMolecularPropertiesPartialUpdate?.(id, data);
  }

  deleteMolecularProperty(id: number): Observable<void> {
    return this.propertiesApi.chemistryMolecularPropertiesDestroy(
      id
    ) as unknown as Observable<void>;
  }

  // ========== Family Properties ==========
  listFamilyProperties(params?: any): Observable<FamilyProperty[]> {
    return this.propertiesApi
      .chemistryFamilyPropertiesList(
        params?.mine,
        params?.ordering,
        params?.search
      )
      .pipe(
        map((result) =>
          Array.isArray(result) ? result : (result as any).results ?? []
        )
      );
  }

  getFamilyProperty(id: number): Observable<FamilyProperty> {
    return this.propertiesApi.chemistryFamilyPropertiesRetrieve(id);
  }

  createFamilyProperty(data: FamilyProperty): Observable<FamilyProperty> {
    return this.propertiesApi.chemistryFamilyPropertiesCreate(data);
  }

  updateFamilyProperty(
    id: number,
    data: Partial<FamilyProperty>
  ): Observable<FamilyProperty> {
    return (this.propertiesApi as any).chemistryFamilyPropertiesPartialUpdate?.(
      id,
      data
    );
  }

  deleteFamilyProperty(id: number): Observable<void> {
    return this.propertiesApi.chemistryFamilyPropertiesDestroy(
      id
    ) as unknown as Observable<void>;
  }
}
