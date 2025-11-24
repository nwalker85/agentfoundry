import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface GraphCodeState {
  // Graph data
  nodes: any[];
  edges: any[];
  agentName: string;

  // Generated code
  pythonCode: string;

  // Validation
  isValid: boolean;
  errors: string[];

  // Actions
  setGraphData: (nodes: any[], edges: any[], agentName: string) => void;
  setCode: (code: string, isValid: boolean, errors: string[]) => void;
  clear: () => void;
}

export const useGraphCodeStore = create<GraphCodeState>()(
  devtools(
    (set) => ({
      // Initial state
      nodes: [],
      edges: [],
      agentName: '',
      pythonCode: '',
      isValid: true,
      errors: [],

      // Actions
      setGraphData: (nodes, edges, agentName) => {
        set({ nodes, edges, agentName });
      },

      setCode: (pythonCode, isValid, errors) => {
        set({ pythonCode, isValid, errors });
      },

      clear: () => {
        set({
          nodes: [],
          edges: [],
          agentName: '',
          pythonCode: '',
          isValid: true,
          errors: [],
        });
      },
    }),
    { name: 'graph-code-store' }
  )
);
