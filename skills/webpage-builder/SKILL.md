---

name: webpage-builder

description: Use when building or extending a Next.js site that should follow the project-a-next Swedish B2B e-commerce design language, component patterns, aesthetic direction, and technical stack.

---

&#x20;

\# Webpage Builder Skill: project-a-next Design System

&#x20;

\## Overview

&#x20;

This skill captures the precise design language, component patterns, and technical architecture

derived from building the project-a-next website for project-a Trading AB — a Swedish B2B wholesaler.

The user has strong aesthetic opinions and iterates toward minimalism, dark luxury, and sharp

contrast. Every choice documented here is the result of explicit user feedback and refinement.

&#x20;

\---

&#x20;

\## Tech Stack

&#x20;

| Layer        | Technology                             |

|--------------|----------------------------------------|

| Framework    | Next.js (App Router, server + client)  |

| Styling      | Tailwind CSS                           |

| CMS          | Payload CMS v3 (globals + collections) |

| Database     | MongoDB Atlas                          |

| Fonts        | Google Fonts via `next/font/google`    |

| Language     | TypeScript                             |

| Deployment   | Vercel (via `main` branch)             |

&#x20;

\---

&#x20;

\## Design Philosophy

&#x20;

\### Core Aesthetic: "Dark Luxury Minimalism"

The user strongly prefers a \*\*dark, premium, minimalist\*\* aesthetic. Key principles:

\- \*\*Black background\*\* everywhere (`bg-black`). Never white or light themes.

\- \*\*Maximum whitespace\*\* — layouts breathe. Remove clutter aggressively.

\- \*\*No decorative boxes or cards\*\* by default — use plain lists, underlines, and spacing instead.

\- \*\*Information hierarchy\*\* communicated through typography scale alone, not containers.

\- \*\*Remove everything that is not strictly necessary.\*\* If it looks redundant, it is.

&#x20;

\### Color Philosophy: Logo-Derived Accent System

&#x20;

> \*\*Important:\*\* The orange `#F27722` used throughout this project is specific to project-a Trading AB because it is the most prominent, characteristic color in their logo. The \*\*principle\*\* generalizes: always extract the most distinctive, saturated color from the brand's logo and use it as the single accent color throughout the site. Do not use browser defaults or generic colors — use the brand's own visual identity as the source of truth.

&#x20;

\#### Deriving the Accent Color

1\. Look at the logo — find the most \*\*characteristic, saturated, and distinctive\*\* color.

2\. Use that color as the \*\*single accent\*\* for all interactive elements, underlines, hover states, CTAs, and decorative dividers.

3\. Apply it sparingly but consistently — not everywhere, but as a "pop" on specifically chosen elements for visual impact.

4\. Keep everything else monochromatic (black backgrounds, white/gray text, zinc borders).

&#x20;

\#### "Pop" Placement Strategy — Where to Apply the Accent

The accent color should appear at \*\*high-impact, attention-directing\*\* spots only:

| Element                        | Usage                                               |

|-------------------------------|-----------------------------------------------------|

| Page title divider bar        | `w-24 h-1 bg-\[accent] mx-auto rounded-full`         |

| Active/hover nav links         | Text color change to accent                         |

| Nav active underline           | 2px expanding underline in accent                   |

| Category hover underline       | Expanding bottom underline in accent                |

| Nav rollout tab (if animated)  | Entire tab shape in accent color                    |

| CTA section background         | Full-width accent color panel                       |

| Carousel section title         | Heading in accent color                             |

| Submit buttons                 | `bg-\[accent] hover:bg-white`                        |

| Icon accents (SVG + social)   | `text-\[accent]` for icon                            |

| Input focus border             | Bottom border changes to accent on focus             |

| Carousel nav arrows            | Accent color, white on hover                        |

| Dropdown option hover          | `hover:bg-\[accent] hover:text-black`                |

&#x20;

\#### For project-a-next specifically:

| Role           | Value         | Usage                                            |

|----------------|---------------|--------------------------------------------------|

| Background     | `#000000`     | All page backgrounds                             |

| Surface Dark   | `zinc-900`    | Subtle sections, gradient starts                 |

| Accent Primary | `#F27722`     | Orange — logo-derived signature accent           |

| Text Primary   | `#ffffff`     | Headlines, key content                           |

| Text Secondary | `gray-300`    | Body text, descriptions                          |

| Text Muted     | `gray-400`    | Labels, metadata, captions                       |

| Text Dim       | `zinc-600/700`| Placeholders, disabled states                    |

| Border         | `zinc-800`    | Very subtle separators (bottom borders only)     |

&#x20;

\### Spacing \& Density

\- \*\*Compact is correct.\*\* Prefer tight padding over generous whitespace on content sections.

\- Page sections use `py-12 md:py-16` max in hero areas.

\- Lists and content follow `pt-0 pb-4 md:pb-8` — moved as high as possible.

\- Remove vertical padding between related elements. The user explicitly asked to "move content up" multiple times.

&#x20;

\---

&#x20;

\## Typography

&#x20;

\### Fonts

Two fonts are active in the system:

1\. \*\*Afacad\*\* (`font-afacad`) — Display/Heading font. Aggressive, uppercase, heavy weight. Used for page titles, section headings, nav labels, and all `<h1>` elements.

2\. \*\*Outfit\*\* (`font-outfit`) — UI/Form font. Modern, clean, slightly rounded. Used for form elements, labels, contact details, and body UI copy. \*\*NOT for page headings.\*\*

&#x20;

\### Font Mapping

```

Page title (h1):  font-afacad, text-4xl md:text-5xl, font-black, uppercase, tracking-tight

Section heading:  font-afacad, text-3xl md:text-4xl, font-black, uppercase

Category names:   font-afacad, text-xl md:text-2xl, font-black, uppercase, tracking-\[0.2em]

Form heading:     font-outfit, text-3xl md:text-4xl, font-light, tracking-wide

Form labels:      font-outfit, text-xs, font-semibold, uppercase, tracking-widest, text-gray-400

Contact labels:   font-outfit, text-xs, font-bold, uppercase, tracking-widest, text-gray-400

Contact values:   text-lg, text-white, font-medium

Body text:        text-xl md:text-2xl, text-gray-300, leading-relaxed

```

&#x20;

\### Heading Preferences

\- \*\*Reduce headings aggressively.\*\* The user iteratively reduced heading sizes throughout the project (from `text-5xl` down to roughly `text-xl md:text-2xl` for category lists).

\- Category heading sizes were reduced by 50% from initial implementation.

\- Use `font-black` for all major headings — never `font-bold` or lighter.

\- Always `uppercase` for display headings.

\- Letter spacing: `tracking-tight` on hero, `tracking-\[0.2em]` on category/list items for premium spread.

&#x20;

\---

&#x20;

\## Page Structure Patterns

&#x20;

\### Standard Page Layout

Every page follows this structure:

```

1\. Hero section (py-12 md:py-16, bg-gradient-to-b from-zinc-900 to-black)

&#x20;  - h1 (font-afacad, uppercase)

&#x20;  - Orange underline bar (w-24 h-1 bg-\[#F27722] mx-auto rounded-full mb-4)

&#x20;  - Optional subtitle (text-xl md:text-2xl text-gray-300)

2\. Content section (max-w-4xl or max-w-6xl, standard horizontal padding)

```

&#x20;

\### Orange Underline / Divider

Every hero section has a signature orange divider below the title:

```jsx

<div className="w-24 h-1 bg-\[#F27722] mx-auto rounded-full mb-4" />

```

This is a \*\*non-negotiable\*\* design element — it must appear under every page title.

&#x20;

\### Hover States

All interactive text elements use this pattern:

\- Default: `text-white` or `text-gray-300`

\- Hover: `hover:text-\[#F27722]`

\- Transition: `transition-colors duration-300` or `transition-all duration-300`

&#x20;

For category/list links, there is also an expanding underline:

```jsx

<span className="absolute -bottom-2 left-1/2 w-0 h-1 bg-\[#F27722] group-hover:w-full group-hover:left-0 transition-all duration-500 rounded-full" />

```

&#x20;

\---

&#x20;

\## Component Patterns

&#x20;

\### Navigation (Header)

\- File: `app/components/Layout.tsx`

\- Sticky top, `bg-black/95 backdrop-blur-md border-b border-zinc-800`

\- Height: `h-24 md:h-32`

\- Includes: Logo (left), Nav links (center), Language switcher + Facebook icon (right), Mobile hamburger

\- \*\*Active nav item\*\* is indicated by a signature \*\*orange horizontal "rollout tab"\*\* that animates from left to right. This is the centerpiece of the navigation interaction.

\- A \*\*"Flying Arrow"\*\* (from the logo) animates toward hovered nav items.

\- Language switcher: toggles SV/EN locale, stored in hook

\- Social icons (Facebook): placed next to language switcher, `w-\[30px] h-\[30px]`

&#x20;

\### Footer

\- Three-column grid: Brand info + social links | Contact details | Quick links

\- Facebook icon in brand column: `h-\[36px] w-\[36px]` with `hover:scale-110`

\- Contact details have labeled fields (Adress, E-post, Telefon) — same style as contact page

\- Copyright row at bottom: `border-t border-zinc-900`, centered text, `text-zinc-600`

&#x20;

\### Category / List Pages (Sortiment \& Varumärken)

\*\*Do not use cards.\*\* The preferred pattern is:

```jsx

<div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8">

&#x20; {items.map(item => (

&#x20;   <Link href={...} className="group text-center">

&#x20;     <h2 className="font-afacad text-xl md:text-2xl font-black text-white group-hover:text-\[#F27722] transition-all duration-300 uppercase tracking-\[0.2em] relative inline-block">

&#x20;       {item.name}

&#x20;       <span className="absolute -bottom-2 left-1/2 w-0 h-1 bg-\[#F27722] group-hover:w-full group-hover:left-0 transition-all duration-500 rounded-full" />

&#x20;     </h2>

&#x20;   </Link>

&#x20; ))}

</div>

```

\- \*\*No descriptions or subtitles\*\* next to category names — text only.

\- Sort alphabetically by Swedish locale (`localeCompare('sv')`).

\- Section padding: `pt-0 pb-4 md:pb-8` — content as high as possible.

&#x20;

\### Contact Page Layout

Two columns on desktop (`lg:grid-cols-2 gap-12 lg:gap-24 items-start`):

&#x20;

\*\*Left column:\*\*

1\. Image (at natural aspect ratio — `w-full h-auto block`, never `h-full object-cover`)

2\. Contact details (Address, Email, Phone) stacked vertically below the image

&#x20;

\*\*Right column:\*\*

\- Contact form (extracted to a `'use client'` component: `ContactForm.tsx`)

&#x20;

\*\*Contact detail item pattern:\*\*

```jsx

<div className="flex items-start gap-5 group">

&#x20; <div className="text-\[#F27722] mt-1 shrink-0">

&#x20;   {/\* SVG icon \*/}

&#x20; </div>

&#x20; <div>

&#x20;   <h3 className="font-outfit text-xs font-bold text-gray-400 uppercase tracking-widest mb-1 group-hover:text-white transition-colors">

&#x20;     Adress

&#x20;   </h3>

&#x20;   <p className="text-lg text-white font-medium">{contact.address}</p>

&#x20; </div>

</div>

```

&#x20;

\### Contact Form

File: `app/components/ContactForm.tsx` (must be a `'use client'` component)

&#x20;

\*\*Form input style (sharp underline, no box):\*\*

```jsx

className="w-full bg-transparent border-b border-zinc-800 rounded-none px-0 py-3 text-white placeholder-zinc-700 focus:outline-none focus:border-\[#F27722] transition-colors"

```

&#x20;

\*\*Custom Glass Dropdown (CRITICAL — never use native `<select>`):\*\*

The native browser `<select>` cannot be made truly transparent. Always build a custom dropdown:

\- Trigger: `bg-white/5 backdrop-blur-xl border-none rounded-sm px-4 py-4 focus:outline-none`

\- Menu: `bg-zinc-900/40 backdrop-blur-2xl border border-white/5 rounded-sm shadow-2xl`

\- Options: `hover:bg-\[#F27722] hover:text-black` — orange hover

\- Include `useEffect` to close on click-outside

\- Include `<input type="hidden">` for form submission

\- Animate chevron with `rotate-180` on open

&#x20;

\*\*Submit button:\*\*

```jsx

className="w-full bg-\[#F27722] hover:bg-white text-black font-semibold uppercase tracking-widest py-5 rounded-sm transition-colors duration-300"

```

&#x20;

\*\*Form labels:\*\*

```jsx

className="text-xs font-semibold text-gray-400 uppercase tracking-widest"

```

&#x20;

\---

&#x20;

\## Glassmorphism Rules

&#x20;

When applying glassmorphism effects, use these values:

| Use case              | Background           | Blur                  | Border              |

|-----------------------|----------------------|-----------------------|---------------------|

| Dropdown menu         | `bg-zinc-900/40`     | `backdrop-blur-2xl`   | `border-white/5`    |

| Dropdown trigger      | `bg-white/5`         | `backdrop-blur-xl`    | none                |

| Nav dropdown          | `bg-black/90`        | `backdrop-blur-3xl`   | `border-white/5`    |

| Header background     | `bg-black/95`        | `backdrop-blur-md`    | `border-zinc-800`   |

&#x20;

\*\*Rules:\*\*

1\. Never use `focus:ring-\*` on glass elements — remove all browser focus rings.

2\. Use `bg-zinc-900` for `<option>` elements (native fallback only).

3\. Blur strength should be high (`2xl` or `3xl`) to look premium.

4\. Keep borders faint (`border-white/5` or `border-white/10`).

&#x20;

\---

&#x20;

\## CMS Architecture (Payload CMS)

&#x20;

\### Pattern

\- Use \*\*Globals\*\* for single-instance content (homepage, contact page, site settings, about page).

\- Use \*\*Collections\*\* for repeating content (categories, products).

\- All globals support localization (`sv` / `en`).

\- Always provide \*\*fallback values\*\* in the frontend — never crash if Payload is unavailable.

&#x20;

\### Global Structure

```

homepage          → heroTitle, heroSubtitle, heroImage, carouselTitle, ctaHeading, ctaBody, ctaButtonText

siteSettings      → footerDescription, footerTagline, contact (address, email, phone)

aboutPage         → title, content

contactPage       → title, introText

```

&#x20;

\### Data Fetching Pattern

```typescript

async function getData() {

&#x20; try {

&#x20;   const payload = await getPayload({ config })

&#x20;   const data = await payload.findGlobal({ slug: '...', locale: 'sv' }) as any

&#x20;   return { field: data.field || 'Fallback value' }

&#x20; } catch {

&#x20;   return { field: 'Fallback value' }

&#x20; }

}

```

&#x20;

\### Route Structure

```

app/

├── (frontend)/          ← All public-facing pages

│   ├── page.tsx         ← Home (server component, renders HomeClient)

│   ├── sortiment/       ← Category list + individual category pages

│   ├── varumarken/      ← Brand list page

│   ├── om-oss/          ← About page (empty until CMS content added)

│   └── kontakt/         ← Contact page

├── (payload)/           ← Payload CMS admin

│   └── admin/

└── components/          ← Shared components (Layout.tsx, ContactForm.tsx)

```

&#x20;

\---

&#x20;

\## Localization

&#x20;

\- Two locales: `sv` (Swedish, default) and `en` (English)

\- Toggle via `useLocale` hook — state controlled client-side

\- Language switcher in header uses a flag icon + `SV / EN` toggle

\- All user-facing text should have both SV and EN versions

\- Form labels and headings on the Kontakt page are in Swedish only (B2B Swedish market)

&#x20;

\---

&#x20;

\## Social \& External Links

&#x20;

\- Social icons use \*\*image files from `/public`\*\* (e.g., `/facebook.png`), not icon libraries.

\- Icons are sized at `w-\[30px] h-\[30px]` in header, `h-\[36px] w-\[36px]` in footer.

\- All external links use `target="\_blank" rel="noopener noreferrer"`.

\- Hover: `hover:scale-110 transition-transform duration-300` and `hover:opacity-100`.

\- Social icons appear in TWO places: next to the language switcher in the header, and in the footer brand column.

&#x20;

\---

&#x20;

\## Images

&#x20;

\- Category hero images: `object-cover opacity-60` (user requested 50% lighter than the original opacity-30)

\- Contact image: `w-full h-auto block` — \*\*always maintain natural aspect ratio, never crop with h-full\*\*

\- Logo: served from `/public/logo.png` and `/public/logo\_no\_arrow.png`

\- Arrow element: `/public/arrow.png` — animated with the FlyingArrow component

\- All images are local — no CDN or external image URLs in production

&#x20;

\---

&#x20;

\## UX \& Interaction Principles

&#x20;

1\. \*\*Navigation\*\*: Seamless, animated. The orange rollout tab and flying arrow are core brand interactions.

2\. \*\*Hover states\*\*: All interactive elements have subtle but clear `#F27722` orange feedback.

3\. \*\*No empty state messages in production\*\* — "Innehåll kommer snart" phrasing if needed, but prefer truly empty over placeholder CMS text.

4\. \*\*No admin panel links visible to end users\*\* — all admin references must be removed before deploy.

5\. \*\*Custom components over native browser controls\*\* — the native `<select>` dropdown was replaced with a fully custom implementation to achieve glassmorphism.

6\. \*\*Responsive-first\*\*: Mobile: 1 column. Desktop (`md:` / `lg:`): 2 columns where applicable.

7\. \*\*Focus styling\*\*: Only the orange bottom-border on inputs. No `ring-\*` on any element.

&#x20;

\---

&#x20;

\## Anti-Patterns (Do NOT do these)

&#x20;

| ❌ Anti-pattern                            | ✅ Correct approach                             |

|--------------------------------------------|------------------------------------------------|

| White or light backgrounds                 | Black (`bg-black`) everywhere                  |

| Cards with borders and backgrounds         | Plain text lists with hover underlines         |

| Native `<select>` dropdowns                | Custom `'use client'` glass dropdown component |

| Full border on form inputs                 | Bottom border only (`border-b border-zinc-800`)|

| `focus:ring-\*` on any element              | `focus:outline-none` + colored bottom border   |

| Large paddings/margins pushing content down| Minimal padding — content as high as possible  |

| Descriptions under category names          | Heading text only — remove all subtitles       |

| Admin panel links in public-facing pages   | Empty section or no section                    |

| Generic icon libraries for social icons    | PNG files from `/public`                       |

| `h-full object-cover` on contact images   | `w-full h-auto block` to preserve proportions  |

&#x20;

\---

&#x20;

\## File Checklist for New Page

&#x20;

When creating a new page in this project:

\- \[ ] Place in `app/(frontend)/\[page-name]/page.tsx`

\- \[ ] Make it an `async` server component that fetches from Payload CMS

\- \[ ] Add Payload Global or Collection for any editable content

\- \[ ] Provide fallback values for all CMS fields

\- \[ ] Include Hero section with `h1`, orange divider bar, and optional subtitle

\- \[ ] Use `font-afacad` for all headings

\- \[ ] Use `font-outfit` for form/UI copy

\- \[ ] Keep all colors within the defined palette

\- \[ ] Remove any admin links or CMS placeholder text

\- \[ ] Test that the page returns HTTP 200 via `Invoke-WebRequest`

\- \[ ] Extract any interactive elements to `'use client'` components

\- \[ ] Push to `development` branch, merge to `main` when ready

&#x20;

\---

&#x20;

\## Suggested Additional Skills

&#x20;

The following skills would complement this one and capture other recurring patterns from the project:

&#x20;

1\. \*\*`payload-cms-setup`\*\* — Documents the Payload CMS v3 setup pattern with MongoDB Atlas, Globals, Collections, localization, and seed scripts.

2\. \*\*`nextjs-localization`\*\* — Documents the `useLocale` hook pattern, SV/EN toggle, and how to pass locale to server components.

3\. \*\*`animated-navigation`\*\* — Captures the orange rollout tab nav, FlyingArrow component, and mobile menu patterns for reuse.
