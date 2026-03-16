# Feature Landscape

**Domain:** Interactive geospatial data visualization / neighbourhood analytics (NLP-powered)
**Researched:** 2026-03-16

## Table Stakes

Features users expect from an interactive map visualization. Missing any of these and the app feels broken or amateur.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Choropleth neighbourhood fills** | Core visual output -- coloured polygons on a map is what users come to see | Medium | GeoJSON polygons with fill colours driven by vibe scores; semi-transparent fills over dark basemap per PROJECT.md spec |
| **Hover tooltip / maptip** | Users expect immediate feedback on hover -- "what neighbourhood is this? what's the score?" | Low | Show neighbourhood name + dominant vibe + summary score on pointer hover; disappear on mouse-out; no click required |
| **Click-to-detail sidebar** | Clicking a neighbourhood must reveal deeper information; tooltip alone is insufficient for 6 vibe dimensions + topics | Medium | Slide-in panel with topic bars, vibe pills, representative quotes. Animated entry, scrollable content |
| **Legend / colour key** | Without a legend, a choropleth is meaningless -- users cannot decode colour without reference | Low | Persistent legend showing colour-to-vibe mapping; position bottom-left or bottom-right of map |
| **Zoom and pan** | Fundamental map interaction; users will attempt pinch/scroll/drag immediately | Low | Handled by Mapbox GL JS / MapLibre natively; ensure scroll-zoom is enabled but guarded on mobile (two-finger scroll) |
| **Dark basemap** | Specified in PROJECT.md; dark maps are standard for data-art visualization (reduces distraction, makes fills pop) | Low | Use Mapbox dark style or custom MapLibre style; suppress most label layers to keep visual focus on data |
| **Responsive layout** | Users will visit on phones; a non-functional mobile experience signals amateur work | Medium | Map full-viewport on mobile; sidebar becomes bottom sheet; controls repositioned for thumb reach; touch targets >= 44x44px |
| **Loading states** | NLP data loads asynchronously; a blank map with no feedback is confusing | Low-Medium | Skeleton shimmer over sidebar content area; map tiles load progressively; subtle spinner or progress indicator during initial GeoJSON fetch |
| **Neighbourhood boundary outlines** | Even without fill, users need to see where one neighbourhood ends and another begins | Low | Thin stroke on polygon boundaries; visible on hover/selection; helps orientation |
| **Basic accessibility** | WCAG 2.1 AA compliance is expected for public portfolio work | Medium | Keyboard navigation for neighbourhood selection (Tab/Arrow); focus ring on active neighbourhood; alt-text summary of map content; 4.5:1 contrast on all text |

## Differentiators

Features that transform this from "another map" into something portfolio-worthy and memorable. These are what make someone say "this is really well done."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Time slider with animated transitions** | The killer feature -- watching neighbourhoods shift colour/vibe year-by-year (2019-2025) is viscerally compelling; few portfolio projects have temporal animation | High | Horizontal slider with year ticks (2019-2025); play/pause button for auto-advance; smooth colour interpolation between years using CSS transitions or deck.gl transition system; fixed time span per step |
| **Smooth animated colour transitions** | Colours morphing between vibes on year change or filter swap communicates "alive" data rather than static snapshots | Medium | Interpolate fill colours over ~400ms on any data change; use `fill-color-transition` in Mapbox GL or custom tween; avoid jarring snap-changes |
| **"Data art" visual quality** | The Pudding / NYT Upshot aesthetic -- the visualization itself is the content, not a dashboard wrapper around a map | High | Glow effects on dominant-vibe polygons; custom typography in sidebar; micro-animations on topic bars; considered colour palette (not default ColorBrewer); overall polish that rewards screenshot-sharing |
| **Vibe archetype system** | Six named archetypes (artsy, foodie, nightlife, family, upscale, cultural) give the data personality and memorability; easier to understand than raw topic clusters | Medium | Colour-coded pills/badges per archetype; each archetype gets an icon or emoji; radar/spider chart showing neighbourhood's archetype profile |
| **"Find similar neighbourhoods" (FAISS)** | Click a neighbourhood, see which others feel like it -- leverages the FAISS nearest-neighbour backend and demonstrates ML systems thinking | Medium | Button in sidebar: "Neighbourhoods like this"; highlights similar polygons on map with connecting animation or pulsing effect; shows similarity score |
| **Representative review quotes** | Grounds abstract vibe scores in real human language; makes the data feel tangible | Low-Medium | 2-3 cherry-picked quotes per topic per neighbourhood; styled as pull-quotes with attribution; loaded from pre-computed backend |
| **Pulsing/glowing hover effects** | Subtle animation on hover (polygon glow, boundary pulse) signals interactivity and elevates perceived quality | Low-Medium | CSS/WebGL glow on hovered polygon; slight scale or brightness increase; smooth ease-in/ease-out |
| **URL-driven state (deep linking)** | Share a link to a specific neighbourhood at a specific year -- essential for portfolio sharing and social media | Medium | Encode selected neighbourhood + year + active vibe in URL hash or query params; parse on load to restore state; enables bookmarking |
| **OG image / social sharing** | When shared on Twitter/LinkedIn, the link preview shows a beautiful map snapshot rather than a generic fallback | Medium | Server-side or edge-rendered OG images via Vercel OG or similar; dynamic per-neighbourhood if deep-linked; static fallback for root URL |
| **Temporal drift narrative** | Not just showing year-by-year but calling out "biggest movers" -- which neighbourhoods changed the most, in what direction | Medium | Small callout cards or annotations on the map; "Williamsburg shifted from artsy to upscale 2019-2024"; computed from temporal drift vectors |

## Anti-Features

Features to deliberately NOT build for v1. Building these would add complexity without proportional value, or actively harm the product.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **User accounts / login** | Explicitly out of scope (PROJECT.md); adds auth complexity, privacy concerns, zero value for a read-only visualization | Keep fully public, no login wall |
| **User-submitted reviews or ratings** | Crowdsourcing needs moderation, spam prevention, data quality pipeline -- massive scope increase for marginal value | Consume only pre-collected API data |
| **Real-time data updates** | PROJECT.md specifies static batch pipeline; real-time adds WebSocket complexity, pipeline re-runs, cost | Pre-compute all results; display "Data as of [date]" |
| **Street-level / building-level granularity** | 30-neighbourhood choropleth is the right abstraction; going finer requires orders of magnitude more data, different viz approach | Stick with neighbourhood-level polygons; mention granularity as future work |
| **3D map extrusions** | 3D choropleth bars look impressive in screenshots but are harder to read, interact with, and make accessible; they obscure neighbouring polygons | Use 2D fills with good colour encoding; 3D adds visual noise without information gain |
| **Comparison mode (side-by-side maps)** | Two synchronized maps doubles rendering cost and interaction complexity; the time slider already handles temporal comparison | Single map with time slider; sidebar can show "then vs now" data textually |
| **Full-text search across reviews** | Requires search index infrastructure (Elasticsearch/Meilisearch); users don't come to this app to search reviews | Show curated representative quotes only |
| **PDF/image export** | Export functionality is engineering-heavy (html2canvas, server-side rendering); screenshots suffice for a portfolio piece | Good OG images + deep linking covers the sharing use case |
| **Onboarding tutorial / walkthrough** | If the UI needs a tutorial, the UI is too complex; data-art visualizations should be explorable without instruction | Make interactions self-evident; brief intro text overlay that dismisses on first click |
| **Multiple cities / global scope** | NYC focus is the constraint; multi-city adds data collection, pipeline, and UI complexity | Ship NYC (Manhattan + Brooklyn) well; architecture should not preclude expansion but v1 is single-city |
| **Chatbot / AI assistant** | Trendy but adds LLM integration complexity with no clear user need for a visualization product | Let the map and sidebar be the interface |

## Feature Dependencies

```
Choropleth fills ──> Hover tooltip (needs polygon data to show info)
                ──> Click-to-detail sidebar (needs polygon selection)
                ──> Legend (needs colour scheme defined)
                ──> Time slider (needs temporal vibe data to animate fills)

Dark basemap ──> Choropleth fills (fills render on top of basemap)

Sidebar ──> Representative quotes (displayed within sidebar)
        ──> Vibe archetype pills (displayed within sidebar)
        ──> "Find similar" button (action within sidebar)

Time slider ──> Animated colour transitions (triggered by year change)
            ──> Temporal drift narrative (derived from multi-year data)

URL-driven state ──> OG image generation (needs URL params to generate per-neighbourhood images)

Loading states ──> Skeleton shimmer (sidebar)
               ──> Progressive tile loading (map)

Responsive layout ──> Bottom sheet sidebar (mobile variant)
                  ──> Touch gesture handling (mobile)
```

## MVP Recommendation

**Phase 1 -- Core Map (ship something visible fast):**
1. Dark basemap with choropleth neighbourhood fills (table stakes)
2. Hover tooltip with neighbourhood name + dominant vibe (table stakes)
3. Click-to-detail sidebar with vibe archetype breakdown (table stakes)
4. Legend (table stakes)
5. Loading states with skeleton shimmer (table stakes)
6. Basic responsive layout (table stakes)

**Phase 2 -- The "Wow" Layer:**
1. Time slider with animated transitions (top differentiator; this is the feature people will remember)
2. Smooth animated colour interpolation between years (elevates time slider from functional to beautiful)
3. Representative review quotes in sidebar (grounds data in reality)
4. Pulsing/glowing hover effects (visual polish)

**Phase 3 -- Portfolio Polish:**
1. URL-driven deep linking (enables sharing)
2. OG image generation (makes shared links look professional)
3. "Find similar neighbourhoods" via FAISS (demonstrates ML depth)
4. Temporal drift narrative callouts (storytelling layer)
5. Accessibility audit and keyboard navigation (professional completeness)

**Defer indefinitely:** All anti-features listed above. If time runs short, Phase 3 items can be cut without the product feeling incomplete.

## Colour Scheme Approach

**Use a custom qualitative palette, not default ColorBrewer.** Each of the 6 vibe archetypes maps to a distinct hue:

| Archetype | Suggested Hue | Rationale |
|-----------|---------------|-----------|
| Artsy | Purple/violet | Creative, unconventional |
| Foodie | Warm orange | Appetite, warmth |
| Nightlife | Electric blue/cyan | Neon, evening energy |
| Family | Green | Parks, safety, growth |
| Upscale | Gold/champagne | Luxury, refinement |
| Cultural | Deep red/terracotta | Heritage, richness |

For the choropleth fill, use the dominant archetype's hue at varying saturation/lightness to encode strength. Neighbourhoods with mixed vibes can use the dominant colour at reduced opacity or a blended hue.

**Accessibility:** Test all 6 hues through Sim Daltonism or similar tool for deuteranopia/protanopia/tritanopia distinguishability. Avoid red-green adjacency. Ensure each archetype is also distinguishable by icon/label, not colour alone (WCAG SC 1.4.1).

## Sources

- [Map UI Patterns](https://mapuipatterns.com/patterns/) -- Catalogue of established map interaction patterns
- [NN/g: Building Interactive UX Maps](https://www.nngroup.com/articles/interactive-ux-maps/) -- Research-backed map UX guidance
- [Map UI Patterns: Timeline Slider](https://mapuipatterns.com/timeline-slider/) -- Temporal slider pattern documentation
- [ColorBrewer 2.0](https://colorbrewer2.org/) -- Colour scheme selection for cartography
- [BOIA: Interactive Maps and Accessibility](https://www.boia.org/blog/interactive-maps-and-accessibility-4-tips) -- WCAG compliance for maps
- [MN IT: Accessibility Guide for Interactive Web Maps](https://mn.gov/mnit/assets/Accessibility%20Guide%20for%20Interactive%20Web%20Maps_tcm38-403564.pdf) -- Screen reader and keyboard patterns
- [Vercel OG Image Generation](https://vercel.com/blog/introducing-vercel-og-image-generation-fast-dynamic-social-card-images) -- Dynamic social card generation
- [NN/g: Skeleton Screens](https://www.nngroup.com/articles/skeleton-screens/) -- Loading state UX research
- [Map UI Patterns: Mobile Map](https://mapuipatterns.com/mobile-map/) -- Touch gesture and responsive patterns
- [Eleken: Map UI Design Best Practices](https://www.eleken.co/blog-posts/map-ui-design) -- Comprehensive map UI guidance
- [UXPin: Map UI Layouts](https://www.uxpin.com/studio/blog/map-ui/) -- Layout patterns for map applications
- [Datawrapper: How to Create Tooltips](https://academy.datawrapper.de/article/116-how-to-create-useful-tooltips-for-your-maps) -- Tooltip design for maps
- [Hands-On Data Viz: Design Choropleth Colors](https://handsondataviz.org/design-choropleth.html) -- Colour interval and scheme guidance
