---
trigger: model_decision
description: Apply these rules when the AI is tasked to create or locate the source code of a new reusable React component that will be used in the actual product pages (landing pages, product pages, etc.).
---

Atomic Primitives (src/components/ui/)
Rule: Place small, highly reusable, generic UI elements here (e.g., Button.tsx, Card.tsx, SplineScene.tsx).
When AI uses: When generating the source code for a fundamental UI building block.
Shared Common Components (src/components/common/)
Rule: Place components that are used in multiple places, more complex than ui, or specific to common app patterns (e.g., Logo.tsx, SectionHeader.tsx).
When AI uses: When generating the source code for a shared, non-primitive component.
Layout Components (src/components/layout/)
Rule: Place components responsible for main page structure (e.g., Header.tsx, Footer.tsx).
When AI uses: When generating the source code for a structural shell component.
Composable UI Blocks (src/components/blocks/[category]/)
Rule: Place larger, pre-composed UI sections (e.g., src/components/blocks/hero-banners/LuxuryCarHero.tsx). Use [category] subfolders.
When AI uses: When generating the source code for a significant, self-contained visual section of a page.
Feature-Specific Components (src/components/features/[featureName]/)
Rule: Place components tightly coupled to a specific application feature (e.g., src/components/features/car-configurator/ColorPicker.tsx).
When AI uses: When generating the source code for a component specific to a distinct application functionality.
Utilities (src/lib/utils.ts)
Rule: Place utility functions like cn.
When AI uses: When needing helper functions for components in src/components/.