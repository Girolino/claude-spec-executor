# Visual QA Skill

Verify UI components render correctly using Claude in Chrome.

## When to Use

**Always run /visual-qa for:**
- New components (any new UI element)
- Layout restructuring
- New interactive states (hover, loading, error)
- Responsive breakpoint changes

**Skip for minor edits** (mark task complete with "skipped - minor edit"):
- CSS class rename
- Padding/margin tweaks (< 8px)
- Color adjustments
- Text/copy changes
- Import reorganization

## Execution Steps

### 1. Determine What to Verify

From the task context, identify:
- Component/page being tested
- Where it's rendered (preview route, page, storybook)
- What specifically to check

### 2. Navigate and Screenshot

```
1. Use mcp__claude-in-chrome__tabs_context_mcp to get browser context
2. Create new tab if needed with mcp__claude-in-chrome__tabs_create_mcp
3. Navigate to the preview route or page where component is visible
4. Take screenshot with mcp__claude-in-chrome__computer action="screenshot"
```

### 3. Visual Verification Checklist

Check the screenshot for:

**Layout**
- [ ] Component renders without visual glitches
- [ ] Proper spacing and alignment
- [ ] No overlapping elements

**Responsiveness** (if applicable)
- [ ] Resize window to mobile width (375px)
- [ ] Take another screenshot
- [ ] Verify layout adapts correctly

**States** (if applicable)
- [ ] Hover states work (use computer action="hover")
- [ ] Loading states display correctly
- [ ] Error states render properly

**Accessibility**
- [ ] Text is readable (contrast)
- [ ] Interactive elements are visible
- [ ] Focus states work (tab through)

### 4. Report Results

**If OK:**
```
Visual QA passed for [Component]:
- Layout renders correctly
- [Any specific observations]
```

**If Issues Found:**
```
Visual QA found issues for [Component]:
- [Issue 1]: [Description]
- [Issue 2]: [Description]

Recommend: [Fix suggestion]
```

## Common Preview Routes

Check project for:
- `/_design-preview` or `/_design-guidelines-preview`
- `/storybook`
- Component-specific test routes
- The actual page where component is used

## Example Usage

```
Task: "Visual QA for Button - run /visual-qa if significant UI change, skip if trivial"

Context: Created new Button component with loading states

Action:
1. Navigate to /_design-preview#button
2. Screenshot default state
3. Trigger loading state, screenshot
4. Verify both render correctly
5. Report: "Visual QA passed - Button renders correctly in default and loading states"
```

## Quick Skip Template

For trivial changes, just mark the task complete:

```
Visual QA skipped - trivial change (CSS class rename only)
```
