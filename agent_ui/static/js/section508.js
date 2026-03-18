/**
 * Section 508 Accessibility Mode
 * Handles Section 508 mode toggle and accessibility features
 */

(function() {
    'use strict';
    
    // Get API base
    function apiBase() {
        return (window.REALTYIQ_API_BASE != null ? window.REALTYIQ_API_BASE : "") || "";
    }
    
    // Get CSRF token
    function getCsrfToken() {
        var el = document.querySelector("[name=csrfmiddlewaretoken]");
        return (window.CSRF_TOKEN != null ? window.CSRF_TOKEN : "") || (el ? el.value : "") || "";
    }
    
    /**
     * Fetch current Section 508 status from server
     */
    window.fetchSection508Status = async function() {
        try {
            const response = await fetch(apiBase() + '/api/section508/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                const data = await response.json();
                window.SECTION_508_ENABLED = data.section_508_enabled;
                applySection508Mode(data.section_508_enabled);
                return data;
            }
        } catch (error) {
            console.error('Error fetching Section 508 status:', error);
        }
        return null;
    };
    
    /**
     * Update Section 508 status on server
     */
    window.updateSection508Status = async function(enabled) {
        try {
            const response = await fetch(apiBase() + '/api/section508/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify({ enabled: enabled })
            });
            
            if (response.ok) {
                const data = await response.json();
                window.SECTION_508_ENABLED = data.section_508_enabled;
                applySection508Mode(data.section_508_enabled);
                return data;
            }
        } catch (error) {
            console.error('Error updating Section 508 status:', error);
        }
        return null;
    };
    
    /**
     * Apply or remove Section 508 mode styling
     */
    function applySection508Mode(enabled) {
        if (enabled) {
            document.body.classList.add('section-508-mode');
            document.documentElement.setAttribute('data-accessibility', 'enabled');
            
            // Add ARIA live region if it doesn't exist
            if (!document.getElementById('aria-live-region')) {
                const liveRegion = document.createElement('div');
                liveRegion.id = 'aria-live-region';
                liveRegion.setAttribute('aria-live', 'polite');
                liveRegion.setAttribute('aria-atomic', 'true');
                liveRegion.style.position = 'absolute';
                liveRegion.style.left = '-10000px';
                liveRegion.style.width = '1px';
                liveRegion.style.height = '1px';
                liveRegion.style.overflow = 'hidden';
                document.body.appendChild(liveRegion);
            }
        } else {
            document.body.classList.remove('section-508-mode');
            document.documentElement.removeAttribute('data-accessibility');
            
            // Remove ARIA live region
            const liveRegion = document.getElementById('aria-live-region');
            if (liveRegion) {
                liveRegion.remove();
            }
        }
    }
    
    /**
     * Announce message to screen readers
     */
    window.announceToScreenReader = function(message) {
        if (!window.SECTION_508_ENABLED) return;
        
        const liveRegion = document.getElementById('aria-live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
            
            // Clear after a delay
            setTimeout(function() {
                liveRegion.textContent = '';
            }, 1000);
        }
    };
    
    // Export as global functions
    window.toggleSection508 = function(enabled) {
        window.SECTION_508_ENABLED = enabled;
        applySection508Mode(enabled);
    };
    
    window.getSection508Status = function() {
        return window.SECTION_508_ENABLED || false;
    };
    
    // Initialize on page load if not already set by server
    if (typeof window.SECTION_508_ENABLED === 'undefined') {
        window.SECTION_508_ENABLED = false;
    }
    
    applySection508Mode(window.SECTION_508_ENABLED);
    
})();
