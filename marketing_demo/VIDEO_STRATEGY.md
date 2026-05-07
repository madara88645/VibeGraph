# VibeGraph — Video & Distribution Strategy

Companion doc for `vibegraph_demo.mp4` (1920×1080 Product Hunt / landing narrative). Product URL: [https://vibegraph.vercel.app](https://vibegraph.vercel.app).

---

## 1) Hero Ad (60s, Product Hunt)

**Storyboard (timestamps)**  

| Time | Visual | Audio / VO cue |
|------|--------|----------------|
| 0:00–0:05 | Clean empty state; headline “Visualize any codebase” | VO: “New codebase?” |
| 0:05–0:15 | Upload demo zip/folder; analyzer spinner → graph bloom | “Upload once.” |
| 0:15–0:25 | Smooth pan/zoom; hover; lock onto entry node (`fetchUserData`) | “See every function and call edge.” |
| 0:25–0:40 | Explanation panel; cut Beginner → Intermediate → Advanced | “Pick your explanation depth.” |
| 0:40–0:55 | Chat drawer; question about entry point; streamed reply | “Ask anything about structure.” |
| 0:55–1:05 | Ghost Runner auto mode; trail + narration bubble | “Watch an AI guide walk the graph.” |
| 1:05–1:15 | Pause; Run Summary stats | “Pause anytime — recap where you’ve been.” |
| 1:15–1:20 | Wide hero shot; visited highlights | CTA line |

**On-screen text overlays**  

- 0:02 — **Turn repos into live maps**  
- 0:08 — **Upload · Python · JS · TS**  
- 0:18 — **Your call graph, explorable**  
- 0:30 — **Beginner · Intermediate · Advanced**  
- 0:44 — **Ask the codebase**  
- 0:58 — **Ghost Runner**  
- 1:08 — **Run summary**  
- 1:16 — **vibegraph.vercel.app**

**Music mood**  

Light ambient electronica (90–110 BPM), optimistic minor-to-major lift at graph reveal; duck −12 dB under VO.

**CTA**  

Button-style lower third: **Try VibeGraph free** → URL. Secondary: **Bring your OpenRouter key for AI** (honesty beats disappointment).

**Optional full voice-over script**  

“Starting a new codebase shouldn’t feel like reading a wall of files. VibeGraph turns your project into a live map — upload a zip or folder, and every function and call edge appears instantly. Click any node for explanations at beginner, intermediate, or advanced depth. Ask questions in chat, then switch on Ghost Runner to watch an AI tracer narrate its walk through your graph. Pause when you need to breathe — your summary is always there. Map your next codebase at vibegraph dot vercel dot app.”

---

## 2) 15s Short Hook (X / Instagram Reels)

**Before / after**  

- **Before:** Dense IDE tree + confusion.  
- **After:** Same repo as an interactive graph + one-line AI explanation.

**First 2 seconds (hook)**  

Full-frame graph morph from messy folder icons → single glowing graph; supersize text: **“Stop drowning in files.”**

**Exact overlay text**  

1. (0:00–0:02) **Stop drowning in files**  
2. (0:03–0:06) **Upload → instant call graph**  
3. (0:07–0:11) **Ghost Runner walks the code for you**  
4. (0:12–0:15) **vibegraph.vercel.app · AI depth levels**

Vertical export: 1080×1920 safe zones for UI chrome.

---

## 3) Reddit / HN GIF (8s loop)

**Recommended moment**  

Ghost Runner segment: **first three node hops** with active edge dash + narration bubble updating — crop centered on the graph pane.

**Why this moment**  

Differentiator is visible without audio; loop feels “alive” at low frame cost; matches curiosity-driven HN/Reddit audiences.

**Export guidance**  

- Crop **800×450** (16:9 slice of the 1920×1080 graph pane).  
- 12–15 fps, **palette + gifsicle** compression or MP4 loop under 5 MB where GIF isn’t required.  
- Target **under 5 MB** for Reddit inline tolerance.

---

## 4) Platform-Specific Cuts

| Platform | Length | Aspect | Voice / text | Audience emphasis |
|----------|--------|--------|--------------|-------------------|
| **YouTube pre-roll** | 15s or 30s bumper | 16:9 | VO + burned-in key phrases | Developers actively searching “codebase map” or onboarding tools |
| **X / Twitter** | 15s | 1:1 or 9:16 | Big captions, optional VO | Scroll-stoppers who learn visually |
| **LinkedIn** | 30–45s | 1:1 or 16:9 | VO-led, minimal jargon | Engineers onboarding to teams; emphasize ramp-up time saved |
| **Reddit** | 8–12s silent GIF / MP4 | 16:9 crop | Text overlays only | Proof-first skeptics; show graph + Ghost in one breath |
| **Product Hunt** | 60s hero | 16:9 | VO optional; captions on | Makers evaluating workflow depth before install |

---

## 5) A/B Hooks for the 60s Ad

**Hook A — Problem-led**  

Opening line: *“Your IDE shows files — not relationships.”*  

**Fits:** Junior devs and bootcamp grads who feel lost in folder trees. **Why:** Names the pain before the product.

**Hook B — Demo-led**  

Opening line: *“Watch this repo become a map in ten seconds.”*  

**Fits:** Intermediate devs evaluating tooling quickly. **Why:** Immediate competence signal; less empathy framing, more proof.

---

## 6) 3-Week Posting Calendar

Assumes primary geography US/EU tech; adjust ±2h for audience analytics.

| Week | Day | Time (UTC) | Platform | Content type |
|------|-----|------------|----------|----------------|
| 1 | Tue | 14:00 | Product Hunt | Launch teaser — 20s cut + maker comment |
| 1 | Wed | 16:30 | LinkedIn | 40s VO — onboarding angle |
| 1 | Thu | 17:00 | X | 15s hook + thread with GIF |
| 1 | Sat | 15:00 | Reddit (r/webdev or r/learnprogramming) | 8s GIF + honest “needs OpenRouter key” top comment |
| 2 | Mon | 14:00 | YouTube Shorts | Vertical crop — Ghost Runner loop |
| 2 | Wed | 09:00 | LinkedIn | Problem-led Hook A variant |
| 2 | Fri | 18:00 | X | Poll: “How do you onboard?” + demo clip |
| 2 | Sun | 20:00 | Reddit side subs | Show HN-style technical GIF |
| 3 | Tue | 14:00 | Product Hunt | Ship recap — metrics + user quote card |
| 3 | Thu | 15:00 | LinkedIn | Demo-led Hook B + carousel (4 slides) |
| 3 | Fri | 12:00 | X | Behind-the-scenes: recording setup / honesty post |
| 3 | Sun | 16:00 | YouTube | Full 60s + pinned chapters |

---

## Recording reproducibility

- Demo sources: `marketing_demo/demo_project/` (archive: `demo_project.zip`).  
- Automation: `marketing_demo/record_vibegraph_demo.py` → WebM → H.264 MP4 via ffmpeg (see script).  
- Production AI requires a **session OpenRouter key** (AI Settings modal); graph upload works without it.
