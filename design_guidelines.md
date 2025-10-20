# Design Guidelines: Web Automation Platform

## Design Approach

**Selected Approach:** Design System + Developer Tool Reference
**Justification:** Utility-focused automation platform for technical users prioritizing efficiency, data clarity, and functional reliability over visual flair.

**Key References:**
- Linear: Clean typography, subtle interactions, functional aesthetics
- VS Code: Developer-familiar patterns, dark mode excellence
- Vercel Dashboard: Modern data presentation, clear status indicators

**Core Principles:**
1. Function over form - every element serves a purpose
2. Information density without clutter
3. Instant feedback on execution states
4. Scannable data structures
5. Technical precision in UI feedback

---

## Color Palette

**Dark Mode (Primary):**
- Background: 222 14% 8% (deep neutral)
- Surface: 222 13% 11% (card backgrounds)
- Border: 217 10% 20% (subtle divisions)
- Text Primary: 210 20% 98%
- Text Secondary: 215 16% 65%

**Accent Colors:**
- Primary: 217 91% 60% (blue - actions, links)
- Success: 142 71% 45% (green - completed runs)
- Warning: 38 92% 50% (amber - pending/in-progress)
- Error: 0 84% 60% (red - failed assertions)
- Info: 199 89% 48% (cyan - informational states)

**Light Mode:**
- Background: 0 0% 100%
- Surface: 210 20% 98%
- Border: 214 15% 88%
- Text Primary: 222 14% 8%
- Text Secondary: 215 16% 45%

---

## Typography

**Font Families:**
- Interface: Inter (Google Fonts) - primary UI text
- Monospace: JetBrains Mono (Google Fonts) - code, logs, JSON

**Type Scale:**
- Display: text-2xl font-semibold (command headers)
- Heading: text-lg font-medium (section titles)
- Body: text-sm font-normal (primary content)
- Caption: text-xs font-normal (metadata, timestamps)
- Code: text-sm font-mono (logs, selectors, JSON)

**Weights:** 400 (normal), 500 (medium), 600 (semibold)

---

## Layout System

**Spacing Primitives:** Use Tailwind units of 2, 3, 4, 6, 8, 12, 16
- Tight spacing: p-2, gap-2 (within components)
- Standard spacing: p-4, gap-4 (between elements)
- Section spacing: p-6, p-8 (major sections)
- Page margins: p-12, p-16 (outer containers)

**Grid Structure:**
- Main container: max-w-7xl mx-auto
- Sidebar: w-64 (run history/navigation)
- Content area: flex-1 (command input, results, logs)
- Data tables: w-full with horizontal scroll on overflow

---

## Component Library

### Navigation & Structure
- **Top Bar:** Fixed header with logo, navigation, user menu (h-14)
- **Sidebar:** Collapsible run history panel with status badges
- **Main Workspace:** Split view - command input (30%) + results (70%)

### Command Input
- **Text Area:** Large, auto-expanding input with placeholder examples
- Subtle border focus: ring-2 ring-primary
- Character count indicator (text-xs text-secondary)
- Submit button: Primary blue, disabled state when empty

### Execution Dashboard
- **Status Cards:** Grid of metrics (total runs, success rate, active executions)
- **Run Timeline:** Vertical list with timestamp, status badge, duration
- **Live Logs:** Terminal-style scrolling output with syntax highlighting
- **Progress Bar:** Linear indicator during execution with percentage

### Data Display
- **Results Table:** 
  - Striped rows (bg-surface alternating)
  - Sortable columns with arrow indicators
  - Selectable rows with checkbox
  - Fixed header on scroll
  - Column resize handles
  
- **Assertion Cards:**
  - Icon + status (checkmark/X) + assertion type
  - Expected vs Actual values in monospace
  - Timestamp and element selector reference

- **Screenshot Gallery:** Thumbnail grid with lightbox expansion

### Status Indicators
- **Badges:** Rounded-full px-2.5 py-0.5 with semantic colors
  - Running: bg-warning/10 text-warning border-warning/20
  - Success: bg-success/10 text-success border-success/20
  - Failed: bg-error/10 text-error border-error/20
  - Queued: bg-info/10 text-info border-info/20

### Forms & Inputs
- **Input Fields:** 
  - Border: border-border rounded-md
  - Focus: ring-2 ring-primary border-transparent
  - Height: h-10 (standard), h-8 (compact)
  - Background matches theme (surface color)

### Modals & Overlays
- **Command History Modal:** Centered overlay with recent executions
- **Export Dialog:** Format selection (JSON/CSV) + date range filter
- **Run Details Drawer:** Slide-in panel from right with full execution log

### Buttons
- **Primary:** bg-primary text-white hover:bg-primary/90
- **Secondary:** bg-surface border-border hover:bg-border/50
- **Ghost:** hover:bg-surface (for icon actions)
- **Destructive:** bg-error text-white hover:bg-error/90

### Data Visualization
- **Execution Timeline:** Horizontal bars showing step duration
- **Success Rate Chart:** Simple line graph (last 30 runs)
- **Element Selector Tree:** Collapsible hierarchy view

---

## Interaction Patterns

### Feedback Mechanisms
- Loading states: Pulsing skeleton screens (animate-pulse)
- Success notifications: Toast in top-right (green border-l-4)
- Error messages: Inline below inputs + toast for critical errors
- Hover states: Subtle bg-surface transition on interactive elements

### Keyboard Navigation
- Cmd/Ctrl + K: Focus command input
- Cmd/Ctrl + Enter: Submit command
- Escape: Close modals/drawers
- Tab navigation through all interactive elements

### Animations
**Minimal & Purposeful:**
- Transitions: transition-colors duration-200 (state changes)
- Slide-ins: translate-x-0 transition-transform (drawers)
- Fade: opacity transitions for notifications
- NO complex animations, parallax, or decorative motion

---

## Accessibility

- Maintain WCAG AA contrast ratios (4.5:1 minimum)
- All interactive elements keyboard accessible
- ARIA labels on icon-only buttons
- Screen reader announcements for status changes
- Focus visible indicators (ring-2 ring-offset-2)
- Dark mode default with consistent implementation across all components

---

## Images

**No hero images required.** This is a utility application focused on function.

**Functional Images:**
- **Screenshots:** Captured during automation runs, displayed in results section
- **Status Icons:** Heroicons for checkmarks, errors, info badges
- **Empty States:** Simple SVG illustrations (optional) for "No runs yet" messages

---

## Export & Download Elements

- **Export Buttons:** Secondary style with download icon
- **Format Indicators:** Small badges showing JSON/CSV file type
- **Download Progress:** Linear progress bar with file size indication

This design system prioritizes clarity, speed, and technical precision - empowering users to create and monitor browser automations without UI friction.