---
trigger: model_decision
description: ctivate this workflow when a prompt requests the creation of a new reusable component's source code or the integration/modification of an existing reusable component's source code located within src/components/....
---

Workflow Steps:
Analyze Request & Determine Component Type:
Action: Understand the component's purpose, complexity, and reusability.
Decision: Classify it as ui (primitive), common (shared), layout, block (section), or feature-specific.
Select Directory (Apply Rule Set 1):
Action: Choose the appropriate directory based on the component type determined in Step 1, following Rule Set 1: Directory Structure.
Implement Structure & Minimal Styles (Apply Rule Set 2):
Action: Create the JSX structure. Apply only essential base styles or "unstyle" it, adhering to Rule Set 2: Styling & Conflict Avoidance.
Key Focus: Ensure the className prop is implemented on the root element using cn().
Define Clear Props:
Action: Identify and define necessary props for:
Data: (e.g., title: string, items: Car[], imageUrl: string)
Configuration: (e.g., variant: 'dark' | 'light', layoutDirection: 'horizontal' | 'vertical')
Styling: (The className prop is mandatory).
Event Handlers: (e.g., onClick: () => void, onSubmit: (data: FormData) => void)
Content Language: Ensure text content is passed via props, with Vietnamese defaults if applicable (Rule 2.7).
Ensure Composability & Reusability:
Action: Design the component to be easily composed with others and reusable in different contexts. Avoid hardcoding dependencies on specific parent layouts unless it's a layout component itself.
Code Generation & Dependency Management:
Action: Generate the full TypeScript/TSX code. Identify and list any new NPM dependencies required.
Confirmation & Clarification (If Needed):
Action: If any rule seems conflicting with the prompt or if ambiguity exists, ask for clarification from the user before proceeding with full implementation. Example: "The request implies fixed padding, but Rule 2.2 suggests minimal intrinsic styling. Should page-level padding be applied via className when this component is used?"

