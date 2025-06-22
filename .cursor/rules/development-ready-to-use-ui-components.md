---
trigger: model_decision
description: To ensure consistent and predictable placement of components, facilitating discoverability and maintainability. Apply these rules whenever creating a new React component or deciding where to place an existing one.
---

**Atomic Primitives (`src/components/ui/`)**
    *   **Rule:** Place small, highly reusable, generic UI elements here (e.g., `Button.tsx`, `Card.tsx`, `Input.tsx`, `Dialog.tsx`, `Icon.tsx`, `SplineScene.tsx`). These are the fundamental building blocks.
    *   **When to use:** If the component is a general-purpose UI element, often corresponding to a Shadcn/UI primitive or a similar custom-built atom.
2.  **Shared Common Components (`src/components/common/`)**
    *   **Rule:** Place components that are used in multiple places but are more complex than `ui` primitives, or specific to this application's common patterns (e.g., `Logo.tsx`, `SectionHeader.tsx`, `UserAvatar.tsx`). They may compose `ui` components.
    *   **When to use:** If the component is shared across different features or pages but isn't a basic UI primitive.
3.  **Layout Components (`src/components/layout/`)**
    *   **Rule:** Place components responsible for the main structure of pages (e.g., `Header.tsx`, `Footer.tsx`, `Sidebar.tsx`, `PageWrapper.tsx`, `GridContainer.tsx`).
    *   **When to use:** If the component defines a major layout area or a structural shell for content.
4.  **Composable UI Blocks (`src/components/blocks/[category]/`)**
    *   **Rule:** Place larger, pre-composed UI sections intended as "ready-made" segments for pages (e.g., `src/components/blocks/hero-banners/LuxuryCarHero.tsx`, `src/components/blocks/product-showcases/InteractiveShowcase.tsx`, `src/components/blocks/testimonials/CustomerStoriesSlider.tsx`).
    *   **Sub-folders:** Use a `[category]` subfolder for better organization (e.g., `hero-banners`, `feature-sections`, `cta-sections`).
    *   **When to use:** If the component is a significant, self-contained visual section of a page, often combining multiple `ui` and `common` components. This is key for "ready-made UI".
5.  **Feature-Specific Components (`src/components/features/[featureName]/`)**
    *   **Rule:** Place components that are tightly coupled to a specific application feature (e.g., `src/components/features/car-configurator/ColorPicker.tsx`, `src/components/features/booking-system/CalendarView.tsx`).
    *   **When to use:** If the component is part of a larger, distinct functionality and is unlikely to be used outside that feature's context.
6.  **Utilities (`src/lib/utils.ts`)**
    *   **Rule:** Place utility functions like `cn` (for merging class names) here.
    *   **When to use:** When needing helper functions, especially for styling or common logic.