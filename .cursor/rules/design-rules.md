---
trigger: model_decision
description: When it comes to user interfaces design or styling
---


## 2. Overall Design Philosophy

* **Luxury First:** Every design decision must reinforce a sense of exclusivity, premium quality, and sophistication. The aesthetic should be bold, high-end, and appeal to discerning, high-spending clients.
* **Modern & Minimalist:** Embrace a clean, contemporary design language. Avoid clutter and focus on clear visual hierarchy.
* **Visually Driven:** Prioritize high-impact visuals (images, videos, 3D elements) to showcase the product's excellence.
* **Immersive Experiencnimat engated:*ve. A 100m (TaiSS ut(padding, margin, gaps). Define standard spacing values in `tailwind.config.js` if necessary, but prefer Tailwind's default scale where appropriate.
* **Mobile-First Approach:** Design and implement components for mobile screens first, then scale up to tablet and desktop using Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`, `2xl:`).
* **Grid System:** Employ Tailwind's grid system (`grid`, `grid-cols-*`, `gap-*`) for structuring page layouts and component arrangements.
* **Generous Whitespace (Negative Space):** Use ample whitespace to create a breathable, uncluttered, and luxurious feel. This helps in focusing user attention on key content and visuals.
    * *Instruction for AI Builder:* Apply larger padding and margin values consistently across sections and elements (e.g., `py-12 md:py-16`, `px-6 md:px-8`, `mb-8 md:mb-12`).
* **Max Width:** Content sections on larger screens should have a `max-width` (e.g., `max-w-7xl`) and be centered to ensure readability and prevent overly wide text lines.

## 4. Typography (Next/Font & TailwindCSS)

* **Font Selection:**
    * Define primary and secondary fonts in `tailwind.config.js` using `@next/font` for optimal performance and to avoid layout shifts.
    * Choose elegant, modern sans-serif fonts that convey luxury and are highly legible (e.g., Montserrat, Lato, Raleway, or specified brand fonts).
* **Hierarchy:** Establish a clear typographic hierarchy using TailwindCSS utility classes for headings (`h1` to `h6`), body text, and captions.
    * *Instruction for AI Builder:* Example hierarchy:
        * `h1`: `text-4xl md:text-5xl font-bold text-brand-gold`
        * `h2`: `text-3xl md:text-4xl font-semibold text-white`
        * `h3`: `text-2xl md:text-3xl font-medium text-gray-200`
        * Body: `text-base md:text-lg text-gray-300 leading-relaxed`
* **Readability:** Ensure sufficient line height (`leading-relaxed` or `leading-loose`) and appropriate letter spacing for body text.
* **Responsiveness:** Text sizes should adapt gracefully across different screen sizes. Use responsive prefixes for font sizes if necessary.

## 5. Color Palette (TailwindCSS)

* **Primary Colors:** Deep, rich blues or dark charcoals for backgrounds to evoke sophistication. (e.g., `bg-brand-blue` like `#0A192F`).
* **Accent Colors:** Gold, champagne, or bronze tones for CTAs, highlights, icons, and key interactive elements. (e.g., `text-brand-gold` like `#B08D57`). Ensure accents are used purposefully and not excessively.
* **Secondary Colors:** Neutral grays, off-whites for text, secondary elements, and subtle backgrounds. (e.g., `text-gray-300`, `bg-gray-800/50`).
* **Color Definition:** Define all brand-specific colors in `tailwind.config.js` under `theme.extend.colors`.
    * *Instruction for AI Builder:* `colors: { 'brand-blue': '#0A192F', 'brand-gold': '#B08D57', 'brand-light-gold': '#D4AF37', 'neutral-text': '#E5E7EB' }`
* **Contrast:** Ensure sufficient color contrast for readability and accessibility (WCAG AA).

## 6. Component Styling (Shadcn-ui & TailwindCSS)

* **Shadcn-ui Foundation:** Utilize Shadcn-ui components as the base for UI elements. Install components using the Shadcn UI CLI.
* **Customization:** Extensively customize Shadcn-ui components using TailwindCSS utility classes to align with the brand's luxury aesthetic. Modify `components.json` as needed for consistent styling.
    * *Instruction for AI Builder:* When adding a Shadcn-ui component, immediately review its default styling and apply custom Tailwind classes to elements like backgrounds, borders, text colors, and hover states to match the luxury theme. For instance, `Button` variants should reflect the brand's color scheme (e.g., a primary gold button with dark text).
* **Cards:** Use `Card` components for showcasing products, features, or testimonials. Style them with subtle borders, custom backgrounds (potentially semi-transparent with backdrop blur for a modern effect), and refined shadows.
* **Forms:** Style `Input`, `Select`, `Textarea`, `Checkbox` components from Shadcn-ui for a clean, premium look. Ensure focus states are clear and visually appealing using accent colors.
* **Buttons:**
    * Primary CTAs: Use the brand's accent gold color.
    * Secondary buttons: More subtle styling, perhaps ghost buttons or outline styles with accent color.
    * Ensure hover and active states are defined and provide clear visual feedback.
* **Modals/Dialogs/Sheets:** Use Shadcn-ui `Dialog`, `Sheet`. Ensure they have a sophisticated appearance, potentially with a dark, slightly transparent overlay.
* **Carousel/Sliders:** For image galleries, use Shadcn-ui `Carousel` or a well-vetted, performant alternative. Ensure smooth transitions and intuitive navigation.

## 7. Imagery & Media

* **Quality:** All images and videos must be of the highest professional quality—crisp, well-lit, and visually stunning.
* **Optimization:**
    * Use Next.js `<Im