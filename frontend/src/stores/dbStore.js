import { create } from 'zustand';
import apiClient from 'api/apiClient';
import { toast } from 'react-toastify';

export const useDbStore = create((set, get) => ({
  databases: [],
  llmProviders: [],
  selectedDbId: null,
  selectedLlmProvider: 'gemini',
  schema: [],
  isLoadingSchema: false,
  queryResult: null,
  isQuerying: false,
  generatedQuery: null,
  isGenerating: false,

  fetchAppConfig: async () => {
    try {
      const response = await apiClient.get('/api/config');
      const { databases, llm_providers } = response.data;
      set({ databases, llmProviders: llm_providers });
      if (databases.length > 0 && !get().selectedDbId) {
        const initialDbId = databases[0].id;
        set({ selectedDbId: initialDbId });
        get().fetchSchema(initialDbId); // Fetch schema for the default DB
      }
      if (llm_providers.length > 0) {
        set({ selectedLlmProvider: llm_providers[0] });
      }
    } catch (error) {
      toast.error("Failed to fetch app configuration.");
    }
  },

  setSelectedDbId: (dbId) => {
    set({ selectedDbId: dbId, schema: [], queryResult: null, generatedQuery: null });
    get().fetchSchema();
  },

  setSelectedLlmProvider: (provider) => set({ selectedLlmProvider: provider }),

  fetchSchema: async (dbId = null) => {
    const finalDbId = dbId || get().selectedDbId;
    if (!finalDbId) return;
    set({ isLoadingSchema: true, schema: [] });
    try {
      const response = await apiClient.get(`/api/schema/${finalDbId}`);
      set({ schema: response.data });
    } catch (error) {
      toast.error(`Failed to fetch schema for ${finalDbId}.`);
    } finally {
      set({ isLoadingSchema: false });
    }
  },

  generateQuery: async (natural_language_query) => {
    if (!get().selectedDbId) {
      toast.warn("Please select a database first.");
      return;
    }
    set({ isGenerating: true, generatedQuery: null });
    try {
      const response = await apiClient.post('/api/query/generate', {
        db_id: get().selectedDbId,
        model_provider: get().selectedLlmProvider,
        natural_language_query,
      });
      set({ generatedQuery: response.data });
      if (response.data.error) {
        toast.error(response.data.error);
      }
    } catch (error) {
      toast.error("Failed to generate query.");
    } finally {
      set({ isGenerating: false });
    }
  },

  executeQuery: async (rawQuery, nlQuery = "") => {
    if (!get().selectedDbId) {
      toast.warn("Please select a database first.");
      return;
    }
    set({ isQuerying: true, queryResult: null });
    try {
      const response = await apiClient.post('/api/query/execute', {
        db_id: get().selectedDbId,
        model_provider: get().selectedLlmProvider,
        raw_query: rawQuery,
        natural_language_query: nlQuery,
        confirm_execute: true,
      });
      set({ queryResult: response.data });
       if (response.data.error) {
        toast.error(response.data.error);
      } else {
        toast.success("Query executed successfully!");
      }
    } catch (error) {
      if (error.response && error.response.status === 422) {
          toast.error("Unprocessable Content: The request from the UI is missing required data.");
          console.error("422 Error Detail:", error.response.data.detail);
      } else {
          toast.error("Failed to execute query.");
      }
    } finally {
      set({ isQuerying: false });
    }
  },
}));