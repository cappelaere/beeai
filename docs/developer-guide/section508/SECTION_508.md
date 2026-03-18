# Section 508 Accessibility Mode

## Overview

The Section 508 Accessibility Mode provides enhanced accessibility features to ensure compliance with Section 508 of the Rehabilitation Act, making the BeeAI RealtyIQ Agent fully accessible to users with disabilities.

## Features

When Section 508 mode is enabled, the following accessibility enhancements are applied:

### Visual Enhancements
- **Larger Text**: Base font size increased to 18px
- **Increased Line Height**: Line height set to 1.6 for better readability
- **Enhanced Focus Indicators**: 3px solid outline with 2px offset for all focusable elements
- **Minimum Touch Targets**: All interactive elements (buttons, links, inputs) have minimum 44x44px size

### Screen Reader Support
- **ARIA Live Regions**: Automatic announcements for dynamic content changes
- **Semantic HTML**: Proper heading hierarchy and landmark regions
- **ARIA Labels**: Descriptive labels for all interactive elements
- **Screen Reader Announcements**: Function to announce messages to screen readers

### Keyboard Navigation
- **Full Keyboard Access**: All functionality accessible via keyboard
- **Scroll Margin**: 80px scroll margin for better focus visibility
- **Tab Order**: Logical tab order through interface

## Configuration

### Environment Variable

Set the default Section 508 mode for all users via environment variable:

```bash
# .env
SECTION_508_MODE=false  # or true to enable by default
```

**Supported Values:**
- `true`, `1`, `yes` → Enabled
- `false`, `0`, `no` → Disabled (default)

### Database Field

User preferences are stored in the `UserPreference` model:

```python
section_508_enabled = models.BooleanField(
    null=True,
    blank=True,
    help_text="Enable Section 508 accessibility features..."
)
```

- `null` → Uses environment default
- `true` → Explicitly enabled (overrides environment)
- `false` → Explicitly disabled (overrides environment)

## Usage

### Via Command Line

```bash
# Check current status
/settings

# Enable Section 508 mode
/settings 508 on

# Disable Section 508 mode
/settings 508 off
```

### Via Settings UI

1. Navigate to Settings page
2. Find "Accessibility" section
3. Toggle "Section 508 Mode" switch
4. Changes apply immediately (no page reload required)

### Via API

**Get Status:**
```bash
GET /api/section508/
```

Response:
```json
{
  "section_508_enabled": true,
  "default": false
}
```

**Update Status:**
```bash
POST /api/section508/
Content-Type: application/json

{"enabled": true}
```

Response:
```json
{
  "success": true,
  "section_508_enabled": true,
  "message": "Section 508 mode enabled"
}
```

## Frontend Integration

### JavaScript API

The frontend provides global functions for Section 508 mode:

```javascript
// Check if Section 508 mode is enabled
if (window.getSection508Status()) {
    console.log('Section 508 mode is active');
}

// Toggle Section 508 mode (applies CSS classes)
window.toggleSection508(true);  // Enable
window.toggleSection508(false); // Disable

// Fetch current status from server
await window.fetchSection508Status();

// Update status on server
await window.updateSection508Status(true);

// Announce message to screen readers
window.announceToScreenReader('Document uploaded successfully');
```

### CSS Styling

Section 508 mode applies the `section-508-mode` class to the body:

```css
/* Custom styles for Section 508 mode */
body.section-508-mode {
  font-size: 18px;
  line-height: 1.6;
}

body.section-508-mode button,
body.section-508-mode a {
  min-height: 44px;
  min-width: 44px;
}

body.section-508-mode :focus {
  outline: 3px solid #0f62fe;
  outline-offset: 2px;
}
```

### Template Variables

Section 508 status is available in all Django templates:

```django
{% if SECTION_508_ENABLED %}
  <div class="accessible-notice" role="alert">
    Section 508 mode is active
  </div>
{% endif %}

<!-- Default from environment -->
{% if SECTION_508_DEFAULT %}
  <span class="badge">Default Enabled</span>
{% endif %}
```

## Architecture

### Server-Side

1. **Context Processor** (`agent_app/context_processors.py`):
   - Reads `SECTION_508_MODE` from environment
   - Queries `UserPreference.section_508_enabled` for user override
   - Provides `SECTION_508_ENABLED` and `SECTION_508_DEFAULT` to all templates

2. **API Endpoint** (`agent_app/views.py`):
   - `GET /api/section508/` - Returns current status
   - `POST /api/section508/` - Updates user preference

3. **Command Handler** (`agent_app/commands/settings.py`):
   - `/settings 508 <on|off>` - CLI interface for toggling mode

4. **Database Model** (`agent_app/models.py`):
   - `UserPreference.section_508_enabled` - Per-user preference (nullable)

### Client-Side

1. **Script Initialization** (`templates/base.html`):
   - Sets `window.SECTION_508_ENABLED` from server-rendered value
   - Loads `section508.js` for additional functionality

2. **Section 508 Module** (`static/js/section508.js`):
   - Applies CSS classes and ARIA attributes
   - Provides API functions for fetching/updating status
   - Creates ARIA live region for screen reader announcements
   - Exports global functions for integration

3. **Settings Page** (`templates/settings.html`):
   - Interactive toggle switch
   - Updates via AJAX without page reload
   - Shows current status with environment indicator

## Compliance

This implementation addresses the following Section 508 requirements:

### §1194.22 Web-based Applications

- **(a) Text alternative**: All images and non-text content have alt text or ARIA labels
- **(b) Multimedia**: Text-to-Speech integration via Section 508 Agent
- **(c) Color independence**: Not reliant on color alone for information
- **(d) Readable without stylesheet**: Content is structured and readable
- **(i) Frames**: All frames are properly titled
- **(k) Skip navigation**: Skip links provided for repetitive content
- **(l) Title for documents**: All pages have descriptive titles

### WCAG 2.1 Level AA

- **1.4.3 Contrast**: Minimum contrast ratio 4.5:1 for normal text
- **2.1.1 Keyboard**: All functionality available via keyboard
- **2.4.3 Focus Order**: Logical focus order throughout interface
- **2.4.7 Focus Visible**: Enhanced focus indicators in 508 mode
- **3.2.1 On Focus**: No context changes on focus
- **4.1.2 Name, Role, Value**: All components have proper ARIA attributes

## Testing

### Manual Testing

1. **Keyboard Navigation**:
   ```bash
   # Enable 508 mode
   /settings 508 on
   
   # Navigate using Tab, Shift+Tab, Enter, Escape
   # Verify all interactive elements are reachable
   ```

2. **Screen Reader Testing**:
   - Test with NVDA (Windows), JAWS (Windows), or VoiceOver (macOS)
   - Verify all commands and responses are announced
   - Check ARIA live regions announce dynamic content

3. **Visual Testing**:
   - Verify larger text and spacing
   - Check focus indicators are visible
   - Test high contrast mode compatibility

### Automated Testing

```python
# Test Section 508 API endpoint
python manage.py test agent_app.tests.test_commands::TestSection508Settings

# Test command handler
/settings 508 on
/settings
/settings 508 off
```

## Browser Compatibility

Section 508 features are supported in:

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Android 90+)

## Related Documentation

- [TTS_INTEGRATION.md](./TTS_INTEGRATION.md) - Text-to-Speech integration details
- [COMMANDS.md](./COMMANDS.md) - Command system reference
- [agents/section508/SKILLS.md](../agents/section508/SKILLS.md) - Section 508 Agent capabilities
- [piper/README.md](../piper/README.md) - Text-to-Speech microservice

## Support

For accessibility issues or Section 508 compliance questions:

1. Use `/help` to see accessibility features
2. Check this documentation
3. Test with assistive technologies
4. Report issues with specific WCAG criteria

## Version History

- **v0.1.0** (2026-02) - Initial Section 508 mode implementation
  - Environment-based default
  - Per-user preference override
  - Command and UI toggle
  - CSS enhancements
  - Screen reader support
  - API endpoint
