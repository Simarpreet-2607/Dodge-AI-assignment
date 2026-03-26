export type NodeType = 'customer' | 'product' | 'order' | 'delivery' | 'invoice' | 'payment';

export interface GraphNodeData {
  id: string | number;
  [key: string]: any;
}

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  data: GraphNodeData;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  node_count: number;
  edge_count: number;
}

export interface ConnectedNode {
  id: string;
  type: string;
  label: string;
}

export interface NodeDetail {
  id: string;
  type: string;
  label: string;
  properties: Record<string, any>;
  connected_nodes: ConnectedNode[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  isError?: boolean;
}

export interface QueryResponse {
  answer: string;
  sql_query?: string;
  raw_results?: any[];
  highlighted_nodes?: string[];
  is_data_query: boolean;
  error?: string;
}
