---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications. Discovers existing design systems and adapts accordingly. Generates creative, polished code that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---

# Frontend Design

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The skill adapts to existing design systems when present, and makes bold creative choices when building from scratch.

---

## Phase 1: Discovery (MANDATORY)

Before designing, discover what already exists in the project:

### 1.1 Design System Detection

```bash
# Check for design tokens
Glob("**/globals.css")
Glob("**/tailwind.config.*")
Glob("**/theme.ts")
Glob("**/tokens.css")

# Check for component library
Glob("**/components/ui/**")
Glob("**/components/common/**")
LS("src/components/") or LS("app/components/")

# Check for existing patterns
Grep("--primary|--accent|--neutral", "*.css")
Grep("colors:|fontFamily:", "tailwind.config.*")
```

### 1.2 What to Look For

| Asset | Where to Find | What It Tells You |
|-------|---------------|-------------------|
| CSS Variables | `globals.css`, `:root` | Color palette, spacing scale |
| Tailwind Config | `tailwind.config.js/ts` | Extended colors, fonts, custom utilities |
| Component Library | `components/ui/` | Existing patterns, shadcn/radix usage |
| Typography | Font imports, `font-*` classes | Font families in use |
| Existing Pages | `app/`, `pages/` | Layout patterns, spacing conventions |

### 1.3 Decision Point

**If design system exists:**
- Follow the established colors, fonts, and patterns
- Be creative WITHIN the system's constraints
- Maintain consistency with existing components
- Use existing utilities and classes

**If no design system (greenfield):**
- Make bold, intentional creative choices
- Establish patterns that can be reused
- Document your choices for consistency

---

## Phase 2: Design Thinking

Before coding, understand the context and commit to a clear direction:

- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick a direction that fits the context:
  - Brutally minimal, maximalist, retro-futuristic
  - Organic/natural, luxury/refined, playful/toy-like
  - Editorial/magazine, brutalist/raw, art deco/geometric
  - Soft/pastel, industrial/utilitarian
- **Constraints**: Technical requirements (framework, performance, accessibility)
- **Differentiation**: What makes this UNFORGETTABLE?

**Key insight**: Bold maximalism and refined minimalism both work. The key is *intentionality*, not intensity.

---

## Phase 3: Implementation

Implement working code that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

### Typography

- **If project has fonts**: Use them consistently
- **If choosing fonts**: Pick distinctive, characterful choices
  - Pair a display font (headings) with a body font (content)
  - Avoid overused fonts: Inter, Roboto, Arial, system defaults
  - Consider: serif for elegance, geometric sans for modern, humanist for warmth

### Color

- **If project has palette**: Use the defined tokens (`--primary-*`, `--neutral-*`)
- **If choosing colors**: Commit to a cohesive scheme
  - Dominant color with sharp accents outperforms timid, evenly-distributed palettes
  - Use CSS variables for consistency
  - Consider dark/light mode from the start

### Layout & Spacing

- **If project has scale**: Follow the spacing tokens
- **If choosing**: Be intentional about density
  - Generous negative space OR controlled density (pick one)
  - Unexpected layouts: asymmetry, overlap, diagonal flow
  - Grid-breaking elements for visual interest

### Motion & Animation

- Prioritize CSS-only solutions when possible
- Focus on high-impact moments:
  - Page load with staggered reveals (`animation-delay`)
  - Hover states that surprise
  - Scroll-triggered effects
- One well-orchestrated animation > scattered micro-interactions

### Backgrounds & Depth

Create atmosphere rather than defaulting to solid colors:
- Gradient meshes, noise textures, geometric patterns
- Layered transparencies, dramatic shadows
- Decorative borders, grain overlays
- Match the overall aesthetic

---

## Anti-Patterns (NEVER DO)

### Generic AI Aesthetics
- Overused fonts (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (purple gradients on white backgrounds)
- Predictable layouts and cookie-cutter patterns
- Safe choices that lack context-specific character

### Implementation Mistakes
- Inline styles instead of utility classes (unless dynamic values)
- Hardcoded colors instead of tokens (`#14b88c` → `primary-500`)
- Ignoring existing component library
- Nested cards (Card inside Card)
- Scattered, purposeless micro-interactions

### Breaking Existing Patterns
- Using different fonts than the project defines
- Creating new color values when tokens exist
- Building components that exist in the library
- Inconsistent spacing and sizing

---

## Adaptation Examples

### Scenario A: Project Has Design System

```
Discovery found:
- CSS variables: --primary-500, --neutral-*, --accent-*
- Fonts: Crimson Pro (serif), DM Sans (sans)
- Component library: shadcn/ui in components/ui/
- Animation classes: animate-fade-in, stagger-*

Action:
- Use these exact tokens and patterns
- Import from existing component library
- Apply existing animation utilities
- Be creative with layout and composition
```

### Scenario B: Greenfield Project

```
Discovery found:
- Basic Tailwind config (no customization)
- No component library
- No established patterns

Action:
- Make bold choices: pick distinctive fonts, define color palette
- Establish component patterns for reuse
- Create CSS variables for new tokens
- Document choices in comments or design notes
```

---

## Quality Checklist

Before considering the design complete:

- [ ] Discovered and followed existing design system (if present)
- [ ] Typography is intentional and consistent
- [ ] Color palette is cohesive with clear hierarchy
- [ ] Spacing follows a consistent scale
- [ ] Animations are purposeful, not decorative
- [ ] Responsive behavior is considered
- [ ] Accessibility basics (contrast, focus states, semantic HTML)
- [ ] No generic AI aesthetics

---

## Creative Freedom

Remember: Claude is capable of extraordinary creative work. Within the constraints of any project, there is always room for:

- Typography mixing and expressive type choices
- Spatial composition and visual rhythm
- Animation timing and choreography
- Color intensity and contrast decisions
- Unexpected details that delight

Don't hold back. Show what can truly be created when thinking outside the box and committing fully to a distinctive vision.
