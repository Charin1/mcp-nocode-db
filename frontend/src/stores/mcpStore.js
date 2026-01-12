import { create } from 'zustand';
import apiClient from 'api/apiClient';
import { toast } from 'react-toastify';

export const useMcpStore = create((set, get) => ({
    connections: [],
    isLoading: false,
    activeConnectionIds: [], // IDs of connections enabled for the current chat

    fetchConnections: async () => {
        set({ isLoading: true });
        try {
            const response = await apiClient.get('/api/mcp-connections');
            set({ connections: response.data });
        } catch (error) {
            console.error("Failed to fetch MCP connections", error);
            toast.error("Failed to fetch MCP connections.");
        } finally {
            set({ isLoading: false });
        }
    },

    addConnection: async (connectionData) => {
        try {
            const response = await apiClient.post('/api/mcp-connections', connectionData);
            set((state) => ({ connections: [...state.connections, response.data] }));
            toast.success("MCP Connection added successfully.");
            return true;
        } catch (error) {
            console.error("Failed to add MCP connection", error);
            toast.error("Failed to add MCP connection. Ensure the URL is reachable.");
            return false;
        }
    },

    deleteConnection: async (id) => {
        try {
            await apiClient.delete(`/api/mcp-connections/${id}`);
            set((state) => ({
                connections: state.connections.filter((c) => c.id !== id),
                activeConnectionIds: state.activeConnectionIds.filter((cid) => cid !== id)
            }));
            toast.success("MCP Connection deleted.");
        } catch (error) {
            console.error("Failed to delete MCP connection", error);
            toast.error("Failed to delete MCP connection.");
        }
    },

    toggleActiveConnection: (id) => {
        set((state) => {
            const isActive = state.activeConnectionIds.includes(id);
            if (isActive) {
                return { activeConnectionIds: state.activeConnectionIds.filter((cid) => cid !== id) };
            } else {
                return { activeConnectionIds: [...state.activeConnectionIds, id] };
            }
        });
    },

    clearActiveConnections: () => set({ activeConnectionIds: [] }),
}));
