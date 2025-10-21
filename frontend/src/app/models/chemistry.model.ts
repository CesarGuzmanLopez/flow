export interface Molecule {
  id: number;
  name: string;
  formula?: string;
  smiles?: string;
  inchi?: string;
  molecular_weight?: number;
  properties: Record<string, any>;
  created_at: string;
  created_by: number;
}

export interface Reaction {
  id: number;
  name: string;
  description?: string;
  reaction_type: string;
  reactants: MoleculeRef[];
  products: MoleculeRef[];
  conditions: Record<string, any>;
  yield_percentage?: number;
  created_at: string;
  created_by: number;
}

export interface MoleculeRef {
  molecule: number;
  stoichiometry: number;
  role: 'reactant' | 'product' | 'catalyst' | 'solvent';
}

export interface Protocol {
  id: number;
  name: string;
  description?: string;
  protocol_type: string;
  steps: ProtocolStep[];
  equipment: string[];
  safety_notes?: string;
  created_at: string;
  created_by: number;
}

export interface ProtocolStep {
  order: number;
  instruction: string;
  duration?: number;
  temperature?: number;
  parameters: Record<string, any>;
}
