---

name: payload-cms-setup

description: Use when setting up Payload CMS v3 in a Next.js App Router project with MongoDB Atlas, globals, collections, localization, access control, seeding, and server-component data fetching patterns.

---

&#x20;

\# Payload CMS Setup Skill

&#x20;

\## Overview

&#x20;

Payload CMS v3 lives \*\*inside\*\* the same Next.js App Router project as the frontend. It handles

content management via Globals (single-instance content) and Collections (repeating content).

The admin panel runs at `/admin` while the public frontend runs at `/`.

&#x20;

\---

&#x20;

\## Router Group Structure

&#x20;

Next.js route groups prevent Payload middleware from running on frontend routes:

&#x20;

```

app/

├── (frontend)/        ← All public pages — no Payload middleware

│   ├── layout.tsx     ← Fetches from Payload, passes as props

│   ├── page.tsx

│   └── ...

├── (payload)/         ← Payload admin — isolated from frontend

│   └── admin/

│       └── \[\[...segments]]/

│           └── page.tsx

└── api/

&#x20;   └── \[...slug]/

&#x20;       └── route.ts   ← Payload REST/GraphQL API

```

&#x20;

This is critical. Without the route group separation, Payload's Next.js plugin middleware fires

on every page load, adding significant overhead.

&#x20;

\---

&#x20;

\## payload.config.ts

&#x20;

```typescript

import { buildConfig } from 'payload'

import { mongooseAdapter } from '@payloadcms/db-mongodb'

import { lexicalEditor } from '@payloadcms/richtext-lexical'

import { nextJsPlugin } from '@payloadcms/next'

&#x20;

export default buildConfig({

&#x20; admin: {

&#x20;   user: Users.slug,

&#x20; },

&#x20; collections: \[Users, Categories],

&#x20; globals: \[Homepage, SiteSettings, AboutPage, ContactPage],

&#x20; db: mongooseAdapter({

&#x20;   url: process.env.MONGODB\_URI || '',

&#x20; }),

&#x20; editor: lexicalEditor({}),

&#x20; localization: {

&#x20;   locales: \['sv', 'en'],

&#x20;   defaultLocale: 'sv',

&#x20;   fallback: true, // SV content falls back to EN if missing

&#x20; },

&#x20; secret: process.env.PAYLOAD\_SECRET || '',

&#x20; typescript: {

&#x20;   outputFile: 'payload-types.ts',

&#x20; },

&#x20; plugins: \[nextJsPlugin({ configPath: './payload.config.ts' })],

})

```

&#x20;

\---

&#x20;

\## Globals (Single-Instance Content)

&#x20;

Create one file per Global in `globals/`:

&#x20;

\### Homepage.ts

```typescript

import { GlobalConfig } from 'payload'

&#x20;

export const Homepage: GlobalConfig = {

&#x20; slug: 'homepage',

&#x20; label: 'Startsida',

&#x20; fields: \[

&#x20;   { name: 'heroTitle',      type: 'text',     localized: true },

&#x20;   { name: 'heroSubtitle',   type: 'textarea', localized: true },

&#x20;   { name: 'heroImage',      type: 'upload',   relationTo: 'media' },

&#x20;   { name: 'carouselTitle',  type: 'text',     localized: true },

&#x20;   { name: 'ctaHeading',     type: 'text',     localized: true },

&#x20;   { name: 'ctaBody',        type: 'textarea', localized: true },

&#x20;   { name: 'ctaButtonText',  type: 'text',     localized: true },

&#x20; ],

}

```

&#x20;

\### SiteSettings.ts

```typescript

export const SiteSettings: GlobalConfig = {

&#x20; slug: 'site-settings',

&#x20; label: 'Webbplatsinställningar',

&#x20; fields: \[

&#x20;   { name: 'footerDescription', type: 'textarea', localized: true },

&#x20;   { name: 'footerTagline',     type: 'text',     localized: true },

&#x20;   {

&#x20;     name: 'contact',

&#x20;     type: 'group',

&#x20;     fields: \[

&#x20;       { name: 'address', type: 'text' },

&#x20;       { name: 'email',   type: 'email' },

&#x20;       { name: 'phone',   type: 'text' },

&#x20;     ],

&#x20;   },

&#x20; ],

}

```

&#x20;

\### ContactPage.ts / AboutPage.ts

Follow the same pattern — fields for `title` (localized) and body content.

&#x20;

\---

&#x20;

\## Collections

&#x20;

\### Categories Collection (with Carousel Support)

```typescript

export const Categories: CollectionConfig = {

&#x20; slug: 'categories',

&#x20; labels: { singular: 'Kategori', plural: 'Kategorier' },

&#x20; access: { read: () => true },  // Public read access

&#x20; fields: \[

&#x20;   { name: 'name',          type: 'text',     required: true, localized: true },

&#x20;   { name: 'slug',          type: 'text',     required: true },

&#x20;   { name: 'description',   type: 'textarea', localized: true },

&#x20;   { name: 'image',         type: 'upload',   relationTo: 'media' },

&#x20;   { name: 'showInCarousel',type: 'checkbox', defaultValue: false },

&#x20;   { name: 'sortOrder',     type: 'number',   defaultValue: 0 },

&#x20; ],

}

```

&#x20;

\### Users Collection (Invite-Only Auth)

```typescript

export const Users: CollectionConfig = {

&#x20; slug: 'users',

&#x20; auth: true,

&#x20; admin: { useAsTitle: 'email' },

&#x20; access: {

&#x20;   create: () => false,  // No self-registration

&#x20;   read:   () => true,

&#x20;   update: ({ req }) => req.user?.role === 'admin',

&#x20;   delete: ({ req }) => req.user?.role === 'admin',

&#x20; },

&#x20; fields: \[

&#x20;   { name: 'role', type: 'select', options: \['admin', 'editor'], defaultValue: 'editor' },

&#x20; ],

}

```

&#x20;

\---

&#x20;

\## Data Fetching Pattern (Server Components)

&#x20;

Always use this pattern — it provides Payload data with a graceful fallback:

&#x20;

```typescript

async function getData() {

&#x20; try {

&#x20;   const payload = await getPayload({ config })

&#x20;   const data = await payload.findGlobal({

&#x20;     slug: 'homepage',

&#x20;     locale: 'sv',

&#x20;   }) as any

&#x20;   return {

&#x20;     heroTitle: data.heroTitle || 'Fallback Title',

&#x20;     // ... map all fields with fallbacks

&#x20;   }

&#x20; } catch {

&#x20;   // Payload unavailable (build time, cold start, etc.)

&#x20;   return {

&#x20;     heroTitle: 'Fallback Title',

&#x20;     // ... return identical shape with hardcoded fallbacks

&#x20;   }

&#x20; }

}

```

&#x20;

\*\*Key rules:\*\*

1\. Import `getPayload` from `'payload'` and `config` from `'@payload-config'`

2\. Always `as any` — avoid fighting auto-generated types for globals

3\. Always provide fallback values — the site must work even if MongoDB is unreachable

4\. Only call from `async` server components — never from client components

&#x20;

\### Fetching Collections

```typescript

const result = await payload.find({

&#x20; collection: 'categories',

&#x20; where: { showInCarousel: { equals: true } },

&#x20; sort: 'sortOrder',

&#x20; limit: 20,

&#x20; locale: 'sv',

})

const docs = result.docs

```

&#x20;

\---

&#x20;

\## Localization

&#x20;

Localized fields automatically return content for the requested `locale`.

Fetch SV and EN separately when you need both:

&#x20;

```typescript

const sv = await payload.findGlobal({ slug: 'homepage', locale: 'sv' }) as any

const en = await payload.findGlobal({ slug: 'homepage', locale: 'en' }) as any

```

&#x20;

With `fallback: true` in config, EN content falls back to SV if EN is not filled in.

&#x20;

\---

&#x20;

\## Environment Variables

&#x20;

```env

MONGODB\_URI=mongodb+srv://user:password@cluster.mongodb.net/dbname

PAYLOAD\_SECRET=your-long-random-secret-string

NEXT\_PUBLIC\_SERVER\_URL=http://localhost:3000

```

&#x20;

\---

&#x20;

\## Seeding

&#x20;

Create one-off seed scripts (`seed.ts`) to populate Globals with initial content:

&#x20;

```typescript

import { getPayload } from 'payload'

import config from './payload.config'

&#x20;

async function seed() {

&#x20; const payload = await getPayload({ config })

&#x20; 

&#x20; await payload.updateGlobal({

&#x20;   slug: 'homepage',

&#x20;   locale: 'sv',

&#x20;   data: {

&#x20;     heroTitle: 'Vi bygger dina varumärken.',

&#x20;     // ...

&#x20;   },

&#x20; })

&#x20; 

&#x20; process.exit(0)

}

&#x20;

seed()

```

&#x20;

Run with `npx ts-node --esm seed.ts` or `tsx seed.ts`.

&#x20;

\---

&#x20;

\## Access Control

&#x20;

\- Public routes: set `access: { read: () => true }` on collections

\- Admin panel: protected by Users auth

\- Never expose admin links on public-facing pages — remove all `/admin` hrefs before launch

&#x20;

