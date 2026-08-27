---
name: slideshow
description: >
  A detailed skill for building the signature 3D perspective carousel/slideshow used in project-a-next.
  Covers the full interaction model, card positioning math, blur/scale/opacity depth effect,
  auto-play, pause-on-hover, navigation, animated content area, and CMS integration.
  Use this skill any time you need to create a premium, depth-based content slideshow.
---
 
# Slideshow Skill: 3D Perspective Carousel
 
## Overview
 
This carousel is NOT a standard left/right slide. It creates the illusion of a **3D stack** by
arranging all cards simultaneously in a fanned-out perspective, using scale, opacity, and blur
to simulate depth in 2D space. The active card is front-and-center; adjacent cards recede on
both sides with exponentially increasing depth. Cards are clickable to jump directly to any item.
 
---
 
## Visual Design
 
### Card Stack Appearance
- **Center card (active)**: Full size, full opacity, sharp, no blur — `scale-100 opacity-100 blur-none`
- **Side cards (±1)**: 75% size, 70% opacity, slight blur — `scale-75 opacity-70 blur-[2px]`
- **Far cards (±2)**: 60% size, 40% opacity, more blur — `scale-[0.6] opacity-40 blur-[4px]`
- **Hidden cards**: Zero opacity, scale-50 — `scale-50 opacity-0 blur-[6px]`
 
This graduated falloff makes the carousel feel three-dimensional without any actual 3D CSS transforms.
 
### Card Dimensions
```
Mobile:  240px × 240px (square)
Desktop: 360px × 360px (square)  ← md: breakpoint
```
Square cards work best for this layout — equal width and height.
 
### Card Positioning (Horizontal Offset)
```
Position +1 (right side):  translate-x-[40%] md:translate-x-[45%]
Position +2 (far right):   translate-x-[70%] md:translate-x-[85%]
Position -1 (left side):  -translate-x-[40%] md:-translate-x-[45%]
Position -2 (far left):   -translate-x-[70%] md:-translate-x-[85%]
```
All cards are `absolute` positioned within a `relative` container — they overlap each other.
 
### Card Visual Style
- `rounded-2xl overflow-hidden` — rounded corners, no content bleeding
- `bg-black` — dark background fill in case image doesn't load
- Image inside: `w-full h-full object-cover` — fills the card
- Image hover: `hover:scale-110 transition-transform duration-700` — subtle zoom on the inner image
- Thin dark overlay on image: `bg-black/10` — prevents images from being overly bright
 
---
 
## Position Math
 
The position calculation maps each card to a relative slot based on `activeIndex`:
 
```typescript
const getCardStyle = (index: number) => {
  const total = categories.length;
  const pos = (index - activeIndex + total) % total;
 
  if (pos === 0)          return "z-30 scale-100 opacity-100 translate-x-0 blur-none";
  else if (pos === 1)     return "z-20 scale-75 opacity-70 translate-x-[40%] md:translate-x-[45%] blur-[2px]";
  else if (pos === 2)     return "z-10 scale-[0.6] opacity-40 translate-x-[70%] md:translate-x-[85%] blur-[4px]";
  else if (pos === total - 1) return "z-20 scale-75 opacity-70 -translate-x-[40%] md:-translate-x-[45%] blur-[2px]";
  else if (pos === total - 2) return "z-10 scale-[0.6] opacity-40 -translate-x-[70%] md:-translate-x-[85%] blur-[4px]";
  else                    return "z-0 scale-50 opacity-0 translate-x-0 blur-[6px]";
};
```
 
All cards render in the DOM simultaneously — only CSS classes switch to rearrange them.
 
---
 
## Animation
 
### Card Transition
```
transition-all duration-700 ease-[cubic-bezier(0.25,1,0.5,1)]
```
 
The cubic-bezier `(0.25,1,0.5,1)` is the **signature easing** used throughout this project for any
animated motion. It creates a fast start that brakes smoothly — never linear, never bounce.
Duration: `700ms`. This makes the card transitions feel buttery, not mechanical.
 
### Content Area below Cards
The text (name, description, CTA button) fades in with a bottom-up slide using Tailwind's `animate-in`:
```jsx
<div key={activeIndex} className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-forwards">
```
The `key={activeIndex}` is critical — it forces React to re-mount the element on every slide change,
re-triggering the animation. Without this, the animation only plays once.
 
---
 
## Container Structure
 
```jsx
<section className="w-full max-w-7xl mx-auto py-12 md:py-16 px-4 sm:px-6 lg:px-8 overflow-hidden">
  
  {/* Section Title */}
  <div className="text-center mb-8 md:mb-12">
    <h2 className="font-afacad text-4xl md:text-5xl font-black uppercase tracking-widest text-[accent]">
      {title}
    </h2>
    <div className="w-24 h-1 bg-[accent] mx-auto mt-6 rounded-full" />
  </div>
 
  {/* Card Stage */}
  <div
    className="relative w-full max-w-4xl mx-auto h-[300px] md:h-[400px] flex items-center justify-center mb-6 md:mb-8"
    onMouseEnter={() => setIsPaused(true)}
    onMouseLeave={() => setIsPaused(false)}
  >
    {/* Prev Arrow */}
    <button onClick={handlePrev} className="absolute left-0 z-30 p-2 text-[accent] hover:text-white transition-colors duration-300">
      <ChevronLeft className="w-10 h-10 md:w-14 md:h-14" />
    </button>
 
    {/* Cards */}
    <div className="relative w-full h-full flex justify-center items-center">
      {cards.map((card, i) => (
        <div
          key={card.id}
          className={`absolute w-[240px] h-[240px] md:w-[360px] md:h-[360px] transition-all duration-700 ease-[cubic-bezier(0.25,1,0.5,1)] rounded-2xl overflow-hidden bg-black ${getCardStyle(i)} cursor-pointer`}
          onClick={() => setActiveIndex(i)}
        >
          <img src={card.image} alt={card.name} className="w-full h-full object-cover transition-transform duration-700 hover:scale-110" />
          <div className="absolute inset-0 bg-black/10" />
        </div>
      ))}
    </div>
 
    {/* Next Arrow */}
    <button onClick={handleNext} className="absolute right-0 z-30 p-2 text-[accent] hover:text-white transition-colors duration-300">
      <ChevronRight className="w-10 h-10 md:w-14 md:h-14" />
    </button>
  </div>
 
  {/* Content Area */}
  <div className="relative w-full max-w-2xl mx-auto min-h-[160px] text-center flex flex-col items-center">
    <div key={activeIndex} className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-forwards flex flex-col items-center">
      <h3 className="text-xl md:text-2xl font-bold uppercase text-white mb-4 tracking-wide">
        {activeCard.name}
      </h3>
      <p className="text-lg md:text-xl text-gray-300 mb-6 max-w-xl font-medium leading-relaxed">
        {activeCard.description}
      </p>
      <Link
        href={`/sortiment/${activeCard.slug}`}
        className="inline-flex items-center bg-[accent] text-black px-8 py-3 rounded-full font-bold uppercase tracking-wider hover:bg-white transition-all duration-300 shadow-[0_0_20px_rgba(accent,0.3)] hover:shadow-[0_0_30px_rgba(accent,0.5)] transform hover:scale-105 active:scale-95 group"
      >
        Utforska
        <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
      </Link>
    </div>
  </div>
 
</section>
```
 
---
 
## Auto-Play & Pause
 
```typescript
const [isPaused, setIsPaused] = useState(false);
 
useEffect(() => {
  if (isPaused || cards.length === 0) return;
  const interval = setInterval(() => {
    setActiveIndex((prev) => (prev - 1 + cards.length) % cards.length);
  }, 3500); // Advance every 3.5 seconds
  return () => clearInterval(interval);
}, [isPaused, cards.length]);
```
 
- Pauses on `mouseEnter` of the card stage (not the whole section).
- Resumes on `mouseLeave`.
- Auto-advances **backwards** (decrements index) so `handleNext` and auto-play go the same direction.
- Direction: `handleNext` decrements, `handlePrev` increments (counter-intuitive naming — "next" in the visual flow moves the card stack left).
 
---
 
## Navigation Buttons
 
```typescript
const handleNext = () => setActiveIndex((prev) => (prev - 1 + cards.length) % cards.length);
const handlePrev = () => setActiveIndex((prev) => (prev + 1) % cards.length);
```
 
Arrow sizing:
```
Mobile:  w-10 h-10 (40px)
Desktop: w-14 h-14 (56px)  ← md: breakpoint
```
 
---
 
## CTA Button Style (Inside Carousel)
 
The CTA button within the content area is in **pill (rounded-full) shape** — unlike most other buttons which use `rounded-sm`. This is intentional contrast.
 
```jsx
className="inline-flex items-center bg-[accent] text-black px-8 py-3 rounded-full font-bold uppercase tracking-wider hover:bg-white transition-all duration-300 shadow-[0_0_20px_rgba(242,119,34,0.3)] hover:shadow-[0_0_30px_rgba(242,119,34,0.5)] transform hover:scale-105 active:scale-95 group"
```
 
Key effects:
- Glow shadow using accent RGBA: `shadow-[0_0_20px_rgba(R,G,B,0.3)]`
- Glow intensifies on hover: `hover:shadow-[0_0_30px_rgba(R,G,B,0.5)]`
- Scales up on hover, slightly shrinks on click (press feel)
- `ArrowRight` icon with `group-hover:translate-x-1` — nudges right on hover
 
---
 
## CMS Integration
 
Cards are populated from Payload CMS `categories` collection with `showInCarousel: true`:
```typescript
const result = await payload.find({
  collection: 'categories',
  where: { showInCarousel: { equals: true } },
  sort: 'sortOrder',   // Maintain manual order set in admin
  limit: 20,
  locale: 'sv',
})
```
 
Provide fallback data (hardcoded array) for when Payload is unreachable. Never crash without cards.
 
---
 
## Component Architecture
 
- **`CarouselSection`** — self-contained component within `HomeClient.tsx`
- Must be `'use client'` because it uses `useState` and `useEffect`
- Receives: `categories`, `locale`, `carouselTitle`
- Parent (`Home`) is a server component that fetches data and passes it down
- Carousel title text comes from the `homepage` global (CMS-editable)
 
---
 
## Key Rules
 
1. **All cards render simultaneously** — visibility is controlled by CSS classes only, not conditional rendering.
2. **`key={activeIndex}` on the content area** — required to re-trigger animations on slide change.
3. **`overflow-hidden` on the section** — prevents off-screen cards from causing horizontal scroll.
4. **Never use CSS 3D transforms** (`rotateY`, `perspective`) — the depth effect is achieved through scale + blur + opacity alone.
5. **Minimum 5 cards recommended** — fewer than 5 may leave empty slots in the visual stack.
6. **Square cards only** — the overlap math assumes equal width and height.
