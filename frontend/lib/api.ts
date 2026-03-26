import { GraphData, NodeDetail, QueryResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiClient {
  /**
   * Fetch full graph data.
   */
  static async getGraph(): Promise<GraphData> {
    const res = await fetch(`${API_BASE_URL}/graph`);
    if (!res.ok) {
      throw new Error(`Failed to fetch graph: ${res.statusText}`);
    }
    return res.json();
  }

  /**
   * Refresh graph from latest database state.
   */
  static async refreshGraph(): Promise<GraphData> {
    const res = await fetch(`${API_BASE_URL}/graph/refresh`);
    if (!res.ok) {
      throw new Error(`Failed to refresh graph: ${res.statusText}`);
    }
    return res.json();
  }

  /**
   * Fetch specific node details by type and ID.
   * Node parameter ID is expected to be raw identifier (e.g. integer),
   * but the frontend will usually provide the typed identifier (e.g. 'order_1').
   * So we split it.
   */
  static async getNodeDetails(nodeIdStr: string): Promise<NodeDetail> {
    const parts = nodeIdStr.split('_');
    if (parts.length < 2) {
      throw new Error(`Invalid node ID: ${nodeIdStr}`);
    }
    const type = parts[0];
    const id = parts[1];
    const res = await fetch(`${API_BASE_URL}/node/${type}/${id}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch node details: ${res.statusText}`);
    }
    return res.json();
  }

  /**
   * Submit a natural language query and get results, SQL, and highlighted nodes.
   */
  static async postQuery(question: string, chatHistory: any[] = []): Promise<QueryResponse> {
    const res = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question, chat_history: chatHistory }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => null);
      throw new Error(errorData?.detail || `Query failed: ${res.statusText}`);
    }
    return res.json();
  }
}
