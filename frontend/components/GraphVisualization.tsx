"use client";

import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import cola from 'cytoscape-cola';
import { GraphData } from '@/types';

// Register cola layout
if (typeof window !== 'undefined') {
  cytoscape.use(cola);
}

interface GraphVisualizationProps {
  data: GraphData | null;
  onNodeSelect: (nodeId: string) => void;
  highlightedNodes?: string[];
}

export default function GraphVisualization({ data, onNodeSelect, highlightedNodes = [] }: GraphVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || !data) return;

    // Convert API data to cytoscape elements
    const elements = [
      ...data.nodes.map((node) => {
        // node.data contains the DB 'id', which will overwrite the cytoscape string ID if spread naively
        const { id: dbId, ...restData } = node.data || {};
        return {
          data: {
            id: node.id,
            label: node.label,
            type: node.type,
            dbId: dbId,
            ...restData
          }
        };
      }),
      ...data.edges.map((edge, index) => ({
        data: {
          id: `e${index}`,
          source: edge.source,
          target: edge.target,
          label: edge.label
        }
      }))
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'font-size': '12px',
            'color': '#f8fafc',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-outline-width': 2,
            'text-outline-color': '#1e293b',
            'background-color': (ele) => {
              const type = ele.data('type');
              const colors: Record<string, string> = {
                customer: '#6366f1',
                product: '#f59e0b',
                order: '#10b981',
                delivery: '#3b82f6',
                invoice: '#8b5cf6',
                payment: '#ec4899'
              };
              return colors[type as string] || '#94a3b8';
            },
            'width': 60,
            'height': 60,
            'border-width': 2,
            'border-color': '#0f172a',
            'transition-property': 'background-color, border-color, width, height, text-outline-color',
            'transition-duration': 200
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#475569',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'color': '#94a3b8',
            'text-background-opacity': 1,
            'text-background-color': '#0f172a',
            'text-background-padding': '2px',
            'text-background-shape': 'roundrectangle'
          }
        },
        // Highlighted state from search
        {
          selector: '.highlighted',
          style: {
            'border-width': 4,
            'border-color': '#ffffff',
            'width': 70,
            'height': 70,
            'z-index': 100
          }
        },
        // Faded state (for non-highlighted nodes during search)
        {
          selector: '.faded',
          style: {
            'opacity': 0.3
          }
        },
        // Selected state (clicked)
        {
          selector: ':selected',
          style: {
            'border-width': 4,
            'border-color': '#3b82f6',
            'width': 75,
            'height': 75,
            'text-outline-color': '#3b82f6',
          }
        }
      ],
      layout: {
        name: 'cola',
        maxSimulationTime: 3000,
        nodeSpacing: 50,
        edgeLength: 150,
        fit: true,
        padding: 30,
        randomize: false,
        animate: true,
        refresh: 1
      }
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      onNodeSelect(node.id());
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        // Clicked on background
        onNodeSelect('');
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [data, onNodeSelect]);

  // Handle highlighting when highlightedNodes prop changes
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.elements().removeClass('highlighted faded');

    if (highlightedNodes && highlightedNodes.length > 0) {
      const highlightedEles = cy.collection();
      
      highlightedNodes.forEach(id => {
        const node = cy.getElementById(id);
        if (node.length > 0) {
          highlightedEles.merge(node);
          // Highlight connected edges slightly too
          highlightedEles.merge(node.connectedEdges());
        }
      });

      if (highlightedEles.length > 0) {
        highlightedEles.addClass('highlighted');
        cy.elements().difference(highlightedEles).addClass('faded');
        
        // Fit view to highlighted nodes
        cy.animate({
          fit: {
            eles: highlightedEles,
            padding: 50
          },
          duration: 500
        });
      }
    } else {
      // Fit to all if no highlights
      cy.animate({
        fit: {
          eles: cy.elements(),
          padding: 30
        },
        duration: 500
      });
    }
  }, [highlightedNodes]);

  return (
    <div id="cy-container" style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      {/* Legend */}
      <div style={{ position: 'absolute', bottom: 20, left: 20, background: 'var(--panel-bg)', padding: '10px 15px', borderRadius: '8px', border: '1px solid var(--panel-border)', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <h4 style={{ fontSize: '12px', fontWeight: 'bold', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Node Types</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', fontSize: '12px' }}>
          {[
            { type: 'customer', label: 'Customer', color: 'var(--node-customer)' },
            { type: 'product', label: 'Product', color: 'var(--node-product)' },
            { type: 'order', label: 'Order', color: 'var(--node-order)' },
            { type: 'delivery', label: 'Delivery', color: 'var(--node-delivery)' },
            { type: 'invoice', label: 'Invoice', color: 'var(--node-invoice)' },
            { type: 'payment', label: 'Payment', color: 'var(--node-payment)' },
          ].map(item => (
            <div key={item.type} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: item.color }}></div>
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
