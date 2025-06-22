---
trigger: model_decision
description: Defines the typography system for the DE-limousine website, focusing on Vietnamese language support, luxury, and modern aesthetics.
---

# Vietnamese Typography Rules for DE-Limousine

This document outlines the typographic standards to ensure a consistent, luxurious, modern, and legible visual identity across the DE-limousine website, with a strong emphasis on beautiful Vietnamese rendering.

## 1. Chosen Fonts

We will utilize fonts from Google Fonts for optimal performance and ease of integration with Next.js (`next/font/google`).

*   **Primary Heading Font:** **Darker Grotesque**
    *   **Weights to be used:** Bold (700), ExtraBold (800), Black (900) for primary headings; SemiBold (600) for secondary headings or less emphasized titles.
    *   **Characteristics:** Contemporary grotesque, strong character, excellent Vietnamese support. Ideal for impactful, luxurious headlines.
*   **Secondary & Body Text Font:** **Be Vietnam Pro**
    *   **Weights to be used:** Regular (400) for body text; Medium (500) or SemiBold (600) for sub-headings, UI elements, captions, or emphasized body text.
    *   **Characteristics:** Clean, modern sans-serif, highly legible, excellent Vietnamese support, versatile range of weights.

## 2. Typographic Scale & Hierarchy

The following scale provides a baseline. Sizes are in `rem` for accessibility and scalability. Line heights are unitless (relative to font size). Letter spacing can be adjusted for larger display text to improve readability and aesthetic appeal.

**Base Font Size:** `16px` (for `1rem` calculation)

---

### **H1 - Primary Page Titles / Hero Headlines**
*   **Font Family:** 'Darker Grotesque', sans-serif
*   **Font Size:** `clamp(2.5rem, 5vw + 1rem, 4.5rem)` (Responsive: min 40px, scales with viewport width, max 72px)
*   **Font Weight:** 800 (ExtraBold) or 900 (Black)
*   **Line Height:** 1.1 - 1.2
*   **Letter Spacing:** -0.02em to -0.03em (slight tightening for large display text)
*   **Case:** Sentence case or Title Case (as per design context). Avoid all caps for long H1s in Vietnamese due to diacritics.
*   **Color:** `var(--text-primary)` or `var(--brand-accent)` (e.g., `var(--brand-gold)`)

---

### **H2 - Major Section Titles**
*   **Font Family:** 'Darker Grotesque', sans-serif
*   **Font Size:** `clamp(2rem, 4vw + 0.8rem, 3rem)` (Responsive: min 32px, scales, max 48px)
*   **Font Weight:** 700 (Bold) or 800 (ExtraBold)
*   **Line Height:** 1.2 - 1.3
*   **Letter Spacing:** -0.01em to -0.02em
*   **Case:** Sentence case or Title Case.
*   **Color:** `var(--text-primary)`

---

### **H3 - Sub-Section Titles / Prominent Labels**
*   **Font Family:** 'Darker Grotesque', sans-serif
*   **Font Size:** `clamp(1.5rem, 3vw + 0.6rem, 2.25rem)` (Responsive: min 24px, scales, max 36px)
*   **Font Weight:** 600 (SemiBold) or 700 (Bold)
*   **Line Height:** 1.3 - 1.4
*   **Letter Spacing:** Normal or -0.01em
*   **Case:** Sentence case or Title Case.
*   **Color:** `var(--text-secondary)` or `var(--text-primary)`

---

### **H4 - Minor Headings / Card Titles**
*   **Font Family:** 'Be Vietnam Pro', sans-serif
*   **Font Size:** `clamp(1.125rem, 2vw + 0.5rem, 1.5rem)` (Responsive: min 18px, scales, max 24px)
*   **Font Weight:** 600 (SemiBold)
*   **Line Height:** 1.4 - 1.5
*   **Letter Spacing:** Normal
*   **Case:** Sentence case.
*   **Color:** `var(--text-primary)`

---

### **Body Text (Paragraphs, Descriptions)**
*   **Font Family:** 'Be Vietnam Pro', sans-serif
*   **Font Size:** `1rem` (16px) to `1.125rem` (18px). Consider `clamp(0.9rem, 1.5vw + 0.5rem, 1.125rem)` for slight responsiveness.
*   **Font Weight:** 400 (Regular)
*   **Line Height:** 1.5 - 1.7 (crucial for Vietnamese readability with diacritics)
*   **Letter Spacing:** Normal
*   **Color:** `var(--text-body)` or `var(--text-secondary)`
*   **Max Width:** Apply a `max-width` (e.g., `65ch` to `75ch`) to paragraphs for optimal readability.

---

### **Subtext / Captions / UI Labels**
*   **Font Family:** 'Be Vietnam Pro', sans-serif
*   **Font Size:** `0.875rem` (14px) or `0.75rem` (12px)
*   **Font Weight:** 400 (Regular) or 500 (Medium)
*   **Line Height:** 1.4 - 1.6
*   **Letter Spacing:** Normal or +0.01em (for very small text if needed)
*   **Case:** Sentence case or UPPERCASE (for specific UI labels like "NEW").
*   **Color:** `var(--text-muted)` or `var(--text-secondary)`

---

## 3. Styling & Usage Notes

*   **Color:**
    *   Prioritize high contrast for accessibility.
    *   Use CSS variables defined in `globals.css` (e.g., `var(--text-primary)`, `var(--text-secondary)`, `var(--brand-accent)`).
    *   **Gradient Text:** If used, ensure sufficient contrast and apply sparingly to H1 or very prominent short H2s.
        ```css
        .gradient-text {
          background: linear-gradient(to right, var(--gradient-start), var(--gradient-end));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          text-fill-color: transparent;
        }
        ```

*   **Alignment:**
    *   **Left-alignment** is generally preferred for body text in Vietnamese for optimal readability.
    *   Headings (H1, H2, H3) can be left-aligned or centered depending on the section layout and design intent. Avoid justifying long passages of Vietnamese text as it can create uneven spacing.

*   **Line Breaks (Vietnamese Specific):**
    *   Vietnamese is a syllabic language. While automatic line breaking is usually sufficient, be mindful of awkward breaks within multi-syllable words if manual adjustments are ever needed (rare in web).
    *   Ensure ample `line-height` to accommodate diacritical marks comfortably without them clashing with lines above or below. The recommended `line-height` values should address this.

*   **Consistency:**
    *   Adhere strictly to this typographic scale and style guide across all pages and components to maintain a cohesive and professional user experience.
    *   Any deviations should be well-justified and discussed.

*   **Responsiveness:**
    *   The `clamp()` function is recommended for fluid typography for headings.
    *   Test thoroughly on various screen sizes to ensure readability and aesthetic balance.

## 4. Implementation in Next.js

In your `src/app/layout.tsx` or a dedicated `src/styles/fonts.ts` file:

```typescript
// Example: src/styles/fonts.ts
import { Darker_Grotesque, Be_Vietnam_Pro } from 'next/font/google';

export const darker_grotesque = Darker_Grotesque({
  subsets: ['latin', 'vietnamese'],
  variable: '--font-darker-grotesque',
  weight: ['600', '700', '800', '900'], // Select weights you'll use
  display: 'swap',
});

export const be_vietnam_pro = Be_Vietnam_Pro({
  subsets: ['latin', 'vietnamese'],
  variable: '--font-be-vietnam-pro',
  weight: ['400', '500', '600'], // Select weights you'll use
  display: 'swap',
});
```

In your `globals.css`:

```css
/* globals.css */
:root {
  --font-darker-grotesque: ${darker_grotesque.variable};
  --font-be-vietnam-pro: ${be_vietnam_pro.variable};

  /* Other color and spacing variables */
  --text-primary: #1a1a1a; /* Example dark text */
  --text-secondary: #4a4a4a; /* Example medium-dark text */
  --text-body: #333333;
  --text-muted: #7a7a7a;
  --brand-accent: #DAA520; /* Example gold */
  /* ... other variables ... */
}

body {
  font-family: var(--font-be-vietnam-pro); /* Default body font */
  color: var(--text-body);
}

h1, h2, h3 {
  font-family: var(--font-darker-grotesque);
}

/* You can then apply specific weights/styles in component CSS or utility classes */
```

In your `src/app/layout.tsx`:

```typescript
// src/app/layout.tsx
import { darker_grotesque, be_vietnam_pro } from '@/styles/fonts'; // Adjust path if needed
import './globals.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${darker_grotesque.variable} ${be_vietnam_pro.variable}`}>
      <body>{children}</body>
    </html>
  );
}
```

This setup makes the font families available via CSS variables throughout your application.