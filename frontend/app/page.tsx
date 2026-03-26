"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { GraphData } from "@/types";
import { ApiClient } from "@/lib/api";
import LoadingSpinner from "@/components/LoadingSpinner";
import ChatPanel from "@/components/ChatPanel";
import NodeDetails from "@/components/NodeDetails";

const GraphVisualization = dynamic(() => import("@/components/GraphVisualization"), {
  ssr: false,
  loading: () => <LoadingSpinner />
});

export default function Home() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [highlightedNodes, setHighlightedNodes] = useState<string[]>([]);

  useEffect(() => {
    const loadGraph = async () => {
      try {
        const data = await ApiClient.getGraph();
        setGraphData(data);
      } catch (err: any) {
        setError(err.message || "Failed to load graph data");
      } finally {
        setLoading(false);
      }
    };

    loadGraph();
  }, []);

  return (
    <div style={{ display: "flex", width: "100%", height: "100%", overflow: "hidden" }}>
      
      {/* Left Area - Graph */}
      <div style={{ flex: "1 1 auto", position: "relative", background: "var(--background)" }}>
        
        {/* Header / Top Bar */}
        <div style={{ 
          position: "absolute", 
          top: 0, 
          left: 0, 
          right: 0, 
          padding: "16px 24px", 
          zIndex: 10,
          background: "linear-gradient(to bottom, rgba(15, 23, 42, 0.9) 0%, rgba(15, 23, 42, 0) 100%)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <div>
            <h1 style={{ fontSize: "20px", fontWeight: "bold", margin: 0, background: "linear-gradient(90deg, #3b82f6, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Graph-Based Data Query System
            </h1>
            <p style={{ margin: "4px 0 0 0", color: "#94a3b8", fontSize: "14px" }}>
              Explore data visually or query via natural language
            </p>
          </div>
          
          {graphData && (
            <div style={{ display: "flex", gap: "16px", color: "#94a3b8", fontSize: "14px", background: "rgba(30, 41, 59, 0.8)", padding: "8px 16px", borderRadius: "20px", border: "1px solid var(--panel-border)", backdropFilter: "blur(4px)" }}>
              <span><strong style={{ color: "#f8fafc" }}>{graphData.node_count}</strong> Nodes</span>
              <span><strong style={{ color: "#f8fafc" }}>{graphData.edge_count}</strong> Edges</span>
            </div>
          )}
        </div>

        {/* The Graph Canvas */}
        <div style={{ width: "100%", height: "100%" }}>
          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%", color: "#ef4444" }}>
              <p>Error: {error}</p>
            </div>
          ) : (
            <GraphVisualization 
              data={graphData} 
              onNodeSelect={(id) => setSelectedNodeId(id || null)}
              highlightedNodes={highlightedNodes}
            />
          )}
        </div>

        {/* Node Details Overlay */}
        {selectedNodeId && (
          <NodeDetails 
            nodeId={selectedNodeId} 
            onClose={() => setSelectedNodeId(null)} 
          />
        )}
      </div>

      {/* Right Area - Chat */}
      <div style={{ width: "400px", flexShrink: 0 }}>
        <ChatPanel onHighlightNodes={setHighlightedNodes} />
      </div>

    </div>
  );
}
