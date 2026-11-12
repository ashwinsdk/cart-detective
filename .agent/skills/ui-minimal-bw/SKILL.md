# Skill: Minimalist Black and White UI Design

- **Name**: ui-minimal-bw
- **Description**: Build functional, high-density, accessible web interfaces strictly using monochrome and neutral gray palettes without marketing embellishments.

## When to Use
Use this skill for all frontend development, page styling, component crafting, and microcopy writing.

## Step by Step Procedure
1. Verify color tokens comply with `docs/UI_GUIDELINES.md`: use pure black, pure white, and neutral grays only.
2. Ensure all interactive borders use 1px width (`border border-neutral-200 dark:border-neutral-800`).
3. Set uniform subtle border radius (`rounded-sm` or `rounded-md`, maximum 6px).
4. Use Inter or Geist typography. Use monospace font for IDs, currency values, dates, and metrics.
5. Support system default theme, manual dark/light toggle, and prevent load flash by checking localStorage in the HTML head.
6. Check contrast ratios against WCAG AA standards (minimum 4.5:1 for body text).
7. Eliminate all banned patterns: no gradients, no glows, no blobs, no decorative icons, no emojis, no em dashes or en dashes.
8. Eliminate all banned words from labels, empty states, and error alerts.

## Code Patterns
```tsx
// Good: Minimalist card with crisp border and muted typography
export function ProductCard({ title, brand, price, score }: ProductCardProps) {
  return (
    <div className="border border-neutral-200 bg-white p-4 rounded-sm dark:border-neutral-800 dark:bg-neutral-900">
      <div className="text-xs uppercase tracking-wider text-neutral-500 font-mono">{brand}</div>
      <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mt-1">{title}</h3>
      <div className="mt-3 flex items-baseline justify-between">
        <span className="font-mono text-base font-semibold">{price}</span>
        <span className="font-mono text-xs text-neutral-500">Score: {score}/100</span>
      </div>
    </div>
  );
}
```

## Pitfalls
- Adding colorful badges or accent colors to make the UI look more flashy.
- Using decorative floating icons.
- Using em dashes in headings or copy: replace with commas, periods, or colons.
- Failing to style dark mode inputs and dropdowns to match the monochrome theme.

## Done Checklist
- [ ] Only black, white, and neutral gray tokens used.
- [ ] Dark and light themes render identically with high contrast.
- [ ] Zero emojis anywhere in component JSX or copy.
- [ ] Zero em dashes or en dashes in text.
- [ ] All icons sourced from Lucide React.
