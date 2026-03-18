(function () {
  var messageList, promptInput, sendBtn, chatForm, sessionListEl, favoriteCardsEl, favoriteCardsPanel, toggleCardsBtn, newSessionBtn;
  var currentSessionId = null;

  function apiBase() {
    return (window.REALTYIQ_API_BASE != null ? window.REALTYIQ_API_BASE : "") || "";
  }

  function initElements() {
    messageList = document.getElementById("message-list");
    promptInput = document.getElementById("prompt-input");
    sendBtn = document.getElementById("send-btn");
    chatForm = document.getElementById("chat-form");
    sessionListEl = document.getElementById("session-list");
    favoriteCardsEl = document.getElementById("favorite-cards");
    favoriteCardsPanel = document.getElementById("favorite-cards-panel");
    toggleCardsBtn = document.getElementById("toggle-cards-btn");
    newSessionBtn = document.getElementById("new-session-btn");
  }

  function getCsrfToken() {
    var el = document.querySelector("[name=csrfmiddlewaretoken]");
    return (window.CSRF_TOKEN != null ? window.CSRF_TOKEN : "") || (el ? el.value : "") || "";
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function isChartImage(src) {
    if (!src || typeof src !== "string") return false;
    return src.indexOf("/api/agent-chart/") === 0 || src.indexOf("data:image/png;base64,") === 0;
  }

  function downloadChartImage(img, filename) {
    var src = img.getAttribute("src");
    if (!src) return;
    var name = filename || "chart.png";
    if (src.indexOf("data:image/png;base64,") === 0) {
      var a = document.createElement("a");
      a.href = src;
      a.download = name;
      a.rel = "noopener";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      return;
    }
    if (src.indexOf("/api/agent-chart/") === 0) {
      var base = apiBase();
      var url = (src.indexOf(base) === 0 ? src : base + (src.charAt(0) === "/" ? "" : "/") + src);
      fetch(url, { credentials: "same-origin" })
        .then(function (res) { return res.ok ? res.blob() : Promise.reject(new Error("Failed to load chart")); })
        .then(function (blob) {
          var a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = name;
          a.rel = "noopener";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(a.href);
        })
        .catch(function () { console.warn("Chart download failed"); });
    }
  }

  function addChartDownloadButtons(bubble) {
    var imgs = bubble.querySelectorAll ? bubble.querySelectorAll("img") : [];
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      var src = img.getAttribute("src");
      if (!isChartImage(src)) continue;
      var wrapper = document.createElement("div");
      wrapper.className = "chart-image-wrapper";
      img.parentNode.insertBefore(wrapper, img);
      wrapper.appendChild(img);
      var label = (img.getAttribute("alt") || "Chart").replace(/^Chart:\s*/i, "");
      var filename = (label.trim() || "chart").replace(/[^\w\s-]/g, "").replace(/\s+/g, "_").slice(0, 60) + ".png";
      var downloadLink = document.createElement("button");
      downloadLink.type = "button";
      downloadLink.className = "chart-download-btn";
      downloadLink.title = "Download chart as PNG";
      downloadLink.textContent = "Download image";
      downloadLink.addEventListener("click", function (imgEl, fn) {
        return function () { downloadChartImage(imgEl, fn); };
      }(img, filename));
      wrapper.appendChild(downloadLink);
    }
  }

  function toggleFavoriteCards() {
    if (favoriteCardsPanel) {
      favoriteCardsPanel.classList.toggle("collapsed");
    }
  }

  function bindToggleCards() {
    if (toggleCardsBtn) {
      toggleCardsBtn.addEventListener("click", toggleFavoriteCards);
    }
  }
  
  function bindAgentSelector() {
    var agentSelector = document.getElementById('agent-selector');
    if (agentSelector) {
      agentSelector.addEventListener('change', function() {
        // Agent selector only affects which agent processes messages
        // Cards remain visible regardless of agent selection
        console.log('Agent changed to:', agentSelector.value);
      });
    }
  }

  function appendMessage(role, content, timestamp, elapsedMs, messageId, traceId, fromCache, agentName, isCommand, commandMetadata, audioUrl, section508Enabled, modelName) {
    if (!messageList) return;
    
    var div = document.createElement("div");
    div.className = "message " + role;
    if (messageId) {
      div.setAttribute("data-message-id", messageId);
    }
    if (fromCache) {
      div.classList.add("from-cache");
    }
    if (isCommand) {
      div.classList.add("command");
      div.setAttribute("role", "status");
      if (commandMetadata && commandMetadata.command) {
        div.setAttribute("aria-label", "Command response: " + commandMetadata.command);
      }
    }
    
    var bubble = document.createElement("div");
    bubble.className = "bubble";
    
    // Render markdown for assistant, plain text for user
    if (role === "assistant" && typeof marked !== "undefined") {
      // Configure marked to use highlight.js for code blocks
      if (typeof hljs !== "undefined") {
        marked.setOptions({
          highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
              try {
                return hljs.highlight(code, { language: lang }).value;
              } catch (err) {}
            }
            return hljs.highlightAuto(code).value;
          }
        });
      }
      bubble.innerHTML = marked.parse(content);
      addChartDownloadButtons(bubble);
    } else {
      bubble.innerHTML = escapeHtml(content).replace(/\n/g, "<br>");
    }
    
    var meta = document.createElement("div");
    meta.className = "meta";
    
    // Add copy button for assistant messages
    if (role === "assistant") {
      var copyBtn = document.createElement("button");
      copyBtn.className = "copy-btn";
      copyBtn.title = "Copy to clipboard";
      copyBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
      copyBtn.addEventListener("click", function() {
        copyToClipboard(content, copyBtn);
      });
      meta.appendChild(copyBtn);
    }
    
    var metaText = document.createElement("span");
    metaText.className = "meta-text";
    // Use agent name if provided, otherwise default to "RealtyIQ"
    var displayText = role === "user" ? "You" : (agentName || "RealtyIQ");
    // Add model name on same line for assistant messages (not commands)
    if (role === "assistant" && modelName && !isCommand) {
      displayText += " • " + modelName;
    }
    metaText.textContent = displayText;
    meta.appendChild(metaText);
    
    // Add command badge for command responses
    if (role === "assistant" && isCommand && commandMetadata) {
      var cmdBadge = document.createElement("span");
      cmdBadge.className = "command-badge";
      cmdBadge.textContent = "Command";
      cmdBadge.title = "Command: " + (commandMetadata.command || "unknown");
      meta.appendChild(cmdBadge);
    }
    
    // Add cache badge for cached responses
    if (role === "assistant" && fromCache) {
      var cacheBadge = document.createElement("span");
      cacheBadge.className = "cache-badge";
      cacheBadge.title = "Response retrieved from cache";
      cacheBadge.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> Cached';
      meta.appendChild(cacheBadge);
    }
    
    // Add timestamp and elapsed time for assistant messages
    if (role === "assistant" && (timestamp || elapsedMs)) {
      var metaDetails = document.createElement("span");
      metaDetails.className = "meta-details";
      var detailsParts = [];
      
      if (timestamp) {
        var time = new Date(timestamp);
        var dateStr = time.toLocaleDateString(undefined, { 
          month: 'short', 
          day: 'numeric',
          year: time.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
        });
        var timeStr = time.toLocaleTimeString(undefined, {
          hour: 'numeric',
          minute: '2-digit',
          second: '2-digit'
        });
        detailsParts.push(dateStr + " " + timeStr);
      }
      
      if (elapsedMs) {
        var seconds = (elapsedMs / 1000).toFixed(1);
        detailsParts.push(seconds + "s");
      }
      
      if (detailsParts.length > 0) {
        metaDetails.textContent = " • " + detailsParts.join(" • ");
        meta.appendChild(metaDetails);
      }
    }
    
    // Add feedback buttons for assistant messages
    if (role === "assistant" && messageId) {
      var feedbackContainer = document.createElement("span");
      feedbackContainer.className = "feedback-buttons";
      
      var thumbsUpBtn = document.createElement("button");
      thumbsUpBtn.className = "feedback-btn thumbs-up";
      thumbsUpBtn.title = "Good response";
      thumbsUpBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>';
      thumbsUpBtn.addEventListener("click", function() {
        submitFeedback(messageId, "positive", thumbsUpBtn, thumbsDownBtn, traceId);
      });
      
      var thumbsDownBtn = document.createElement("button");
      thumbsDownBtn.className = "feedback-btn thumbs-down";
      thumbsDownBtn.title = "Bad response";
      thumbsDownBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>';
      thumbsDownBtn.addEventListener("click", function() {
        submitFeedback(messageId, "negative", thumbsUpBtn, thumbsDownBtn, traceId);
      });
      
      feedbackContainer.appendChild(thumbsUpBtn);
      feedbackContainer.appendChild(thumbsDownBtn);
      meta.appendChild(feedbackContainer);
    }
    
    div.appendChild(bubble);
    div.appendChild(meta);
    
    // Add audio player for Section 508 mode (assistant messages only)
    if (role === "assistant" && section508Enabled && messageId) {
      var audioContainer = document.createElement("div");
      audioContainer.className = "audio-player-container";
      audioContainer.setAttribute("data-message-id", messageId);
      
      if (audioUrl) {
        // Audio is ready, show player
        createAudioPlayer(audioContainer, audioUrl, messageId);
      } else {
        // Audio is being generated, show loading state
        audioContainer.innerHTML = '<div class="audio-loading"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg> Generating audio...</div>';
        
        // Poll for audio URL
        pollForAudio(messageId, audioContainer);
      }
      
      div.appendChild(audioContainer);
    }
    
    messageList.appendChild(div);
    messageList.scrollTop = messageList.scrollHeight;
    
    // Check if this assistant message mentions a workflow run and monitor it
    if (role === "assistant" && content) {
      var runId = extractRunId(content);
      if (runId) {
        console.log('Detected workflow run ID:', runId);
        // Delay slightly to ensure message is fully rendered
        setTimeout(function() {
          monitorWorkflowProgress(runId, div);
        }, 100);
      }
    }
  }
  
  function createAudioPlayer(container, audioUrl, messageId) {
    container.innerHTML = '';
    
    var playerWrapper = document.createElement("div");
    playerWrapper.className = "audio-player";
    
    var audioElement = document.createElement("audio");
    audioElement.controls = true;
    audioElement.preload = "metadata";
    audioElement.className = "audio-controls";
    audioElement.setAttribute("aria-label", "Text-to-speech audio for this response");
    
    var source = document.createElement("source");
    source.src = audioUrl;
    // Auto-detect format from URL or default to WAV (Piper native format)
    source.type = audioUrl.includes('.mp3') ? "audio/mpeg" : "audio/wav";
    audioElement.appendChild(source);
    
    var listenLabel = document.createElement("span");
    listenLabel.className = "audio-label";
    listenLabel.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align: middle; margin-right: 4px;"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>Listen';
    
    playerWrapper.appendChild(listenLabel);
    playerWrapper.appendChild(audioElement);
    container.appendChild(playerWrapper);
    
    // Announce to screen reader
    if (window.announceToScreenReader) {
      window.announceToScreenReader('Audio available for this response');
    }
  }
  
  function pollForAudio(messageId, container) {
    var attempts = 0;
    var maxAttempts = 30;  // Poll for up to 60 seconds (2s intervals)
    
    var pollInterval = setInterval(function() {
      attempts++;
      
      fetch(apiBase() + "/api/messages/" + messageId + "/audio/", {
        method: "GET",
        headers: {
          "Content-Type": "application/json"
        }
      })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.has_audio && data.audio_url) {
          // Audio is ready
          clearInterval(pollInterval);
          createAudioPlayer(container, data.audio_url, messageId);
        } else if (attempts >= maxAttempts) {
          // Give up after max attempts
          clearInterval(pollInterval);
          container.innerHTML = '<div class="audio-error"><small>Audio generation timed out</small></div>';
        }
      })
      .catch(function(err) {
        console.error("Error polling for audio:", err);
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          container.innerHTML = '<div class="audio-error"><small>Audio unavailable</small></div>';
        }
      });
    }, 2000);  // Poll every 2 seconds
  }
  
  function copyToClipboard(text, button) {
    // Remove markdown formatting for cleaner clipboard text
    var plainText = text.replace(/[#*`_~\[\]]/g, '');
    
    navigator.clipboard.writeText(plainText).then(function() {
      // Visual feedback
      var originalHTML = button.innerHTML;
      button.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
      button.classList.add("copied");
      
      setTimeout(function() {
        button.innerHTML = originalHTML;
        button.classList.remove("copied");
      }, 2000);
    }).catch(function(err) {
      console.error("Failed to copy:", err);
      alert("Failed to copy to clipboard");
    });
  }
  
  function submitFeedback(messageId, feedbackType, thumbsUpBtn, thumbsDownBtn, traceId) {
    fetch(apiBase() + "/api/messages/" + messageId + "/feedback/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        feedback: feedbackType,
        trace_id: traceId  // Send Langfuse trace ID for observability
      })
    })
    .then(function(r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function(data) {
      console.log("Feedback submitted:", feedbackType);
      
      // Update button states
      thumbsUpBtn.classList.remove("active");
      thumbsDownBtn.classList.remove("active");
      
      if (feedbackType === "positive") {
        thumbsUpBtn.classList.add("active");
      } else {
        thumbsDownBtn.classList.add("active");
      }
    })
    .catch(function(err) {
      console.error("Failed to submit feedback:", err);
      alert("Failed to submit feedback. Please try again.");
    });
  }

  function setLoading(loading) {
    if (sendBtn) {
      sendBtn.disabled = loading;
      sendBtn.textContent = loading ? "..." : "Send";
    }
    
    // Change cursor to wait while loading
    if (loading) {
      document.body.classList.add("loading");
      if (messageList && messageList.parentElement) {
        messageList.parentElement.classList.add("loading");
      }
    } else {
      document.body.classList.remove("loading");
      if (messageList && messageList.parentElement) {
        messageList.parentElement.classList.remove("loading");
      }
    }
  }

  function runPrompt(promptText) {
    console.log(">>> runPrompt() called with:", promptText);
    
    if (!(promptText || "").trim()) {
      console.log("✗ Empty prompt, returning");
      return;
    }
    
    console.log("✓ Adding to prompt history");
    // Add to prompt history (for card clicks that bypass the form)
    if (window.RealtyIQPromptHistory) {
      window.RealtyIQPromptHistory.add(promptText);
    }
    
    console.log("✓ Appending user message to chat");
    appendMessage("user", promptText);
    
    console.log("✓ Setting loading state");
    setLoading(true);
    
    var startTime = Date.now();
    
    // Get selected agent and model
    var agentSelector = document.getElementById('agent-selector');
    var modelSelector = document.getElementById('model-selector');
    var selectedAgent = agentSelector ? agentSelector.value : 'gres';
    var selectedModel = modelSelector ? modelSelector.value : 'claude-3-5-sonnet';
    
    console.log("✓ Using agent:", selectedAgent, "model:", selectedModel);
    
    fetch(apiBase() + "/api/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ 
        prompt: promptText,
        session_id: currentSessionId,
        agent: selectedAgent,
        model: selectedModel,
        elapsed_ms: Date.now() - startTime
      }),
    })
      .then(function (r) {
        var ct = (r.headers.get("Content-Type") || "").toLowerCase();
        if (ct.indexOf("application/json") !== -1) {
          return r.json().then(function (data) { return { ok: r.ok, data: data }; });
        }
        return r.text().then(function (text) {
          return { ok: r.ok, data: { error: "Server returned " + r.status + (text ? ": " + text.substring(0, 200) : "") } };
        });
      })
      .then(function (result) {
        setLoading(false);
        var elapsedMs = Date.now() - startTime;
        var timestamp = new Date().toISOString();
        var data = result.data;
        
        if (!result.ok && data && data.error) {
          appendMessage("assistant", "Error: " + data.error, timestamp, elapsedMs, null, null, false, null, false, null, null, false, null);
          return;
        }
        if (data && data.error) {
          appendMessage("assistant", "Error: " + data.error, timestamp, elapsedMs, null, null, false, null, false, null, null, false, null);
        } else {
          appendMessage(
            "assistant", 
            (data && data.response) || "", 
            timestamp, 
            elapsedMs, 
            data.message_id, 
            data.trace_id, 
            data.from_cache, 
            data.agent_name,
            data.is_command,
            data.metadata,
            data.audio_url,
            data.section_508_enabled,
            data.model_name
          );
          
          // Check if command wants to open a diagram
          if (data && data.diagram_url) {
            window.open(data.diagram_url, '_blank');
          }
          
          // Check if command wants to reload UI (e.g., Section 508 mode changed)
          if (data && data.metadata && data.metadata.reload_ui) {
            // Update Section 508 mode if changed
            if (data.metadata.setting === "508" && typeof data.metadata.value !== 'undefined') {
              if (window.toggleSection508) {
                window.toggleSection508(data.metadata.value);
              }
            }
          }
          
          if (data && data.session_id) {
            currentSessionId = data.session_id;
            loadSessions();
          }
        }
      })
      .catch(function (err) {
        setLoading(false);
        var elapsedMs = Date.now() - startTime;
        var timestamp = new Date().toISOString();
        appendMessage("assistant", "Error: " + (err.message || "Request failed"), timestamp, elapsedMs, null, null, false, null, false, null, null, false, null);
      });
  }

  function renderFavoriteCards(cards) {
    console.log('renderFavoriteCards called with', cards ? cards.length : 0, 'cards');
    if (!favoriteCardsEl) {
      console.log('favoriteCardsEl not found!');
      return;
    }
    favoriteCardsEl.innerHTML = "";
    if (!(cards && cards.length)) {
      var empty = document.createElement("p");
      empty.className = "favorite-cards-empty";
      empty.style.cssText = "margin:0;font-size:0.875rem;color:#6f6f6f;";
      empty.textContent = "No favorite cards. Add favorites from Card Library.";
      favoriteCardsEl.appendChild(empty);
      return;
    }
    cards.forEach(function (c) {
      console.log('Rendering card:', c.name, 'agent_type:', c.agent_type);
      var tile = document.createElement("div");
      tile.className = "favorite-card-tile";
      tile.dataset.cardId = c.id;
      tile.dataset.cardName = c.name || "";
      tile.dataset.cardDescription = c.description || "";
      tile.dataset.prompt = c.prompt || "";
      tile.dataset.agentType = c.agent_type || "";
      
      // Card number badge (upper left)
      var cardNumberBadge = document.createElement("div");
      cardNumberBadge.className = "card-number-badge";
      cardNumberBadge.textContent = "#" + c.id;
      cardNumberBadge.title = "Card ID: " + c.id;
      
      // Ellipsis menu button (upper right)
      var ellipsisBtn = document.createElement("button");
      ellipsisBtn.type = "button";
      ellipsisBtn.className = "card-ellipsis";
      ellipsisBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><circle cx="8" cy="3" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="8" cy="13" r="1.5"/></svg>';
      ellipsisBtn.title = "Edit Card";
      ellipsisBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        openEditModal(c.id, c.name, c.description, c.prompt);
      });
      
      var nameEl = document.createElement("div");
      nameEl.className = "card-name";
      
      // Add agent badge to card name
      var nameText = document.createElement("span");
      nameText.textContent = c.name || "Card";
      nameEl.appendChild(nameText);
      
      if (c.agent_type) {
        var badge = document.createElement("span");
        badge.style.cssText = "font-size:0.75rem;margin-left:0.5rem;opacity:0.7;";
        if (c.agent_type === 'gres') {
          badge.textContent = "🏢";
          badge.title = "GRES Agent";
        } else if (c.agent_type === 'sam') {
          badge.textContent = "🚫";
          badge.title = "SAM.gov Agent";
        } else if (c.agent_type === 'ofac') {
          badge.textContent = "🚨";
          badge.title = "OFAC Compliance Agent";
        } else if (c.agent_type === 'idv') {
          console.log('Setting IdV badge for card:', c.name);
          badge.textContent = "🔐";
          badge.title = "Identity Verification Agent";
        } else if (c.agent_type === 'library') {
          badge.textContent = "📚";
          badge.title = "Library Agent";
        } else if (c.agent_type === '508') {
          badge.textContent = "🔊";
          badge.title = "Section 508 Agent";
        } else if (c.agent_type === 'all') {
          badge.textContent = "📋";
          badge.title = "All Agents";
        }
        // Only append badge if it has content
        if (badge.textContent) {
          nameEl.appendChild(badge);
        } else {
          console.warn('Badge has no content for agent_type:', c.agent_type);
        }
      }
      
      nameEl.dataset.cardId = c.id;
      
      var preview = document.createElement("div");
      preview.className = "card-prompt-preview";
      preview.textContent = (c.prompt || "").trim() || "(no prompt)";
      preview.title = (c.prompt || "").trim();
      
      tile.appendChild(cardNumberBadge);
      tile.appendChild(ellipsisBtn);
      tile.appendChild(nameEl);
      tile.appendChild(preview);
      
      // Click on card runs the prompt
      tile.addEventListener("click", function (e) {
        if (e.target.tagName === "BUTTON") return;
        if (e.target.closest(".card-ellipsis")) return;
        
        // Auto-switch to the card's agent if specified
        var cardAgentType = tile.dataset.agentType || c.agent_type;
        if (cardAgentType && cardAgentType !== 'all') {
          var agentSelector = document.getElementById('agent-selector');
          if (agentSelector && agentSelector.value !== cardAgentType) {
            console.log('Auto-switching agent to:', cardAgentType);
            agentSelector.value = cardAgentType;
            
            // Trigger change event to update any listeners
            var event = new Event('change', { bubbles: true });
            agentSelector.dispatchEvent(event);
          }
        }
        
        runPrompt(tile.dataset.prompt || c.prompt);
      });
      
      favoriteCardsEl.appendChild(tile);
    });
  }

  var currentEditCardModal = null;
  
  function openEditModal(cardId, name, description, prompt) {
    document.getElementById("edit-card-id").value = cardId;
    document.getElementById("edit-card-name").value = name || "";
    document.getElementById("edit-card-description").value = description || "";
    document.getElementById("edit-card-prompt").value = prompt || "";
    
    if (!currentEditCardModal && window.bootstrap) {
      currentEditCardModal = new bootstrap.Modal(document.getElementById("cardEditModal"));
    }
    if (currentEditCardModal) {
      currentEditCardModal.show();
    }
  }
  
  function saveCardFromModal() {
    var cardId = document.getElementById("edit-card-id").value;
    var name = document.getElementById("edit-card-name").value.trim();
    var description = document.getElementById("edit-card-description").value.trim();
    var prompt = document.getElementById("edit-card-prompt").value.trim();
    
    if (!name || !prompt) {
      alert("Title and Prompt are required.");
      return;
    }
    
    var saveBtn = document.getElementById("save-card-btn");
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";
    
    fetch(apiBase() + "/api/card/" + cardId + "/patch/", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ name: name, description: description, prompt: prompt }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        saveBtn.disabled = false;
        saveBtn.textContent = "Save Changes";
        
        // Update the card tile in the UI
        var tile = favoriteCardsEl.querySelector('[data-card-id="' + cardId + '"]');
        if (tile) {
          tile.dataset.cardName = data.name || "";
          tile.dataset.cardDescription = data.description || "";
          tile.dataset.prompt = data.prompt || "";
          
          var nameEl = tile.querySelector(".card-name");
          if (nameEl) nameEl.textContent = data.name || "Card";
          
          var previewEl = tile.querySelector(".card-prompt-preview");
          if (previewEl) {
            previewEl.textContent = (data.prompt || "").trim() || "(no prompt)";
            previewEl.title = (data.prompt || "").trim();
          }
        }
        
        // Close modal
        if (currentEditCardModal) {
          currentEditCardModal.hide();
        }
      })
      .catch(function (err) {
        saveBtn.disabled = false;
        saveBtn.textContent = "Save Changes";
        alert("Error saving card: " + (err.message || "Unknown error"));
      });
  }

  function parseJsonResponse(r) {
    var ct = (r.headers.get("Content-Type") || "").toLowerCase();
    if (ct.indexOf("application/json") !== -1) return r.json();
    return r.text().then(function () { return null; });
  }

  function loadFavoriteCards() {
    // Load ALL favorite cards, regardless of selected agent
    // This allows users to see and use any favorite card with any agent
    console.log('loadFavoriteCards: Fetching from API...');
    fetch(apiBase() + "/api/cards/?favorites=1")
      .then(function (r) { return parseJsonResponse(r); })
      .then(function (data) {
        console.log('loadFavoriteCards: API response received:', data);
        var cards = data && data.cards ? data.cards : [];
        console.log('loadFavoriteCards: Extracted', cards.length, 'cards');
        cards.forEach(function(c, idx) {
          console.log('  Card', idx + 1, ':', c.name, '(agent:', c.agent_type, ', favorite:', c.is_favorite, ')');
        });
        if (favoriteCardsEl) renderFavoriteCards(cards);
      })
      .catch(function (err) {
        console.error('loadFavoriteCards: API fetch failed:', err);
        // Keep existing content (e.g. server-rendered cards) on fetch failure
        if (!favoriteCardsEl) return;
        if (!favoriteCardsEl.querySelector(".favorite-card-tile") && !favoriteCardsEl.querySelector(".favorite-cards-empty")) {
          renderFavoriteCards([]);
        }
      });
  }


  function loadSessions() {
    if (!sessionListEl) return;
    fetch(apiBase() + "/api/sessions/")
      .then(function (r) { return parseJsonResponse(r); })
      .then(function (data) {
        sessionListEl.innerHTML = "";
        var sessions = (data && data.sessions) ? data.sessions : [];
        
        if (sessions.length === 0) {
          var emptyLi = document.createElement("li");
          emptyLi.style.cssText = "padding: 0.5rem 0; color: #6f6f6f; font-size: 0.8125rem;";
          emptyLi.textContent = "No sessions yet";
          sessionListEl.appendChild(emptyLi);
          return;
        }
        
        sessions.forEach(function (s) {
          var li = document.createElement("li");
          li.className = "session-item";
          
          var a = document.createElement("a");
          a.href = "#";
          a.dataset.sessionId = s.id;
          a.dataset.title = s.title || "Session " + s.id;
          
          // Session title (clickable to load)
          var titleSpan = document.createElement("span");
          titleSpan.className = "session-title";
          titleSpan.textContent = s.title || "Session " + s.id;
          a.appendChild(titleSpan);
          
          // Mark active session
          if (currentSessionId === s.id) {
            a.className = "active";
          }
          
          a.addEventListener("click", function (e) {
            e.preventDefault();
            loadSession(parseInt(a.dataset.sessionId, 10));
          });
          
          // Rename button
          var renameBtn = document.createElement("button");
          renameBtn.className = "session-action-btn";
          renameBtn.title = "Rename session";
          renameBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>';
          renameBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            renameSession(s.id, a);
          });
          
          // Export button
          var exportBtn = document.createElement("button");
          exportBtn.className = "session-action-btn";
          exportBtn.title = "Export session";
          exportBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>';
          exportBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            exportSession(s.id);
          });
          
          // Delete button
          var deleteBtn = document.createElement("button");
          deleteBtn.className = "session-action-btn session-delete-btn";
          deleteBtn.title = "Delete session";
          deleteBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';
          deleteBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            deleteSession(s.id, li);
          });
          
          li.appendChild(a);
          li.appendChild(renameBtn);
          li.appendChild(exportBtn);
          li.appendChild(deleteBtn);
          sessionListEl.appendChild(li);
        });
      })
      .catch(function () {});
  }
  
  function renameSession(sessionId, sessionLink) {
    var currentTitle = sessionLink.dataset.title;
    var newTitle = prompt("Enter new session name:", currentTitle);
    
    if (newTitle === null || newTitle.trim() === "") return;
    
    fetch(apiBase() + "/api/sessions/" + sessionId + "/rename/", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ title: newTitle.trim() }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          sessionLink.dataset.title = data.title;
          sessionLink.querySelector(".session-title").textContent = data.title;
        } else {
          alert("Error renaming session: " + (data.error || "Unknown error"));
        }
      })
      .catch(function (err) {
        alert("Error renaming session: " + err.message);
      });
  }
  
  function exportSession(sessionId) {
    window.open(apiBase() + "/api/chat/" + sessionId + "/export/?view=browser", "_blank");
  }
  
  function deleteSession(sessionId, listItem) {
    if (!confirm("Are you sure you want to delete this session? This cannot be undone.")) {
      return;
    }
    
    fetch(apiBase() + "/api/sessions/" + sessionId + "/delete/", {
      method: "DELETE",
      headers: {
        "X-CSRFToken": getCsrfToken(),
      },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          // Remove from list
          listItem.remove();
          
          // If it was the active session, clear the chat
          if (currentSessionId === sessionId) {
            currentSessionId = null;
            if (messageList) messageList.innerHTML = "";
          }
        } else {
          alert("Error deleting session: " + (data.error || "Unknown error"));
        }
      })
      .catch(function (err) {
        alert("Error deleting session: " + err.message);
      });
  }

  function loadSession(sessionId) {
    currentSessionId = sessionId;
    if (messageList) messageList.innerHTML = "";
    
    fetch(apiBase() + "/api/chat/" + sessionId + "/")
      .then(function (r) { return parseJsonResponse(r); })
      .then(function (data) {
        var messages = (data && data.messages) ? data.messages : [];
        messages.forEach(function (m) {
          appendMessage(m.role, m.content, m.created_at, m.elapsed_ms, m.id, null, false, null, false, null, m.audio_url, window.SECTION_508_ENABLED, null);
          
          // Restore feedback state if exists
          if (m.role === "assistant" && m.feedback && m.id) {
            setTimeout(function() {
              var messageDiv = messageList.querySelector('[data-message-id="' + m.id + '"]');
              if (messageDiv) {
                var thumbsUp = messageDiv.querySelector('.thumbs-up');
                var thumbsDown = messageDiv.querySelector('.thumbs-down');
                
                if (m.feedback === "positive" && thumbsUp) {
                  thumbsUp.classList.add("active");
                } else if (m.feedback === "negative" && thumbsDown) {
                  thumbsDown.classList.add("active");
                }
              }
            }, 50);
          }
        });
        
        // Update session list to highlight active
        loadSessions();
      })
      .catch(function () {});
  }
  
  function startNewSession() {
    var sessionName = prompt("Enter a name for the new session:", "New Session");
    
    if (sessionName === null) return; // User cancelled
    
    var title = sessionName.trim() || "New Session";
    
    fetch(apiBase() + "/api/sessions/create/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ title: title }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          currentSessionId = data.session.id;
          if (messageList) messageList.innerHTML = "";
          if (promptInput) promptInput.focus();
          
          // Show notification about cleared context
          var cacheInfo = "";
          if (data.cache_cleared && data.cache_cleared > 0) {
            cacheInfo = " (Cache cleared: " + data.cache_cleared + " entries)";
          }
          console.log("✓ New session created" + cacheInfo + " - context reset");
          
          // Reload session list to show new session
          loadSessions();
        } else {
          alert("Error creating session: " + (data.error || "Unknown error"));
        }
      })
      .catch(function (err) {
        alert("Error creating session: " + err.message);
      });
  }
  
  // ----- CHECK PENDING PROMPT -----
  function checkPendingPrompt() {
    console.log("=== checkPendingPrompt() called ===");
    var pendingPrompt = sessionStorage.getItem("pendingPrompt");
    console.log("Pending prompt from sessionStorage:", pendingPrompt);
    
    if (pendingPrompt) {
      console.log("✓ Found pending prompt, will execute:", pendingPrompt);
      sessionStorage.removeItem("pendingPrompt");
      
      // Execute the prompt immediately, just like clicking a favorite card
      setTimeout(function() {
        console.log("✓ Timeout fired, executing prompt now...");
        console.log("✓ promptInput exists:", !!promptInput);
        console.log("✓ messageList exists:", !!messageList);
        
        if (promptInput) {
          console.log("✓ Calling runPrompt with:", pendingPrompt);
          runPrompt(pendingPrompt);
        } else {
          console.error("✗ ERROR: promptInput not found!");
        }
      }, 100);
    } else {
      console.log("✗ No pending prompt found in sessionStorage");
    }
  }

  function bindChatForm() {
    if (chatForm) {
      chatForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var prompt = (promptInput ? promptInput.value : "").trim();
        if (!prompt) return;
        if (promptInput) promptInput.value = "";
        runPrompt(prompt);
      });
    }
  }
  
  function bindNewSessionBtn() {
    if (newSessionBtn) {
      newSessionBtn.addEventListener("click", function () {
        startNewSession();
      });
    }
  }

  // Workflow progress monitoring
  var activeWorkflowConnections = {};
  
  function extractRunId(content) {
    // Look for run_id patterns in the response
    var patterns = [
      /run_id['":\s]+([a-f0-9]{8})/i,
      /run\s+([a-f0-9]{8})/i,
      /\/workflows\/runs\/([a-f0-9]{8})\//
    ];
    
    for (var i = 0; i < patterns.length; i++) {
      var match = content.match(patterns[i]);
      if (match && match[1]) {
        return match[1];
      }
    }
    return null;
  }
  
  function monitorWorkflowProgress(runId, messageElement) {
    if (activeWorkflowConnections[runId]) {
      // Already monitoring this run
      return;
    }
    
    // Create progress container within the message
    var progressContainer = document.createElement('div');
    progressContainer.className = 'workflow-progress';
    progressContainer.id = 'workflow-progress-' + runId;
    progressContainer.style.cssText = 'margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #2196f3; font-family: monospace; font-size: 0.9rem; max-height: 400px; overflow-y: auto;';
    
    var progressHeader = document.createElement('div');
    progressHeader.style.cssText = 'font-weight: 600; margin-bottom: 0.5rem; color: #1976d2; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
    progressHeader.innerHTML = '🔄 Workflow Progress (Live)';
    progressContainer.appendChild(progressHeader);
    
    var progressContent = document.createElement('div');
    progressContent.id = 'workflow-progress-content-' + runId;
    progressContainer.appendChild(progressContent);
    
    // Insert after the bubble element
    var bubble = messageElement.querySelector('.bubble');
    if (bubble && bubble.parentNode) {
      bubble.parentNode.insertBefore(progressContainer, bubble.nextSibling);
    }
    
    // Connect to WebSocket
    var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    var wsUrl = protocol + '//' + window.location.host + '/ws/workflows/' + runId + '/';
    
    console.log('Connecting to workflow WebSocket:', wsUrl);
    
    var ws = new WebSocket(wsUrl);
    activeWorkflowConnections[runId] = ws;
    
    ws.onopen = function() {
      console.log('Workflow WebSocket connected for run:', runId);
      var statusLine = document.createElement('div');
      statusLine.style.cssText = 'color: #388e3c; margin-bottom: 0.5rem;';
      statusLine.textContent = '✓ Connected - receiving live updates...';
      progressContent.appendChild(statusLine);
    };
    
    ws.onmessage = function(event) {
      try {
        var data = JSON.parse(event.data);
        console.log('Workflow progress:', data);
        
        if (data.type === 'progress') {
          // Real-time progress text
          var line = document.createElement('div');
          line.style.cssText = 'padding: 0.125rem 0; white-space: pre;';
          
          var text = data.text;
          if (text.includes('✓')) {
            line.style.color = '#388e3c';
          } else if (text.includes('✗')) {
            line.style.color = '#d32f2f';
          } else if (text.includes('⚠')) {
            line.style.color = '#f57c00';
          } else if (text.includes('→')) {
            line.style.color = '#1976d2';
          } else if (text.includes('=')) {
            line.style.fontWeight = 'bold';
            line.style.color = '#424242';
          }
          
          line.textContent = text;
          progressContent.appendChild(line);
          progressContainer.scrollTop = progressContainer.scrollHeight;
          
        } else if (data.type === 'status') {
          var statusLine = document.createElement('div');
          statusLine.style.cssText = 'padding: 0.25rem 0; font-weight: 600; color: #1976d2;';
          statusLine.textContent = '📊 Status: ' + data.status;
          progressContent.appendChild(statusLine);
          
        } else if (data.type === 'complete') {
          var completeLine = document.createElement('div');
          completeLine.style.cssText = 'padding: 0.5rem; margin-top: 0.5rem; background: #e8f5e9; border-radius: 3px; color: #388e3c; font-weight: 600;';
          completeLine.textContent = '✓ Workflow completed successfully!';
          progressContent.appendChild(completeLine);
          progressHeader.innerHTML = '✓ Workflow Progress (Completed)';
          progressHeader.style.color = '#388e3c';
          ws.close();
          delete activeWorkflowConnections[runId];
          
        } else if (data.type === 'waiting') {
          var waitLine = document.createElement('div');
          waitLine.style.cssText = 'padding: 0.5rem; margin-top: 0.5rem; background: #fff3e0; border-radius: 3px; color: #f57c00; font-weight: 600;';
          waitLine.textContent = '⏸ ' + data.message;
          progressContent.appendChild(waitLine);
          progressHeader.innerHTML = '⏸ Workflow Progress (Waiting for Task)';
          progressHeader.style.color = '#f57c00';
          ws.close();
          delete activeWorkflowConnections[runId];
          
        } else if (data.type === 'error') {
          var errorLine = document.createElement('div');
          errorLine.style.cssText = 'padding: 0.5rem; margin-top: 0.5rem; background: #ffebee; border-radius: 3px; color: #d32f2f; font-weight: 600;';
          errorLine.textContent = '✗ Error: ' + data.message;
          progressContent.appendChild(errorLine);
          progressHeader.innerHTML = '✗ Workflow Progress (Failed)';
          progressHeader.style.color = '#d32f2f';
          ws.close();
          delete activeWorkflowConnections[runId];
        }
      } catch (err) {
        console.error('Failed to parse workflow message:', err);
      }
    };
    
    ws.onerror = function(error) {
      console.error('Workflow WebSocket error:', error);
    };
    
    ws.onclose = function(event) {
      console.log('Workflow WebSocket closed:', event.code, event.reason);
      if (activeWorkflowConnections[runId]) {
        delete activeWorkflowConnections[runId];
      }
    };
  }

  // ============================================
  // Workflow Panel Functions
  // ============================================
  
  function loadFavoriteWorkflows() {
    var favoriteWorkflows = window.REALTYIQ_FAVORITE_WORKFLOWS || [];
    renderFavoriteWorkflows(favoriteWorkflows);
  }
  
  function renderFavoriteWorkflows(workflows) {
    var container = document.getElementById('favorite-workflows');
    if (!container) return;
    
    if (!workflows || workflows.length === 0) {
      container.innerHTML = '<span class="text-muted small">No favorite workflows yet. Star a workflow from the Workflows page to see it here.</span>';
      return;
    }
    
    container.innerHTML = '';
    workflows.forEach(function(workflow) {
      var card = document.createElement('div');
      card.className = 'workflow-quick-card';
      card.innerHTML = `
        <div class="workflow-quick-icon">${workflow.icon || '📋'}</div>
        <div class="workflow-quick-content">
          <h4 class="workflow-quick-title">${escapeHtml(workflow.name)}</h4>
          <p class="workflow-quick-description">${escapeHtml(workflow.description || '')}</p>
          <div class="workflow-quick-meta">
            <span class="workflow-quick-category">${escapeHtml(workflow.category || '')}</span>
            <span class="workflow-quick-duration">⏱ ${escapeHtml(workflow.estimated_duration || '')}</span>
          </div>
        </div>
        <button class="workflow-quick-run-btn" onclick="runWorkflow('${workflow.id}')" title="Run workflow">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </button>
      `;
      container.appendChild(card);
    });
  }
  
  function toggleFavoriteWorkflows() {
    var panel = document.getElementById('favorite-workflows-panel');
    var content = document.getElementById('favorite-workflows-content');
    var btn = document.getElementById('toggle-workflows-btn');
    
    if (!panel || !content || !btn) return;
    
    var isCollapsed = panel.classList.toggle('collapsed');
    
    // Toggle chevron icons
    var chevronUp = btn.querySelector('.chevron-up');
    var chevronDown = btn.querySelector('.chevron-down');
    if (chevronUp && chevronDown) {
      chevronUp.style.display = isCollapsed ? 'none' : 'block';
      chevronDown.style.display = isCollapsed ? 'block' : 'none';
    }
    
    // Update button title
    btn.setAttribute('title', isCollapsed ? 'Expand panel' : 'Collapse panel');
    
    // Store state in localStorage
    localStorage.setItem('favorite-workflows-collapsed', isCollapsed ? 'true' : 'false');
  }
  
  function bindToggleWorkflows() {
    var toggleWorkflowsBtn = document.getElementById('toggle-workflows-btn');
    if (toggleWorkflowsBtn) {
      toggleWorkflowsBtn.addEventListener('click', toggleFavoriteWorkflows);
    }
    
    // Restore collapsed state from localStorage
    var favoritePanel = document.getElementById('favorite-workflows-panel');
    if (favoritePanel && localStorage.getItem('favorite-workflows-collapsed') === 'true') {
      favoritePanel.classList.add('collapsed');
      var btn = document.getElementById('toggle-workflows-btn');
      if (btn) {
        var chevronUp = btn.querySelector('.chevron-up');
        var chevronDown = btn.querySelector('.chevron-down');
        if (chevronUp) chevronUp.style.display = 'none';
        if (chevronDown) chevronDown.style.display = 'block';
        btn.setAttribute('title', 'Expand panel');
      }
    }
  }
  
  window.runWorkflow = function(workflowId) {
    window.location.href = '/workflows/' + workflowId + '/';
  };

  function init() {
    console.log("chat.js: init() called");
    initElements();
    console.log("chat.js: Elements initialized, messageList:", !!messageList, "promptInput:", !!promptInput);
    
    // Show favorite cards from server immediately (so they appear before API fetch)
    var initial = window.REALTYIQ_FAVORITE_CARDS;
    if (Array.isArray(initial) && initial.length > 0 && favoriteCardsEl) {
      renderFavoriteCards(initial);
    }
    bindChatForm();
    bindEditModal();
    bindNewSessionBtn();
    bindToggleCards();
    bindToggleWorkflows();
    bindAgentSelector();
    loadSessions();
    loadFavoriteCards();
    loadFavoriteWorkflows();
    
    console.log("chat.js: About to check pending prompt");
    checkPendingPrompt();
  }
  
  function bindEditModal() {
    var saveBtn = document.getElementById("save-card-btn");
    if (saveBtn) {
      saveBtn.addEventListener("click", saveCardFromModal);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
