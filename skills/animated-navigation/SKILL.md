---
name: animated-navigation
description: >
  A detailed skill for building the premium animated navigation system from project-a-next.
  Captures the complete interaction model: the orange rollout tab, the FlyingArrow element,
  the expanding underline, the glass dropdown reveal, mobile menu, and all timing values.
  Use this skill any time you want a high-end, distinctively animated navigation header.
---
 
# Animated Navigation Skill
 
## Overview
 
The navigation in project-a-next features two signature animation systems that work together:
 
1. **The Rollout Tab** — A filled, pill-and-taper accent-colored shape that "rolls out" from the left when hovering a nav item that has a dropdown. The shape starts from behind the text and slides right as a horizontal reveal.
2. **The Flying Arrow** — A decorative arrow element physically flies from the logo to the currently hovered nav link, drawing an expanding underline as it moves. On mouse-leave, it returns home.
 
These are not subtle — they are the central identity moment of the navigation. Done right, they feel **alive and premium**. Done wrong, they feel janky. Every timing and easing value matters.
 
---
 
## Header Shell
 
```jsx
<header className="sticky top-0 z-50 w-full bg-black/95 backdrop-blur-md border-b border-zinc-800 shadow-xl">
  <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
    <div className="flex justify-between items-center h-24 md:h-32 relative">
      {/* Logo (left) */}
      {/* Navigation (center, absolute) */}
      {/* FlyingArrow (fixed, overlays everything) */}
      {/* Language, Social, Mobile hamburger (right) */}
    </div>
  </div>
  {/* Mobile menu (absolute, full width) */}
</header>
```
 
Key values:
- Height: `h-24 md:h-32`
- Background: `bg-black/95 backdrop-blur-md`
- Border: `border-b border-zinc-800`
- `sticky top-0 z-50`
 
---
 
## The Rollout Tab (Dropdown Trigger Indicators)
 
### What it looks like
A solid accent-colored pill shape that slides from left to right across the nav link text when hovered.
The RIGHT edge deliberately tapers to a custom S-curve polygon — like a liquid droplet or flame shape.
The left edge is a rounded half-circle (pill end).
 
### Shape Breakdown
The shape is TWO overlapping `div` elements inside a clipping container:
 
**1. Left segment (pill end + body):**
```jsx
<div className="absolute inset-y-0 left-0 right-[60px] bg-[accent] rounded-l-full" />
```
 
**2. Right segment (S-curve taper):**
```jsx
<div
  className="absolute inset-y-0 right-0 w-[62px] bg-[accent]"
  style={{
    clipPath: 'polygon(0% 0%, 20% 0%, 35% 1%, 48% 3%, 58% 6%, 66% 12%, 73% 20%, 79% 32%, 84% 48%, 89% 65%, 93% 82%, 96% 91%, 98% 97%, 100% 100%, 0% 100%)',
  }}
/>
```
This polygon precisely defines the S-curve taper. Do not simplify — the smoothness requires many polygon points.
 
### Rollout Animation (Horizontal Clip)
The entire container clips horizontally using `clipPath: inset(...)`:
 
```jsx
<div
  className="absolute top-1/2 -translate-y-1/2 h-[44px] z-20 pointer-events-none transition-all duration-[900ms] ease-[cubic-bezier(0.25,1,0.5,1)]"
  style={{
    left: '12px',
    right: '-16px',  // Taper extends slightly past the text
    clipPath: isOpen
      ? 'inset(-10% -20% -10% 0%)'   // Fully revealed
      : 'inset(-10% 100% -10% 0%)',  // Fully hidden (clipped from right)
  }}
>
```
 
- `inset(-10% -20% -10% 0%)` — negative values overflow the clip box (no clipping)
- `inset(-10% 100% -10% 0%)` — right clip = 100%, hiding everything
- The rollout is left-to-right: the right clip shrinks from 100% to a negative overflow
- `duration-[900ms]` — slow and deliberate
- Easing: `cubic-bezier(0.25,1,0.5,1)` — fast start, smooth brake
 
### Alignment within NavItem
The tab is inside the `<Link>` element, sitting `absolute` relative to the link's bounding box.
Text has `drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]` to stay visible on top of the colored tab.
 
---
 
## The Standard Underline (Non-Dropdown Links)
 
For links without dropdowns (Home, Om Oss, Kontakt), an expanding underline animates from left to right:
 
```jsx
<span className={clsx(
  "absolute bottom-[calc(50%-18px)] left-6 right-6 h-[2px] bg-[accent] origin-left ease-[cubic-bezier(0.25,1,0.5,1)]",
  isActive
    ? "scale-x-100 transition-none"
    : "scale-x-0 group-hover/link:scale-x-100 transition-transform duration-500 group-hover/link:delay-300"
)} />
```
 
Key details:
- `bottom-[calc(50%-18px)]` — vertically positioned in the lower half of the link area (matches underline Y from FlyingArrow)
- `left-6 right-6` — inset from link edges (matching FlyingArrow's target coordinates)  
- `origin-left` — scales from left to right
- `delay-300` — delayed to start **after** the FlyingArrow arrives (sync is critical)
- Active state: `scale-x-100 transition-none` — always visible, no animation needed
 
---
 
## The FlyingArrow
 
### What it is
An image (`/arrow.png`) that is `position: fixed` at the top-left of the viewport and
**translated** to any position using CSS transforms. It physically moves via `transform: translate(X, Y)`.
 
The arrow is always rendered — it simply lives at the logo position when no item is hovered.
 
### Idle Position (at the logo)
The arrow sits inside the logo image at specific relative coordinates:
```
X: logoLeft + logoWidth × 0.775  (77.5% across the logo)
Y: logoTop  + logoHeight × 0.48  (48% down the logo)
```
These were tuned against the specific logo artwork where the decorative arrow element sits.
 
### Arrow Size (Proportional to Logo)
The arrow image (`/arrow.png`) is a cropped 158×157px element from the 1264×832 logo:
```typescript
const arrowW = logoW * (158 / 1264);
const arrowH = logoH * (157 / 832);
```
This keeps the arrow exactly proportional to the rendered logo size.
 
### Flight Animation (Phase 1: Fly to start of underline)
When hovering a nav item, the arrow first jumps to the left edge of the underline:
```typescript
const underlineStartLeft = targetRect.left + 24;  // left-6 inset
const underlineY = targetRect.top + (targetRect.height / 2) + 16;
 
setStyle({
  transform: `translate(${underlineStartLeft - 3}px, ${underlineY - arrowH / 2 - 3}px)`,
  width: `${arrowW}px`,
  height: `${arrowH}px`,
  transition: 'transform 0.3s cubic-bezier(0.25, 1, 0.5, 1)',
  opacity: 1
});
```
The `-3px` offsets were tuned by eye to align perfectly with the underline start.
 
### Flight Animation (Phase 2: Glide to end, drawing the underline)
After 300ms (when Phase 1 completes), the arrow glides right to the end:
```typescript
const timer = setTimeout(() => {
  setStyle({
    transform: `translate(${underlineEndRight - 3}px, ${underlineY - arrowH / 2 - 3}px)`,
    width: `${arrowW}px`,
    height: `${arrowH}px`,
    transition: 'transform 0.5s cubic-bezier(0.25, 1, 0.5, 1)',
    opacity: 1
  });
}, 300);
```
As the arrow glides right, the CSS underline expands left-to-right (with `delay-300` on the underline).
The visual result: the arrow "drags" the line out of the link.
 
### Return Home
On mouse leave, call `setTargetRect(null)` — this resets the arrow to the logo position with: 
```typescript
transition: 'transform 0.4s ease-out'
```
 
On route change: always reset `targetRect` to null in a `useEffect` watching `pathname`:
```typescript
useEffect(() => { setTargetRect(null); }, [pathname]);
```
 
### FlyingArrow Component Signature
```typescript
function FlyingArrow({
  targetRect,     // DOMRect | null — the hovered NavItem's bounding rect
  originRef,      // React.RefObject<HTMLImageElement> — the logo img ref
}: {...}) {
  // ...
  return (
    <div style={style} className="fixed top-0 left-0 z-[100] pointer-events-none drop-shadow-lg">
      <img src="/arrow.png" alt="Flying Arrow" className="w-full h-full object-contain" />
    </div>
  );
}
```
 
---
 
## The Glass Dropdown (Below Rollout Tab)
 
When a dropdown is open, a menu panel appears **directly below the tab**, flush with the tab's bottom edge.
 
### Reveal Animation
Uses `clipPath` for a vertical wipe-in (top-down reveal):
```jsx
style={{
  left: '34px',       // Aligned to start of tab's straight bottom
  right: '-16px',     // Aligned to tab's elongated right tip
  top: 'calc(50% + 22px)', // Flush under the tab's flat bottom edge
  clipPath: isOpen ? 'inset(0% -50% -50% -50%)' : 'inset(0% -50% 100% -50%)',
  transitionDelay: isOpen ? '300ms' : '0ms',
}}
```
 
- Open: clip reveals from top to bottom (bottom clip goes from 100% to -50%)
- `300ms` delay — waits for the rollout tab to partially extend before the menu appears
- Duration: `1000ms` — slow, deliberate reveal
- Easing: `cubic-bezier(0.25,1,0.5,1)`
 
### Dropdown Container Style
```jsx
className="rounded-b-2xl overflow-hidden flex flex-col relative bg-black/90 backdrop-blur-3xl shadow-[0_40px_80px_-15px_rgba(0,0,0,0.95)] border border-white/5"
```
 
### Dropdown Items (Staggered Entrance)
Each item fades in individually with a staggered delay:
```jsx
className="transition-all duration-[600ms] ease-[cubic-bezier(0.25,1,0.5,1)]"
style={{ transitionDelay: isOpen ? `${400 + idx * 40}ms` : '0ms' }}
```
Items start after 400ms (tab + menu are already animating) with 40ms per item.
 
Item hover: text nudges right + scales slightly:
```jsx
className="group-hover/item:translate-x-2 group-hover/item:scale-105 transition-all duration-300 ease-[cubic-bezier(0.25,1,0.5,1)]"
```
 
---
 
## Mobile Menu
 
- Full-width overlay, `absolute top-full left-0` — slides down below header
- Background: `bg-black/95 backdrop-blur-xl border-b border-zinc-800`
- Hamburger / X toggle: Lucide icons `<Menu>` / `<X>`
- Items are stacked vertically with `border-b border-zinc-800/50`
- Closes on: item click, locale change, resize to desktop viewport (`window.innerWidth >= 1024`)
 
---
 
## Easing Reference
 
The **signature easing** for all animations in this navigation:
```
cubic-bezier(0.25, 1, 0.5, 1)
```
Apply this to every animated element. It has a fast start (quick response to hover) with a
smooth, natural deceleration. It should never feel linear, bouncy, or mechanical.
 
| Animation          | Duration   | Easing                          | Notes                          |
|---------------------|------------|---------------------------------|--------------------------------|
| Rollout tab reveal  | `900ms`    | `cubic-bezier(0.25,1,0.5,1)`   | `clipPath` horizontal wipe     |
| Dropdown reveal     | `1000ms`   | `cubic-bezier(0.25,1,0.5,1)`   | `300ms` delay after tab        |
| Item stagger        | `600ms`    | `cubic-bezier(0.25,1,0.5,1)`   | `400ms + idx*40ms` delay       |
| Arrow Phase 1 fly   | `300ms`    | `cubic-bezier(0.25, 1, 0.5, 1)`| Jump to underline start        |
| Arrow Phase 2 glide | `500ms`    | `cubic-bezier(0.25, 1, 0.5, 1)`| Draw the underline             |
| Arrow return home   | `400ms`    | `ease-out`                      | Smooth return                  |
| Underline expand    | `500ms`    | `cubic-bezier(0.25,1,0.5,1)`   | `300ms` delay to sync arrow    |
 
---
 
## Implementation Checklist
 
- [ ] Logo image has a `ref` — required for FlyingArrow origin measurement
- [ ] `FlyingArrow` is `position: fixed top-0 left-0 z-[100]` — overlays everything
- [ ] `pointer-events-none` on FlyingArrow and rollout tab — never intercepts clicks
- [ ] `onHoverStart` passes `DOMRect` from `getBoundingClientRect()` in `requestAnimationFrame`
- [ ] `onHoverEnd` resets `targetRect` to `null`
- [ ] Route changes reset `targetRect` via `useEffect` on `pathname`
- [ ] Underline `delay-300` only applies when NOT active (active = always visible, no delay)
- [ ] Dropdown container has `transitionDelay: '0ms'` on close (instant hide)
- [ ] Rollout tab `left: 12px, right: -16px` aligned with start of text + taper overshoot
- [ ] Dropdown panel `left: 34px, right: -16px` aligned with tab bottom-straight edge and tip
 