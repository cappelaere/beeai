/**
 * Workflow Execution with Real-Time Progress via WebSockets
 * 
 * Handles workflow form submission, WebSocket streaming, progress updates,
 * and result display with notifications.
 */

/**
 * Build input_data object from workflow form (same shape as execute payload).
 * @param {HTMLFormElement} form - The workflow form element
 * @returns {Object} inputData object for workflow execution or scheduling
 */
function getWorkflowFormInputData(form) {
    const formData = new FormData(form);
    const inputData = {};
    const registrationFields = ['email', 'phone', 'user_type', 'terms_accepted', 'age_accepted'];
    const registrationData = {};

    for (const [key, value] of formData.entries()) {
        if (key === 'csrfmiddlewaretoken') continue;

        const field = form.querySelector(`[name="${key}"]`);
        let processedValue = value;

        if (field) {
            if (field.tagName === 'TEXTAREA') {
                try {
                    processedValue = JSON.parse(value);
                } catch {
                    processedValue = value;
                }
            } else if (field.type === 'number') {
                processedValue = parseInt(value, 10);
            } else if (field.type === 'checkbox') {
                processedValue = field.checked;
            } else if (field.type === 'email' || field.tagName === 'SELECT') {
                processedValue = value;
            }
        }

        if (registrationFields.includes(key)) {
            registrationData[key] = processedValue;
        } else {
            inputData[key] = processedValue;
        }
    }

    const allCheckboxes = form.querySelectorAll('input[type="checkbox"]');
    allCheckboxes.forEach((checkbox) => {
        const name = checkbox.name;
        if (name && name !== 'csrfmiddlewaretoken') {
            if (registrationFields.includes(name)) {
                if (!(name in registrationData)) registrationData[name] = false;
            } else {
                if (!(name in inputData)) inputData[name] = false;
            }
        }
    });

    if (Object.keys(registrationData).length > 0) {
        inputData.registration_data = registrationData;
    }

    return inputData;
}

/**
 * Initialize workflow execution interface
 * @param {string} workflowId - ID of the workflow
 * @param {string} executeUrl - URL to execute the workflow
 * @param {string} exportUrl - URL to export results
 * @param {string} csrfToken - CSRF token for POST requests
 */
function initializeWorkflowExecution(workflowId, executeUrl, exportUrl, csrfToken) {
    const form = document.getElementById('workflow-form');
    const executeBtn = document.getElementById('execute-btn');
    const statusBadge = document.getElementById('status-badge');
    const progressSteps = document.getElementById('progress-steps');
    const stepsList = document.getElementById('steps-list');
    const resultsPanel = document.getElementById('results-panel');
    const resultsContent = document.getElementById('results-content');
    const exportBtn = document.getElementById('export-btn');
    
    // Initialize diagram handler
    const diagram = new WorkflowDiagram('workflow-diagram');
    
    let currentResults = null;
    /** @type {{ pendingJoinCount: number }} */
    let parallelProgressPrev = { pendingJoinCount: 0 };
    
    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Disable form during execution
        executeBtn.disabled = true;
        executeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing...';
        
        // Reset UI
        diagram.reset();
        progressSteps.style.display = 'block';
        resultsPanel.style.display = 'none';
        stepsList.innerHTML = '';
        statusBadge.className = 'status-badge status-running';
        statusBadge.textContent = 'Running';
        statusBadge.title = '';
        currentResults = null;
        parallelProgressPrev = { pendingJoinCount: 0 };

        // Collect form data (same shape as getWorkflowFormInputData)
        const inputData = getWorkflowFormInputData(form);
        console.log('Executing workflow with inputs:', inputData);
        
        // Validate date range: start_date must be before or equal to end_date
        const startDate = inputData.start_date;
        const endDate = inputData.end_date;
        if (startDate && endDate && startDate > endDate) {
            executeBtn.disabled = false;
            executeBtn.innerHTML = '<i class="fas fa-play" aria-hidden="true"></i> Execute Workflow';
            statusBadge.className = 'status-badge status-ready';
            statusBadge.textContent = 'Ready';
            progressSteps.style.display = 'none';
            showNotification('Start date must be before or equal to end date.', 'error');
            return;
        }
        
        try {
            // Make POST request to create workflow run
            const response = await fetch(executeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(inputData)
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                handleError(`Failed to start workflow: ${response.status} ${errorText}`);
                return;
            }
            
            // Get run_id and WebSocket URL
            const result = await response.json();
            if (!result.success) {
                handleError(result.error || 'Failed to create workflow run');
                return;
            }
            
            console.log('Workflow run created:', result.run_id);
            
            // Connect to WebSocket for real-time updates
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}${result.websocket_url}`;
            
            const ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
                showNotification('Workflow execution started', 'info');
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleEvent(data);
                } catch (err) {
                    console.error('Failed to parse WebSocket message:', err, event.data);
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                handleError('WebSocket connection error');
            };
            
            ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                // Connection closed - workflow may still be running
            };
            
        } catch (error) {
            console.error('Execution error:', error);
            handleError(`Network error: ${error.message}`);
        }
    });
    
    /**
     * Handle WebSocket event from server
     * @param {Object} event - Event data from server
     */
    function handleEvent(event) {
        console.log('Received event:', event);
        
        switch (event.type) {
            case 'start':
                console.log('Workflow started:', event.workflow_id);
                showNotification('Workflow execution started', 'info');
                break;
                
            case 'step':
                addStepToProgress(event.step);
                diagram.highlightStep(event.step);
                break;
                
            case 'complete':
                handleCompletion(event.result);
                break;
                
            case 'progress':
                if (event.completed_node_ids !== undefined || event.current_node_ids !== undefined) {
                    const cur = event.current_node_ids || [];
                    const es = event.engine_state || {};
                    const pj = es.pending_joins && typeof es.pending_joins === 'object' ? es.pending_joins : {};
                    const pendingKeys = Object.keys(pj);
                    const prevPending = parallelProgressPrev.pendingJoinCount || 0;
                    const retryTid = event.retrying_task_id;
                    const retryAtt = event.retry_attempt;
                    const retryMax = event.bpmn_max_task_retries;
                    const lre = es.last_retryable_error && typeof es.last_retryable_error === 'object'
                        ? es.last_retryable_error : {};
                    const retryMsg = lre.message || lre.Message || '';

                    if (statusBadge && statusBadge.classList.contains('status-running')) {
                        let label = 'Running';
                        let title = '';
                        if (retryTid) {
                            const total = retryMax != null ? Number(retryMax) + 1 : null;
                            const att = retryAtt != null ? Number(retryAtt) : null;
                            if (total != null && att != null && !Number.isNaN(total) && !Number.isNaN(att)) {
                                label = `Retrying · ${retryTid} (${att}/${total})`;
                                title = `Transient failure on task ${retryTid}; attempt ${att} of up to ${total}.${retryMsg ? ' ' + String(retryMsg) : ''}`;
                            } else {
                                label = `Retrying · ${retryTid}`;
                                title = retryMsg ? String(retryMsg) : 'Retrying after transient failure';
                            }
                        } else if (pendingKeys.length > 0) {
                            const parts = pendingKeys.map((jid) => {
                                const info = pj[jid] || {};
                                const arr = (info.arrived_branch_ids || []).length;
                                const exp = (info.expected_branch_ids || []).length;
                                return `${jid} ${arr}/${exp}`;
                            });
                            label = 'Running · at join';
                            title = `Waiting at parallel join: ${parts.join('; ')}`;
                        } else if (cur.length > 1) {
                            label = `Running · ${cur.length} branches`;
                            title = `${cur.length} parallel activities active`;
                        } else if (prevPending > 0 && pendingKeys.length === 0 && cur.length === 1) {
                            label = 'Running · merged path';
                            title = 'Branches merged at join; single path continues';
                        }
                        statusBadge.textContent = label;
                        statusBadge.title = title;
                    }
                    parallelProgressPrev = { pendingJoinCount: pendingKeys.length };

                    if (typeof window.applyBpmnProgress === 'function') {
                        window.applyBpmnProgress(
                            event.completed_node_ids || [],
                            cur,
                            event.failed_node_id || null
                        );
                    }
                }
                break;
                
            case 'error':
                handleError(event.message);
                break;
                
            case 'task_created':
                handleTaskCreated(event);
                break;

            case 'bpmn_intermediate_wait':
                if (statusBadge) {
                    statusBadge.className = 'status-badge status-waiting';
                    statusBadge.textContent =
                        event.wait_kind === 'timer' ? 'BPMN timer wait' : 'BPMN message wait';
                    statusBadge.title = event.message || '';
                }
                if (typeof showNotification === 'function') {
                    showNotification(
                        event.message || 'Workflow paused on BPMN intermediate catch',
                        'warning'
                    );
                }
                executeBtn.disabled = false;
                executeBtn.innerHTML = '<i class="fas fa-play"></i> Open run to resume';
                break;

            default:
                console.warn('Unknown event type:', event.type);
        }
    }
    
    /**
     * Add step to progress list
     * @param {string} stepName - Name of the step
     */
    function addStepToProgress(stepName) {
        const stepItem = document.createElement('div');
        stepItem.className = 'step-item';
        stepItem.innerHTML = `
            <i class="fas fa-check-circle" aria-hidden="true"></i>
            <span>${escapeHtml(stepName)}</span>
            <small>${new Date().toLocaleTimeString()}</small>
        `;
        stepsList.appendChild(stepItem);
        
        // Mark step as complete on diagram
        diagram.completeStep(stepName);
        
        // Auto-scroll to latest step
        stepsList.scrollTop = stepsList.scrollHeight;
    }
    
    /**
     * Handle workflow completion
     * @param {Object} result - Workflow result data
     */
    function handleCompletion(result) {
        console.log('Workflow completed:', result);
        
        // Mark current step as complete
        if (diagram.currentStep) {
            diagram.completeStep(diagram.currentStep);
        }
        
        // Update BPMN diagram coloring (completed nodes + flows)
        if (typeof window.applyBpmnProgressFromRun === 'function') {
            window.applyBpmnProgressFromRun(result);
        }
        
        // Update status badge
        statusBadge.className = 'status-badge status-complete';
        statusBadge.textContent = 'Complete';
        statusBadge.title = '';
        
        // Re-enable form
        executeBtn.disabled = false;
        executeBtn.innerHTML = '<i class="fas fa-play"></i> Execute Again';
        
        // Store results for export
        currentResults = result;
        
        // Show results panel
        resultsPanel.style.display = 'block';
        resultsContent.innerHTML = renderResults(result);
        
        // Show in-page notification
        showNotification('Workflow completed successfully!', 'success');
        
        // Show browser notification if permitted
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Workflow Complete', {
                body: `${workflowId} finished with status: ${result.status}`,
                icon: '/static/images/logo.png'
            });
        }
    }
    
    /**
     * Handle execution error
     * @param {string} message - Error message
     */
    function handleError(message) {
        console.error('Workflow error:', message);
        
        statusBadge.className = 'status-badge status-error';
        statusBadge.textContent = 'Error';
        statusBadge.title = '';
        
        executeBtn.disabled = false;
        executeBtn.innerHTML = '<i class="fas fa-play"></i> Try Again';
        
        showNotification(`Error: ${message}`, 'error');
    }
    
    /**
     * Handle task creation event
     * @param {Object} event - Task created event data
     */
    function handleTaskCreated(event) {
        console.log('Task created:', event);
        
        statusBadge.className = 'status-badge status-waiting';
        statusBadge.textContent = 'Waiting for Task';
        statusBadge.title = '';
        
        executeBtn.disabled = false;
        executeBtn.innerHTML = '<i class="fas fa-play"></i> Execute Again';
        
        // Show prominent in-page notification with link to the task
        const taskMessage = `⏸ Workflow paused - <a href="${event.task_url}" style="color: #fff; font-weight: bold; text-decoration: underline;">Review ${event.task_type} task</a>`;
        showNotification(taskMessage, 'warning');
        
        // Show browser notification if permitted
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification('🔔 Human Task Required', {
                body: `A ${event.task_type} task has been created and needs your attention.`,
                icon: '/static/images/logo.png',
                tag: event.task_id,
                requireInteraction: true
            });
            
            // Click notification to go to task
            notification.onclick = function() {
                window.focus();
                window.location.href = event.task_url;
            };
        }
        
        // Update task badge counter
        const badge = document.getElementById('task-badge');
        if (badge) {
            fetch('/api/tasks/count/')
                .then(response => response.json())
                .then(data => {
                    if (data.count > 0) {
                        badge.textContent = data.count;
                        badge.style.display = 'inline-block';
                    }
                })
                .catch(err => console.error('Failed to update task badge:', err));
        }
    }
    
    /**
     * Render workflow results
     * @param {Object} result - Result data
     * @returns {string} HTML string
     */
    function renderResults(result) {
        const statusClass = result.status ? result.status.toLowerCase() : 'unknown';
        
        let html = `
            <div class="result-summary ${statusClass}">
                <h4>Status: ${escapeHtml(result.status || 'UNKNOWN')}</h4>
                ${result.summary ? `<p>${escapeHtml(result.summary)}</p>` : ''}
        `;
        
        // Add eligibility badge if present
        if (result.eligible !== undefined) {
            const eligibleClass = result.eligible ? 'approved' : 'denied';
            const eligibleText = result.eligible ? '✓ Eligible' : '✗ Not Eligible';
            html += `
                <div class="eligibility-badge ${eligibleClass}">
                    ${eligibleText}
                </div>
            `;
        }
        
        html += `</div>`;
        
        // Add risk factors if present
        if (result.risk_factors && result.risk_factors.length > 0) {
            html += `
                <div class="risk-factors">
                    <h4>Risk Factors:</h4>
                    <ul>
                        ${result.risk_factors.map(rf => `<li>${escapeHtml(rf)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Add checks performed if present
        if (result.checks_performed && result.checks_performed.length > 0) {
            html += `
                <div class="checks-performed">
                    <h4>Checks Performed:</h4>
                    <ul>
                        ${result.checks_performed.map(check => {
                            // Handle both string and object formats
                            if (typeof check === 'string') {
                                return `<li>${escapeHtml(check)}</li>`;
                            } else if (typeof check === 'object' && check !== null) {
                                // Handle check object with check_type and result
                                const checkType = check.check_type || check.name || 'Unknown Check';
                                const checkResult = check.result || 'UNKNOWN';
                                const statusIcon = checkResult === 'PASS' ? '✓' : 
                                                  checkResult === 'FAIL' ? '✗' : 
                                                  checkResult === 'FLAG' ? '⚠️' : '•';
                                const resultClass = checkResult === 'PASS' ? 'check-pass' : 
                                                   checkResult === 'FAIL' ? 'check-fail' : 
                                                   'check-flag';
                                
                                let checkHtml = `<li class="${resultClass}">
                                    <strong>${escapeHtml(checkType)}</strong>: 
                                    <span class="check-result">${statusIcon} ${escapeHtml(checkResult)}</span>`;
                                
                                // Add timestamp if present
                                if (check.timestamp) {
                                    const date = new Date(check.timestamp);
                                    checkHtml += `<br><small class="check-timestamp">Checked at: ${date.toLocaleString()}</small>`;
                                }
                                
                                // Add summary details if present (don't show full nested objects)
                                if (check.details && typeof check.details === 'object') {
                                    if (check.details.matches && Array.isArray(check.details.matches) && check.details.matches.length > 0) {
                                        checkHtml += `<br><small class="check-detail">Matches found: ${check.details.matches.length}</small>`;
                                    } else if (check.details.eligible !== undefined) {
                                        checkHtml += `<br><small class="check-detail">Eligible: ${check.details.eligible ? 'Yes' : 'No'}</small>`;
                                    }
                                }
                                
                                checkHtml += `</li>`;
                                return checkHtml;
                            }
                            return '';
                        }).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Add full result details in HTML format
        html += `
            <details class="full-results">
                <summary>View Full Results</summary>
                <div class="result-details">
                    ${renderResultDetails(result, typeof window !== 'undefined' && window.workflowMetadata || null)}
                </div>
            </details>
        `;
        
        return html;
    }
    
    /**
     * Render full result details in HTML format
     * @param {Object} result - Result data
     * @param {Object} metadata - Optional workflow run metadata (e.g. workflow_id)
     * @returns {string} HTML string
     */
    function renderResultDetails(result, metadata) {
        if (metadata && metadata.workflow_id === 'bi_weekly_report') {
            return renderBiWeeklyReportResults(result);
        }
        let html = '<div class="result-table">';
        for (const [key, value] of Object.entries(result)) {
            html += `
                <div class="result-row">
                    <div class="result-key">${escapeHtml(key.replace(/_/g, ' ').toUpperCase())}:</div>
                    <div class="result-value">${formatValue(value)}</div>
                </div>
            `;
        }
        html += '</div>';
        return html;
    }
    
    /**
     * Format a value for HTML display
     * @param {*} value - Value to format
     * @returns {string} Formatted HTML
     */
    function formatValue(value) {
        if (value === null || value === undefined) {
            return '<span class="null-value">N/A</span>';
        }
        
        if (typeof value === 'boolean') {
            return value ? '<span class="bool-true">✓ Yes</span>' : '<span class="bool-false">✗ No</span>';
        }
        
        if (Array.isArray(value)) {
            if (value.length === 0) {
                return '<em>Empty list</em>';
            }
            return '<ul>' + value.map(item => `<li>${formatValue(item)}</li>`).join('') + '</ul>';
        }
        
        if (typeof value === 'object') {
            let html = '<div class="nested-object">';
            for (const [k, v] of Object.entries(value)) {
                html += `<div class="nested-row"><strong>${escapeHtml(k)}:</strong> ${formatValue(v)}</div>`;
            }
            html += '</div>';
            return html;
        }
        
        // For strings and numbers
        return escapeHtml(String(value));
    }
    
    // Export handler
    if (exportBtn) {
        // Create export dropdown menu
        const exportMenu = document.createElement('div');
        exportMenu.className = 'export-dropdown';
        exportMenu.innerHTML = `
            <button class="btn btn-secondary" id="export-toggle">
                <i class="fas fa-download" aria-hidden="true"></i> Export Results
                <i class="fas fa-chevron-down" aria-hidden="true" style="margin-left: 0.5rem; font-size: 0.8em;"></i>
            </button>
            <div class="export-menu" id="export-menu" style="display: none;">
                <button class="export-option" data-format="html">
                    <i class="fas fa-code" aria-hidden="true"></i> View as HTML
                </button>
                <button class="export-option" data-format="json">
                    <i class="fas fa-download" aria-hidden="true"></i> Download as JSON
                </button>
                <button class="export-option" data-format="markdown">
                    <i class="fas fa-download" aria-hidden="true"></i> Download as Markdown
                </button>
            </div>
        `;
        
        exportBtn.parentNode.replaceChild(exportMenu, exportBtn);
        
        const toggleBtn = document.getElementById('export-toggle');
        const menu = document.getElementById('export-menu');
        const exportOptions = exportMenu.querySelectorAll('.export-option');
        
        // Toggle dropdown
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            menu.style.display = 'none';
        });
        
        // Handle export format selection
        exportOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                const format = option.dataset.format;
                menu.style.display = 'none';
                
                if (currentResults) {
                    if (format === 'json') {
                        exportAsJSON(currentResults);
                    } else if (format === 'markdown') {
                        exportAsMarkdown(currentResults);
                    } else if (format === 'html') {
                        viewAsHTML(currentResults);
                    }
                } else {
                    showNotification('No results to export', 'error');
                }
            });
        });
    }
    
    // Request notification permission on page load
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            console.log('Notification permission:', permission);
        });
    }
}

/**
 * Show toast notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (info, success, error)
 */
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    // Use innerHTML to support HTML links in notifications
    toast.innerHTML = message;
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto-dismiss after 5 seconds (increased for task notifications)
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Get CSRF token from cookies
 * @param {string} name - Cookie name
 * @returns {string|undefined} Cookie value
 */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop().split(';').shift();
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

/**
 * Convert simple Markdown to HTML (headings, bold, lists, paragraphs)
 * @param {string} md - Markdown string
 * @returns {string} HTML string
 */
function simpleMarkdownToHtml(md) {
    if (!md || typeof md !== 'string') return '';
    const lines = md.split('\n');
    let html = '';
    let inList = false;
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        if (trimmed.startsWith('### ')) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<h3>' + escapeHtml(trimmed.slice(4)) + '</h3>';
        } else if (trimmed.startsWith('## ')) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<h2>' + escapeHtml(trimmed.slice(3)) + '</h2>';
        } else if (trimmed.startsWith('# ')) {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<h1>' + escapeHtml(trimmed.slice(2)) + '</h1>';
        } else if (trimmed.startsWith('- ')) {
            if (!inList) { html += '<ul>'; inList = true; }
            const content = escapeHtml(trimmed.slice(2)).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            html += '<li>' + content + '</li>';
        } else if (trimmed === '') {
            if (inList) { html += '</ul>'; inList = false; }
            html += '<br>';
        } else {
            if (inList) { html += '</ul>'; inList = false; }
            const content = escapeHtml(trimmed).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            html += '<p>' + content + '</p>';
        }
    }
    if (inList) html += '</ul>';
    return html;
}

/**
 * Render BI Weekly Report results as HTML (executive brief as HTML, others as tables/text)
 * @param {Object} data - workflow output_data
 * @returns {string} HTML string
 */
function renderBiWeeklyReportResults(data) {
    let html = '<div class="bi-weekly-report-results">';
    if (data.executive_brief_markdown) {
        html += '<section class="bi-section bi-executive-brief"><h2>Executive Brief</h2>';
        html += '<div class="bi-brief-html">' + simpleMarkdownToHtml(data.executive_brief_markdown) + '</div></section>';
    }
    if (data.portfolio_totals && Object.keys(data.portfolio_totals).length > 0) {
        html += '<section class="bi-section"><h2>Portfolio Totals</h2><table class="bi-table"><tbody>';
        for (const [k, v] of Object.entries(data.portfolio_totals)) {
            html += '<tr><th>' + escapeHtml(String(k).replace(/_/g, ' ')) + '</th><td>' + escapeHtml(String(v)) + '</td></tr>';
        }
        html += '</tbody></table></section>';
    }
    if (data.top_performers && data.top_performers.length > 0) {
        html += '<section class="bi-section"><h2>Top Performers</h2><table class="bi-table"><thead><tr>';
        const keys = Object.keys(data.top_performers[0]);
        keys.forEach(k => { html += '<th>' + escapeHtml(String(k).replace(/_/g, ' ')) + '</th>'; });
        html += '</tr></thead><tbody>';
        data.top_performers.forEach(row => {
            html += '<tr>';
            keys.forEach(k => { html += '<td>' + escapeHtml(String(row[k] != null ? row[k] : '')) + '</td>'; });
            html += '</tr>';
        });
        html += '</tbody></table></section>';
    }
    if (data.properties_needing_attention && data.properties_needing_attention.length > 0) {
        html += '<section class="bi-section"><h2>Properties Needing Attention</h2><table class="bi-table"><thead><tr>';
        const keys = Object.keys(data.properties_needing_attention[0]);
        keys.forEach(k => { html += '<th>' + escapeHtml(String(k).replace(/_/g, ' ')) + '</th>'; });
        html += '</tr></thead><tbody>';
        data.properties_needing_attention.forEach(row => {
            html += '<tr>';
            keys.forEach(k => { html += '<td>' + escapeHtml(String(row[k] != null ? row[k] : '')) + '</td>'; });
            html += '</tr>';
        });
        html += '</tbody></table></section>';
    }
    if (data.funnel && Object.keys(data.funnel).length > 0) {
        html += '<section class="bi-section"><h2>Conversion Funnel</h2><table class="bi-table"><tbody>';
        for (const [k, v] of Object.entries(data.funnel)) {
            html += '<tr><th>' + escapeHtml(String(k).replace(/_/g, ' ')) + '</th><td>' + escapeHtml(String(v)) + '</td></tr>';
        }
        html += '</tbody></table></section>';
    }
    if (data.week_over_week_trend && Object.keys(data.week_over_week_trend).length > 0) {
        html += '<section class="bi-section"><h2>Week-over-Week Trend</h2>';
        const w = data.week_over_week_trend;
        if (w.pct_change) {
            html += '<table class="bi-table"><tbody>';
            for (const [k, v] of Object.entries(w.pct_change)) {
                html += '<tr><th>' + escapeHtml(String(k).replace(/_/g, ' ')) + '</th><td>' + escapeHtml(String(v)) + '%</td></tr>';
            }
            html += '</tbody></table>';
        } else if (w.error) {
            html += '<p>' + escapeHtml(w.error) + '</p>';
        } else {
            html += '<pre>' + escapeHtml(JSON.stringify(w, null, 2)) + '</pre>';
        }
        html += '</section>';
    }
    if (data.auction_readiness && data.auction_readiness.length > 0) {
        html += '<section class="bi-section"><h2>Auction Readiness</h2><table class="bi-table"><thead><tr>';
        const keys = Object.keys(data.auction_readiness[0]);
        keys.forEach(k => { html += '<th>' + escapeHtml(String(k).replace(/_/g, ' ')) + '</th>'; });
        html += '</tr></thead><tbody>';
        data.auction_readiness.forEach(row => {
            html += '<tr>';
            keys.forEach(k => { html += '<td>' + escapeHtml(String(row[k] != null ? row[k] : '')) + '</td>'; });
            html += '</tr>';
        });
        html += '</tbody></table></section>';
    }
    if (data.recommended_actions && data.recommended_actions.length > 0) {
        html += '<section class="bi-section"><h2>Recommended Actions</h2><ul class="bi-actions">';
        data.recommended_actions.forEach(a => { html += '<li>' + escapeHtml(a) + '</li>'; });
        html += '</ul></section>';
    }
    if (data.workflow_steps && data.workflow_steps.length > 0) {
        html += '<section class="bi-section"><h2>Workflow Steps</h2><ol>';
        data.workflow_steps.forEach(s => { html += '<li>' + escapeHtml(s) + '</li>'; });
        html += '</ol></section>';
    }
    html += '</div>';
    return html;
}

// Add CSS for toast notifications
if (!document.getElementById('workflow-toast-styles')) {
    const style = document.createElement('style');
    style.id = 'workflow-toast-styles';
    style.textContent = `
        /* Toast Notifications */
        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            padding: 1rem 1.5rem;
            border-radius: 4px;
            color: white;
            font-weight: 500;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            max-width: 400px;
        }
        
        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }
        
        .toast-info { 
            background: #2196f3; 
        }
        
        .toast-success { 
            background: #4caf50; 
        }
        
        .toast-error { 
            background: #f44336; 
        }
        
        .toast-warning { 
            background: #ff9800;
            font-size: 1.05rem;
            padding: 1.25rem 1.75rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        
        .toast-warning a {
            color: #fff;
            font-weight: bold;
            text-decoration: underline;
        }
        
        .toast-warning a:hover {
            color: #ffe0b2;
        }
        
        @media (max-width: 768px) {
            .toast {
                bottom: 1rem;
                right: 1rem;
                left: 1rem;
                max-width: none;
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Global export functions (accessible from run_detail.html)
 */

/**
 * View results as formatted HTML in a new browser tab
 * @param {Object} results - Results to view
 */
function viewAsHTML(results) {
    const htmlContent = generateHTMLExport(results);
    
    // Open in new window/tab
    const newWindow = window.open('', '_blank');
    if (newWindow) {
        newWindow.document.write(htmlContent);
        newWindow.document.close();
        showNotification('Results opened in new tab', 'success');
    } else {
        alert('Please allow popups to view HTML results');
    }
}

/**
 * Format date for export (MM/DD/YYYY, HH:mm:ss) - consistent across locales
 * @param {Date|string} d - Date to format
 * @returns {string} Formatted date string
 */
function formatExportDate(d) {
    const date = d instanceof Date ? d : new Date(d);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

/**
 * Generate standalone HTML export
 * @param {Object} results - Results to convert
 * @returns {string} HTML document string
 */
function generateHTMLExport(results, metadata = {}) {
    const timestamp = formatExportDate(new Date());
    const workflowName = metadata.workflow_name || results.workflow_name || 'Workflow';
    
    let html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workflow Results - ${workflowName}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #f8f9fa;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 { color: #1565c0; border-bottom: 3px solid #2196f3; padding-bottom: 0.5rem; }
        h2 { color: #01579b; margin-top: 2rem; }
        h3 { color: #263238; margin-top: 1.5rem; }
        .status-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: 600;
            margin: 1rem 0;
        }
        .status-approved { background: #4caf50; color: white; }
        .status-denied { background: #f44336; color: white; }
        .status-review { background: #ff9800; color: white; }
        .meta { color: #666; font-size: 0.9rem; margin-bottom: 2rem; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            background: #f5f5f5;
            font-weight: 600;
            color: #555;
        }
        tr:hover {
            background: #f9f9f9;
        }
        .check-pass { color: #4caf50; }
        .check-fail { color: #f44336; }
        .check-flag { color: #ff9800; }
        ul { padding-left: 1.5rem; }
        li { margin: 0.5rem 0; }
        code {
            background: #f5f5f5;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: monospace;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ ${escapeHtml(workflowName)}</h1>
        
        <!-- Workflow Metadata -->
        <div style="background: #f8f9fa; border-radius: 4px; padding: 1rem; margin-bottom: 2rem;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <th style="text-align: left; padding: 0.5rem; width: 200px; font-weight: 600;">Run ID</th>
                    <td style="padding: 0.5rem;"><code>${metadata.run_id || 'N/A'}</code></td>
                </tr>
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <th style="text-align: left; padding: 0.5rem; font-weight: 600;">Workflow ID</th>
                    <td style="padding: 0.5rem;"><code>${metadata.workflow_id || 'N/A'}</code></td>
                </tr>
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <th style="text-align: left; padding: 0.5rem; font-weight: 600;">Initiated By</th>
                    <td style="padding: 0.5rem;"><code>User ${metadata.user_id || 'N/A'}</code></td>
                </tr>
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <th style="text-align: left; padding: 0.5rem; font-weight: 600;">Status</th>
                    <td style="padding: 0.5rem;">${metadata.status || 'completed'}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <th style="text-align: left; padding: 0.5rem; font-weight: 600;">Started</th>
                    <td style="padding: 0.5rem;">${metadata.started_at || 'N/A'}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <th style="text-align: left; padding: 0.5rem; font-weight: 600;">Completed</th>
                    <td style="padding: 0.5rem;">${metadata.completed_at || 'N/A'}</td>
                </tr>
                <tr>
                    <th style="text-align: left; padding: 0.5rem; font-weight: 600;">Duration</th>
                    <td style="padding: 0.5rem;">${metadata.duration ? metadata.duration.toFixed(2) + 's' : 'N/A'}</td>
                </tr>
            </table>
        </div>
        
        <p class="meta">Exported: ${timestamp}</p>
        
        <!-- Task Approvals Section -->
`;
    
    // Add task approvals if available
    if (metadata.tasks && Array.isArray(metadata.tasks) && metadata.tasks.length > 0) {
        html += `<h2>Task Approvals</h2>\n<table>\n`;
        html += `<thead><tr><th>Task</th><th>Type</th><th>Status</th><th>Completed By</th><th>Completed At</th></tr></thead>\n<tbody>\n`;
        
        metadata.tasks.forEach(task => {
            const taskTitle = escapeHtml(task.title || 'Untitled Task');
            const taskType = escapeHtml(task.task_type || 'N/A');
            const status = escapeHtml(task.status || 'N/A');
            const completedBy = task.completed_by_user_id ? `User ${task.completed_by_user_id}` : 'N/A';
            const completedAt = task.completed_at ? formatExportDate(task.completed_at) : 'N/A';
            
            const statusColor = task.status === 'completed' ? 'color: #4caf50;' : 
                               task.status === 'in_progress' ? 'color: #ff9800;' : 
                               'color: #666;';
            
            html += `<tr>
                <td><strong>${taskTitle}</strong></td>
                <td>${taskType}</td>
                <td style="${statusColor}">${status}</td>
                <td><code>${completedBy}</code></td>
                <td><small>${completedAt}</small></td>
            </tr>\n`;
        });
        
        html += `</tbody>\n</table>\n`;
    }
    
    html += `        
        <h2>Results</h2>
`;
    
    if (metadata.workflow_id === 'bi_weekly_report') {
        html += renderBiWeeklyReportResults(results);
    } else {
    // Status
    if (results.status) {
        const statusClass = results.status.toLowerCase();
        html += `<div class="status-badge status-${statusClass}">${escapeHtml(results.status)}</div>\n`;
    }
    
    // Summary
    if (results.summary) {
        // Replace newlines with <br> tags for proper formatting
        const formattedSummary = escapeHtml(results.summary).replace(/\n/g, '<br>\n');
        html += `<h2>Summary</h2>\n<div style="white-space: pre-wrap;">${formattedSummary}</div>\n`;
    }
    
    // Findings summary (for property due diligence)
    if (results.findings_summary) {
        html += `<h2>Findings</h2>\n<pre>${escapeHtml(results.findings_summary)}</pre>\n`;
    }
    
    // Eligibility
    if (results.eligible !== undefined) {
        html += `<h2>Eligibility</h2>\n`;
        html += results.eligible ? '<p class="check-pass">✓ <strong>Eligible</strong></p>\n' : '<p class="check-fail">✗ <strong>Not Eligible</strong></p>\n';
    }
    
    // Risk Factors
    if (results.risk_factors && results.risk_factors.length > 0) {
        html += `<h2>Risk Factors</h2>\n<ul>\n`;
        results.risk_factors.forEach(rf => {
            html += `<li>${escapeHtml(rf)}</li>\n`;
        });
        html += `</ul>\n`;
    }
    
    // Recommendations (for property due diligence)
    if (results.recommendations && results.recommendations.length > 0) {
        html += `<h2>Recommendations</h2>\n<ul>\n`;
        results.recommendations.forEach(rec => {
            html += `<li>${escapeHtml(rec)}</li>\n`;
        });
        html += `</ul>\n`;
    }
    
    // Checks Performed
    if (results.checks_performed && results.checks_performed.length > 0) {
        html += `<h2>Checks Performed</h2>\n<table>\n`;
        html += `<thead><tr><th>Check Type</th><th>Result</th><th>Timestamp</th></tr></thead>\n<tbody>\n`;
        results.checks_performed.forEach(check => {
            if (typeof check === 'object' && check !== null) {
                const checkType = check.check_type || 'Unknown';
                const result = check.result || 'UNKNOWN';
                const timestamp = check.timestamp ? new Date(check.timestamp).toLocaleString() : 'N/A';
                const statusIcon = result === 'PASS' ? '✓' : result === 'FAIL' ? '✗' : result === 'FLAG' ? '⚠️' : '•';
                const resultClass = result === 'PASS' ? 'check-pass' : result === 'FAIL' ? 'check-fail' : 'check-flag';
                
                html += `<tr>
                    <td><strong>${escapeHtml(checkType)}</strong>
                    <td class="${resultClass}">${statusIcon} ${escapeHtml(result)}</td>
                    <td><small>${timestamp}</small></td>
                </tr>\n`;
            }
        });
        html += `</tbody>\n</table>\n`;
    }
    
    // All other fields
    html += `<h2>Complete Results</h2>\n<table>\n<tbody>\n`;
    for (const [key, value] of Object.entries(results)) {
        if (!['status', 'summary', 'eligible', 'risk_factors', 'checks_performed', 'recommendations', 'findings_summary'].includes(key)) {
            html += `<tr>
                <th style="width: 30%;">${escapeHtml(key.replace(/_/g, ' ').toUpperCase())}</th>
                <td>${formatHTMLValue(value)}</td>
            </tr>\n`;
        }
    }
    html += `</tbody>\n</table>\n`;
    }
    
    html += `
    </div>
</body>
</html>`;
    
    return html;
}

/**
 * Format a value for HTML export
 * @param {*} value - Value to format
 * @returns {string} Formatted HTML
 */
function formatHTMLValue(value) {
    if (value === null || value === undefined) {
        return '<em>N/A</em>';
    }
    
    if (typeof value === 'boolean') {
        return value ? '<span style="color: #4caf50;">✓ Yes</span>' : '<span style="color: #f44336;">✗ No</span>';
    }
    
    if (Array.isArray(value)) {
        if (value.length === 0) {
            return '<em>Empty list</em>';
        }
        return '<ul>' + value.map(item => `<li>${formatHTMLValue(item)}</li>`).join('') + '</ul>';
    }
    
    if (typeof value === 'object') {
        return '<code>' + escapeHtml(JSON.stringify(value, null, 2)) + '</code>';
    }
    
    return escapeHtml(String(value));
}

/**
 * Export results as JSON
 * @param {Object} results - Results to export
 */
function exportAsJSON(results) {
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `workflow_results_${new Date().toISOString().split('.')[0].replace(/:/g, '-')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Results exported as JSON', 'success');
}

/**
 * Export results as Markdown
 * @param {Object} results - Results to export
 */
function exportAsMarkdown(results) {
    const markdown = convertToMarkdown(results);
    const dataBlob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `workflow_results_${new Date().toISOString().split('.')[0].replace(/:/g, '-')}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Results exported as Markdown', 'success');
}

/**
 * Convert results object to Markdown format
 * @param {Object} results - Results to convert
 * @param {Object} metadata - Workflow run metadata
 * @returns {string} Markdown string
 */
function convertToMarkdown(results, metadata = {}) {
    const timestamp = formatExportDate(new Date());
    const workflowName = metadata.workflow_name || results.workflow_name || 'Workflow';
    
    let md = `# ${workflowName}\n\n`;
    
    // Workflow Metadata
    md += `## Workflow Run Information\n\n`;
    md += `| Field | Value |\n`;
    md += `|-------|-------|\n`;
    md += `| Run ID | \`${metadata.run_id || 'N/A'}\` |\n`;
    md += `| Workflow ID | \`${metadata.workflow_id || 'N/A'}\` |\n`;
    md += `| Status | ${metadata.status || 'completed'} |\n`;
    md += `| Started | ${metadata.started_at || 'N/A'} |\n`;
    md += `| Completed | ${metadata.completed_at || 'N/A'} |\n`;
    md += `| Duration | ${metadata.duration ? metadata.duration.toFixed(2) + 's' : 'N/A'} |\n`;
    md += `| Exported | ${timestamp} |\n\n`;
    
    md += `---\n\n`;
    md += `## Results\n\n`;
    
    // Status
    if (results.status) {
        md += `### Status\n\n${results.status}\n\n`;
    }
    
    // Summary
    if (results.summary) {
        md += `## Summary\n\n${results.summary}\n\n`;
    }
    
    // Findings summary
    if (results.findings_summary) {
        md += `## Findings\n\n${results.findings_summary}\n\n`;
    }
    
    // Eligibility
    if (results.eligible !== undefined) {
        md += `## Eligibility\n\n`;
        md += results.eligible ? '✓ **Eligible**\n\n' : '✗ **Not Eligible**\n\n';
    }
    
    // Risk Factors
    if (results.risk_factors && results.risk_factors.length > 0) {
        md += `## Risk Factors\n\n`;
        results.risk_factors.forEach(rf => {
            md += `- ${rf}\n`;
        });
        md += `\n`;
    }
    
    // Recommendations
    if (results.recommendations && results.recommendations.length > 0) {
        md += `## Recommendations\n\n`;
        results.recommendations.forEach(rec => {
            md += `- ${rec}\n`;
        });
        md += `\n`;
    }
    
    // Checks Performed
    if (results.checks_performed && results.checks_performed.length > 0) {
        md += `## Checks Performed\n\n`;
        results.checks_performed.forEach(check => {
            if (typeof check === 'object' && check !== null) {
                const checkType = check.check_type || 'Unknown';
                const result = check.result || 'UNKNOWN';
                const statusIcon = result === 'PASS' ? '✓' : result === 'FAIL' ? '✗' : result === 'FLAG' ? '⚠️' : '•';
                md += `- **${checkType}**: ${statusIcon} ${result}\n`;
            }
        });
        md += `\n`;
    }
    
    // All other fields
    md += `## Additional Details\n\n`;
    const excludeKeys = ['status', 'summary', 'eligible', 'risk_factors', 'checks_performed', 'recommendations', 'findings_summary'];
    const otherKeys = Object.keys(results).filter(k => !excludeKeys.includes(k));
    
    if (otherKeys.length > 0) {
        otherKeys.forEach(key => {
            const value = results[key];
            md += `### ${key.replace(/_/g, ' ').toUpperCase()}\n\n`;
            md += formatValue(value) + '\n\n';
        });
    }
    
    return md;
}

/**
 * Format a value for display (used in markdown export)
 * @param {*} value - Value to format
 * @returns {string} Formatted string
 */
function formatValue(value) {
    if (value === null || value === undefined) {
        return '*N/A*';
    }
    
    if (typeof value === 'boolean') {
        return value ? '✓ Yes' : '✗ No';
    }
    
    if (Array.isArray(value)) {
        if (value.length === 0) {
            return '*Empty list*';
        }
        return value.map(item => `- ${formatValue(item)}`).join('\n');
    }
    
    if (typeof value === 'object') {
        return '```json\n' + JSON.stringify(value, null, 2) + '\n```';
    }
    
    return String(value);
}

/**
 * Request browser notification permission
 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            console.log('Notification permission:', permission);
        });
    }
}

// Request notification permission on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', requestNotificationPermission);
} else {
    requestNotificationPermission();
}

// Export for global access
window.initializeWorkflowExecution = initializeWorkflowExecution;
window.getWorkflowFormInputData = getWorkflowFormInputData;
window.showNotification = showNotification;
window.viewAsHTML = viewAsHTML;
window.exportAsJSON = exportAsJSON;
window.exportAsMarkdown = exportAsMarkdown;
window.renderResultDetails = renderResultDetails;
window.generateHTMLExport = generateHTMLExport;
window.convertToMarkdown = convertToMarkdown;
window.escapeHtml = escapeHtml;
window.formatHTMLValue = formatHTMLValue;
window.formatValue = formatValue;
