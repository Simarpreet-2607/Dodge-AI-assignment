import { useEffect, useState } from "react";
import { NodeDetail } from "@/types";
import { ApiClient } from "@/lib/api";

interface NodeDetailsProps {
  nodeId: string | null;
  onClose: () => void;
}

export default function NodeDetails({ nodeId, onClose }: NodeDetailsProps) {
  const [details, setDetails] = useState<NodeDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!nodeId) {
      setDetails(null);
      return;
    }

    const fetchDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await ApiClient.getNodeDetails(nodeId);
        setDetails(data);
      } catch (err: any) {
        setError(err.message || "Failed to fetch node details");
        setDetails(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [nodeId]);

  if (!nodeId) return null;

  return (
    <div style={{
      position: "absolute",
      top: "20px",
      right: "20px",
      width: "320px",
      maxHeight: "80vh",
      background: "var(--panel-bg)",
      border: "1px solid var(--panel-border)",
      borderRadius: "12px",
      boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
      display: "flex",
      flexDirection: "column",
      zIndex: 50,
      overflow: "hidden"
    }}>
      <div style={{ 
        padding: "16px", 
        borderBottom: "1px solid var(--panel-border)", 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center",
        background: details ? `var(--node-${details.type})` : "var(--panel-bg)",
        color: details ? "#ffffff" : "inherit"
      }}>
        <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "600" }}>
          {loading ? "Loading..." : details?.label || "Node Details"}
        </h3>
        <button 
          onClick={onClose}
          style={{ 
            background: "transparent", 
            border: "none", 
            color: "inherit", 
            cursor: "pointer", 
            fontSize: "20px",
            lineHeight: 1,
            opacity: 0.8
          }}
        >×</button>
      </div>

      <div style={{ padding: "16px", overflowY: "auto", flex: 1 }}>
        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "20px" }}>
            <div className="spinner"></div>
          </div>
        ) : error ? (
          <div style={{ color: "#ef4444", fontSize: "14px" }}>{error}</div>
        ) : details ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            
            {/* Properties */}
            <div>
              <h4 style={{ fontSize: "12px", textTransform: "uppercase", color: "#94a3b8", marginBottom: "8px", letterSpacing: "0.05em" }}>Properties</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {Object.entries(details.properties).map(([key, value]) => (
                  <div key={key} style={{ display: "flex", flexDirection: "column" }}>
                    <span style={{ fontSize: "11px", color: "#94a3b8" }}>{key}</span>
                    <span style={{ fontSize: "14px", wordBreak: "break-word" }}>{value !== null && value !== undefined && value !== 'None' ? value.toString() : <span style={{ color: '#475569', fontStyle: 'italic' }}>null</span>}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Connections */}
            {details.connected_nodes.length > 0 && (
              <div>
                <h4 style={{ fontSize: "12px", textTransform: "uppercase", color: "#94a3b8", marginBottom: "8px", letterSpacing: "0.05em" }}>Connections</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {details.connected_nodes.map((node, i) => (
                    <div key={i} style={{ 
                      fontSize: "13px", 
                      padding: "6px 8px", 
                      background: "rgba(255,255,255,0.05)", 
                      borderRadius: "4px",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px"
                    }}>
                      <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: `var(--node-${node.type})` }}></div>
                      {node.label}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
          </div>
        ) : null}
      </div>
    </div>
  );
}
