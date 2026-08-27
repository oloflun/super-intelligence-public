---
name: nextjs-localization
description: >
  A skill for implementing bilingual (SV/EN) localization in a Next.js App Router project
  using a custom useLocale hook with client-side state. Covers the hook implementation,
  translation key patterns, Payload CMS locale handling, and the language toggle UI.
  Derived from the project-a-next project.
---
 
# Next.js Localization Skill
 
## Overview
 
Localization in project-a-next uses a **lightweight client-side approach**: a `useLocale` hook
stores the current locale (`'sv'` | `'en'`) in React state, and a translation function `t(key)`
returns the correct string. No i18n library required. Payload CMS handles localized content
separately via the `locale` parameter in data fetching.
 
---
 
## The `useLocale` Hook
 
```typescript
// app/hooks/useLocale.ts
'use client'
 
import { useState, useCallback } from 'react'
 
const translations: Record<string, { sv: string; en: string }> = {
  'nav.home':        { sv: 'Hem',         en: 'Home' },
  'nav.assortment':  { sv: 'Sortiment',   en: 'Assortment' },
  'nav.brands':      { sv: 'Varumärken',  en: 'Brands' },
  'nav.about':       { sv: 'Om Oss',      en: 'About Us' },
  'nav.contact':     { sv: 'Kontakt',     en: 'Contact' },
  'nav.partners':    { sv: 'Partners',    en: 'Partners' },
  'footer.address':  { sv: 'Adress',      en: 'Address' },
  'footer.email':    { sv: 'E-post',      en: 'Email' },
  'footer.phone':    { sv: 'Telefon',     en: 'Phone' },
  'category.tools':  { sv: 'Verktyg & Maskiner', en: 'Tools & Machinery' },
  'category.power':  { sv: 'Batterier & Ström',  en: 'Batteries & Power' },
  // ... add all keys
}
 
export function useLocale() {
  const [locale, setLocale] = useState<'sv' | 'en'>('sv')
 
  const t = useCallback((key: string) => {
    return translations[key]?.[locale] ?? key
  }, [locale])
 
  const toggleLocale = useCallback(() => {
    setLocale(prev => prev === 'sv' ? 'en' : 'sv')
  }, [])
 
  return { locale, t, toggleLocale }
}
```
 
---
 
## How to Use
 
### In Client Components
```tsx
'use client'
import { useLocale } from '../hooks/useLocale'
 
export function MyComponent() {
  const { t, locale, toggleLocale } = useLocale()
  
  return (
    <div>
      <h1>{t('nav.home')}</h1>
      <p>{locale === 'sv' ? 'Swedish text' : 'English text'}</p>
    </div>
  )
}
```
 
### The Language Toggle Button
```tsx
<button
  onClick={toggleLocale}
  className="flex items-center gap-2 px-3 py-2 text-gray-300 hover:text-[accent] transition-colors rounded hover:bg-white/5"
  aria-label="Toggle Language"
>
  <Flag className="w-5 h-5" />
  <span className="text-sm font-bold uppercase tracking-wider">
    {locale === 'sv' ? 'EN' : 'SV'}
  </span>
</button>
```
Shows the **opposite** locale (what you'll switch TO, not current locale).
 
---
 
## Server Component Localization (Payload CMS)
 
Server components cannot use the hook because they don't have client state.
For server-rendered CMS content, fetch both locales and return both:
 
```typescript
// In server component
const sv = await payload.findGlobal({ slug: 'homepage', locale: 'sv' }) as any
const en = await payload.findGlobal({ slug: 'homepage', locale: 'en' }) as any
 
return <HomeClient homepage={{ titleSv: sv.title, titleEn: en.title }} />
```
 
Then in the client component, use `locale` to select:
```tsx
<h1>{locale === 'sv' ? homepage.titleSv : homepage.titleEn}</h1>
```
 
---
 
## Localized Content in Components
 
For short inline strings, use ternary directly:
```tsx
{locale === 'sv' ? 'Utforska' : 'Explore'}
```
 
For longer blocks, store both in the same data object:
```typescript
type HomepageData = {
  heroTitle: string
  heroTitleEn: string
  heroSubtitle: string
  heroSubtitleEn: string
  // ...
}
```
 
---
 
## Rules
 
1. **Default locale is Swedish (`'sv'`)** — the site is primarily Swedish-language
2. **Never use Next.js i18n routing** (`/en/...`) — locale is client-side state only
3. **Hook state is not persisted** — resets to `'sv'` on page refresh (intentional simplicity)
4. **Payload `fallback: true`** — if EN content is missing in CMS, it falls back to SV automatically
5. **Add keys to `translations`** as needed — keep the object as the single source of truth for UI strings
6. **Server components get data in both languages** from Payload — pass both to client and let client select
