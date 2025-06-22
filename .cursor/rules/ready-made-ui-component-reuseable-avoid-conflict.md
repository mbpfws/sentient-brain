---
trigger: model_decision
description: Apply these rules when the AI is implementing the visual aspects of any reusable React component whose source code resides in src/components/....
---

Rules:
Tailwind CSS & CSS Variables First:
Rule: Primarily use Tailwind CSS utility classes. Leverage pre-defined CSS variables from global.css or tailwind.config.js (e.g., bg-brand-navy, text-brand-gold, border-accent) for colors, fonts, spacing related to the theme.
When to use: Always, for any styling.
Minimal Intrinsic Styling:
Rule: Components (especially in ui/ and blocks/) should have minimal fixed styling that dictates their appearance outside their own scope (e.g., avoid hardcoding specific margins that affect page layout, or colors that aren't part of the base theme). Focus on internal layout (flex, grid) and essential base styles.
When to use: During initial component creation. The goal is a "blank slate" or "base themed" component.
className Prop for Customization:
Rule: Every component's root element (and potentially key internal elements if needed) MUST accept a className prop. Use the cn() utility from src/lib/utils.ts to merge these with base classes: className={cn('internal-base-styles', props.className)}.
When to use: For all components to allow external styling overrides and additions.
No Component-Scoped Global CSS:
Rule: AVOID defining global CSS selectors or creating separate CSS/SCSS module files for individual components unless absolutely necessary (e.g., for complex third-party library overrides) and explicitly instructed. Styling should be primarily via Tailwind utilities passed through props or defined with cn().
When to use: When considering writing custom CSS. Prefer Tailwind.
Shadcn/UI & Radix Philosophy:
Rule: Adhere to the Shadcn/UI approach: components are unstyled or minimally styled by default, and customized via Tailwind. For Radix Themes (if used), leverage its theming capabilities.
When to use: When creating or modifying components, especially those in src/components/ui/.
GSAP & Three.js Styling:
Rule: For GSAP animations, aim to animate Tailwind-compatible CSS properties. For Three.js, the React component hosting the <canvas> should accept a className prop to style its container (size, position). The 3D scene itself is managed by Three.js.
When to use: When integrating dynamic animations or 3D scenes.
Vietnamese Content via Props:
Rule: All display text (titles, descriptions, button labels, etc.) must be configurable via props (e.g., title: string, buttonText: string). Default prop values should be in Vietnamese as per design guidelines.
When to use: When a component includes any user-visible text.

Tailwind CSS & CSS Variables First.
Minimal Intrinsic Styling.
className Prop for Customization (using cn()).
No Component-Scoped Global CSS (for components in src/components/).
Shadcn/UI & Radix Philosophy.
GSAP & Three.js Styling (for components in src/components/).
Vietnamese Content via Props (for components in src/components/).