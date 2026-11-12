# UI and Design Guidelines: Cart Detective

This document defines the strict black-and-white minimalist design system for Cart Detective. All frontend components and copy must adhere to these rules.

## 1. Visual Philosophy

- **Tone**: Functional, objective, journalistic, austere.
- **Palette**: Strictly monochrome and neutral grays. High contrast black and white surfaces.
- **Surface Elevation**: Minimal elevation. Use thin 1px borders (`border border-neutral-200 dark:border-neutral-800`) instead of heavy drop shadows or blurred cards.
- **Borders and Radii**: Uniform small border radius (`rounded-sm` or `rounded-md`, maximum 6px).

---

## 2. Color Tokens

### Light Theme
- Background: `#FFFFFF` (`bg-white`)
- Secondary Surface: `#F9F9F9` (`bg-neutral-50`)
- Border / Divider: `#E5E5E5` (`border-neutral-200`)
- Primary Text: `#0A0A0A` (`text-neutral-950`)
- Muted / Secondary Text: `#525252` (`text-neutral-600`)
- Tertiary / Caption Text: `#737373` (`text-neutral-500`)

### Dark Theme
- Background: `#0A0A0A` (`bg-neutral-950`)
- Secondary Surface: `#141414` (`bg-neutral-900`)
- Border / Divider: `#262626` (`border-neutral-800`)
- Primary Text: `#F5F5F5` (`text-neutral-100`)
- Muted / Secondary Text: `#A3A3A3` (`text-neutral-400`)
- Tertiary / Caption Text: `#737373` (`text-neutral-500`)

### Functional State Tokens (Muted Only)
- Success: Muted green text/border (`#15803d` on light, `#4ade80` on dark) or neutral badge with label "Verified".
- Warning: Muted amber text/border (`#b45309` on light, `#fbbf24` on dark) or neutral badge with label "Unverified".
- Destructive / Error: Muted red text/border (`#b91c1c` on light, `#f87171` on dark).
- Never use saturated neon fills, pulsing animations, or gradient badges.

---

## 3. Typography Scale

- **Font Family**: Inter or Geist, fallback system-ui.
- **Heading 1**: 24px (1.5rem), font-semibold, tracking-tight.
- **Heading 2**: 18px (1.125rem), font-medium, tracking-tight.
- **Heading 3**: 15px (0.9375rem), font-medium.
- **Body**: 13px or 14px (0.875rem), font-normal, line-height 1.5.
- **Data / Monospace**: 12px (0.75rem), `font-mono` for IDs, prices, dates, confidence scores.

---

## 4. Prohibited Design Patterns (Strict Ban List)

- **No Emojis**: Never render emojis in any UI component, badge, label, tooltip, or empty state.
- **No Em or En Dashes**: Use commas, colons, or periods in all microcopy and labels.
- **No AI Slop**:
  - No background gradients (linear or radial).
  - No glow effects or box-shadow blooms.
  - No glassmorphism (`backdrop-blur` with translucent gradients).
  - No floating animated blobs or particle effects.
  - No sparkle or wand icons.
  - No decorative stock hero illustrations.
- **Banned Marketing Terms**: Never use words such as "seamless", "unleash", "supercharge", "elevate", "revolutionary", "game-changer", "magic", "effortless", or "intelligent". Copy must be factual, concise, and direct.

---

## 5. Component Standards

- **Buttons**: Flat solid monochrome (`bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-950`) or outline (`border border-neutral-300 dark:border-neutral-700`).
- **Icons**: Lucide React line icons exclusively, sized 14px to 16px with 1.5px stroke width. Never use decorative icons.
- **Empty States**: Clear factual description of why the section is empty and one direct action button.
- **Loading States**: Restrained neutral skeletons or small monochrome spinners. No bouncy or playful animations.
- **Theme Switching**: Handled via class `dark` on `document.documentElement` with `localStorage` persistence and immediate theme resolution script to prevent flash of unstyled content.
