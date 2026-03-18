/**
 * Workflow Diagram with Live Step Highlighting
 * 
 * Handles live highlighting of workflow steps in Mermaid diagrams
 * during workflow execution.
 */

class WorkflowDiagram {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentStep = null;
        this.completedSteps = new Set();
        
        // Wait for Mermaid to render before initializing
        this.waitForMermaid();
    }
    
    /**
     * Wait for Mermaid diagram to be rendered
     */
    waitForMermaid() {
        const checkInterval = setInterval(() => {
            const svg = this.container.querySelector('svg');
            if (svg) {
                clearInterval(checkInterval);
                console.log('Mermaid diagram rendered successfully');
            }
        }, 100);
        
        // Timeout after 5 seconds
        setTimeout(() => {
            clearInterval(checkInterval);
        }, 5000);
    }
    
    /**
     * Highlight the current step being executed
     * @param {string} stepName - Name of the step to highlight
     */
    highlightStep(stepName) {
        console.log('Highlighting step:', stepName);
        this.currentStep = stepName;
        
        // Remove previous active highlights
        this.container.querySelectorAll('.node').forEach(node => {
            node.classList.remove('active');
        });
        
        // Find and highlight current step node
        const stepNode = this.findNodeByText(stepName);
        if (stepNode) {
            stepNode.classList.add('active');
            stepNode.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            console.warn('Could not find node for step:', stepName);
        }
    }
    
    /**
     * Mark step as completed
     * @param {string} stepName - Name of the step to mark complete
     */
    completeStep(stepName) {
        console.log('Completing step:', stepName);
        this.completedSteps.add(stepName);
        
        const stepNode = this.findNodeByText(stepName);
        if (stepNode) {
            stepNode.classList.remove('active');
            stepNode.classList.add('completed');
        }
    }
    
    /**
     * Reset diagram to initial state
     */
    reset() {
        console.log('Resetting diagram');
        this.currentStep = null;
        this.completedSteps.clear();
        this.container.querySelectorAll('.node').forEach(node => {
            node.classList.remove('active', 'completed');
        });
    }
    
    /**
     * Find Mermaid node by text content
     * @param {string} text - Text to search for in nodes
     * @returns {Element|null} - The matching node element or null
     */
    findNodeByText(text) {
        const nodes = this.container.querySelectorAll('.node');
        
        // Try exact match first
        for (const node of nodes) {
            if (node.textContent.trim() === text.trim()) {
                return node;
            }
        }
        
        // Try partial match (case insensitive)
        const searchText = text.toLowerCase();
        for (const node of nodes) {
            const nodeText = node.textContent.toLowerCase();
            if (nodeText.includes(searchText)) {
                return node;
            }
        }
        
        // Try matching by numbered steps (e.g., "1. Check Property" matches "Check Property")
        const cleanText = text.replace(/^\d+\.\s*/, '').toLowerCase();
        for (const node of nodes) {
            const nodeText = node.textContent.replace(/^\d+\.\s*/, '').toLowerCase();
            if (nodeText.includes(cleanText)) {
                return node;
            }
        }
        
        return null;
    }
    
    /**
     * Highlight all completed steps
     */
    highlightCompleted() {
        this.completedSteps.forEach(stepName => {
            const stepNode = this.findNodeByText(stepName);
            if (stepNode) {
                stepNode.classList.add('completed');
            }
        });
    }
}

// Add CSS for step highlighting
if (!document.getElementById('workflow-diagram-styles')) {
    const style = document.createElement('style');
    style.id = 'workflow-diagram-styles';
    style.textContent = `
        /* Active step highlight with pulsing animation */
        .mermaid-container .node.active rect,
        .mermaid-container .node.active polygon,
        .mermaid-container .node.active circle,
        .mermaid-container .node.active ellipse {
            stroke: #2196F3 !important;
            stroke-width: 3px !important;
            filter: drop-shadow(0 0 8px #2196F3);
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        .mermaid-container .node.active .nodeLabel {
            font-weight: bold !important;
        }
        
        /* Completed step styling */
        .mermaid-container .node.completed rect,
        .mermaid-container .node.completed polygon,
        .mermaid-container .node.completed circle,
        .mermaid-container .node.completed ellipse {
            opacity: 0.6;
            filter: grayscale(50%);
        }
        
        .mermaid-container .node.completed .nodeLabel {
            opacity: 0.6;
        }
        
        /* Pulse animation for active steps */
        @keyframes pulse {
            0%, 100% { 
                filter: drop-shadow(0 0 8px #2196F3); 
            }
            50% { 
                filter: drop-shadow(0 0 16px #2196F3); 
            }
        }
        
        /* Smooth transitions */
        .mermaid-container .node rect,
        .mermaid-container .node polygon,
        .mermaid-container .node circle,
        .mermaid-container .node ellipse {
            transition: opacity 0.3s ease, filter 0.3s ease;
        }
    `;
    document.head.appendChild(style);
}

// Export for use in other scripts
window.WorkflowDiagram = WorkflowDiagram;
