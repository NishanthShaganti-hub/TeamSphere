# Student Project & Team Finder — UI Design Spec (v1)

Companion to `requirements.md`. Describes how every page should look and behave.
Style goals: **clean, calm, student-friendly, interactive, no loud colours.**
Stack reminder: HTML5, CSS3, vanilla JS, Jinja templates. No frameworks.

---

## 1. Design Principles

1. **Neutral first.** White and light-grey surfaces, one muted slate accent. No gradients, neon, or bright colours.
2. **Content over decoration.** Cards, whitespace, and clear headings. Minimal icons and shadows.
3. **Interactive but simple.** Live search, filter chips, modals, toasts. All in vanilla JS.
4. **Accessible by default.** Semantic HTML, visible focus, contrast of at least 4.5:1, works with keyboard only.
5. **Mobile first.** Everything usable at 360px wide.
6. **One source of style.** Shared `static/css/style.css` and `static/js/main.js`. No duplicated CSS or JS per page.

---

## 2. Colour Palette

Define as CSS variables in `:root`.

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#f6f7f8` | Page background |
| `--surface` | `#ffffff` | Cards, navbar, forms |
| `--text` | `#1f2328` | Main text |
| `--muted` | `#59636e` | Secondary text, hints |
| `--border` | `#d9dee3` | Card and divider borders |
| `--border-strong` | `#b9c1c9` | Input borders, outlined buttons |
| `--primary` | `#2f3e4e` | Primary buttons, active states (slate) |
| `--primary-hover` | `#1f2a36` | Primary hover |
| `--primary-soft` | `#e9edf1` | Tags, hover backgrounds |
| `--success` / `--success-soft` | `#2f6b4f` / `#e7f1ec` | "Looking for teammates", accepted |
| `--warn` / `--warn-soft` | `#6b5a22` / `#f2eee3` | "In progress", pending |
| `--danger` / `--danger-soft` | `#9b2c2c` / `#f6e9e9` | Errors, delete, rejected |

Rules:
- Never use colour as the only signal. Badges always include text.
- Dark mode is optional and out of scope for v1.

## 3. Typography and Spacing

- Font: system stack — `system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`. No web fonts.
- Base size 16px, line height 1.55.
- Headings: h1 1.9rem, h2 1.35rem, h3 1.08rem.
- Spacing scale: 0.25 / 0.5 / 0.75 / 1 / 1.25 / 2 rem.
- Border radius: 10px cards, 8px inputs and buttons, 99px badges.
- Shadow: one soft shadow only, used on cards.
- Container: max width 1080px, 1.25rem side padding.

---

## 4. Components

### Navbar (`base.html`)
- Sticky, white, 1px bottom border, 60px tall.
- Left: logo mark and "Team Finder".
- **Logged out:** Projects, Team finder, Log in, Sign up (primary button).
- **Logged in:** Projects, Team finder, Dashboard, Requests (count badge for pending), My profile, Log out.
- Active link has a soft grey background and `aria-current="page"`.
- Under 760px the links collapse into a "Menu" button (`aria-expanded`).

### Buttons
| Type | Look | Use |
|---|---|---|
| Primary | Slate fill, white text | Main action per screen |
| Secondary | White, grey border | Cancel, Edit, filters |
| Danger | White, red text and border | Delete, Cancel request |
| Small | Reduced padding | In list rows |

Loading state: spinner inside the button and `disabled` while a request is in flight.

### Cards
White surface, 1px border, soft shadow. Project and student cards lift 2px on hover.

### Badges and tags
- **Status badges** (rounded pill): looking_for_teammates (green tint), in_progress (tan tint), completed (grey), pending (tan), accepted (green), rejected (red tint), cancelled (grey).
- **Skill tags:** small grey rounded rectangles. Filter tags are buttons with `aria-pressed`.

### Forms
- Every input has a visible `<label>`.
- Inline error text under the field (red, `role="alert"`) and a red border.
- Character counters on bio, short description, and request message.
- Skill/interest input uses **chips**: type, press Enter or comma to add, × or Backspace to remove. Normalize as in requirements section 6 (trim, lowercase, collapse spaces, dedupe, max 10 items, max 30 characters each).
- Every form includes the CSRF hidden field.

### Modal
Used for "Request to join / Collaborate" and "Confirm delete". Closes on Esc, backdrop click, or Cancel. Focus moves into the modal and returns to the trigger on close.

### Toasts
Bottom-right, auto-dismiss after about 3 seconds, in an `aria-live="polite"` region. Slate for success, red for errors.

### Empty states
Dashed-border box with a short heading, one-line help text, and a button to the next action. Examples: "No projects yet — create the first one."

### Pagination
Prev, numbered buttons, Next. Current page has `aria-current="page"`. 12 items per page.

### Loading state
While filters update, show 3 grey skeleton cards for about 150ms (or the real fetch time).

---

## 5. Page Specs

### 1. Landing — `index.html` (`/`)
- Hero: headline "Find teammates. Build something together.", one-line description, and two buttons (logged out: Get started and Browse projects; logged in: Post a project and Find teammates).
- "How it works" in four small cards: build profile, post/discover, team up, keep the archive.
- "Recent projects": 3 active project cards and a "View all" link.

### 2. Register — `register.html` (`/register`)
- Centered card, max width 440px.
- Fields: display name, college email, password (min 8).
- Inline validation on submit. Rate-limit message (429) shown in a toast.
- Link to login. **No role field.**

### 3. Login — `login.html` (`/login`)
- Email and password. A failed login always shows the generic "Invalid email or password."

### 4. Dashboard — `dashboard.html` (`/dashboard`)
- Greeting and "+ New project" button.
- Three stat cards: my projects, requests to review, awaiting reply.
- Two columns (stacked on mobile): **My projects** (title, category, member count, status badge, Edit) and **Pending requests** (Accept and Reject inline).

### 5. Profile — `profile.html` (`/profile/<id>`, `/profile/edit`)
- **View:** large initials avatar (or the image URL if provided), name, department, year, bio, skills, interests, and that user's projects in a side panel.
- Own profile: "Edit profile". Others: "Collaborate" button (disabled and labelled "Request pending" if one exists).
- Email is not shown. Note: "Contact happens through team-up requests."
- **Edit:** name, department select, year (1–6), bio (300 chars), skills chips, interests chips, optional image URL (http/https only).

### 6. Projects — `projects.html` (`/projects`)
- Segmented quick filter: **All · Open for teammates · In progress · Archive**.
- Search box (title/description), category select, year select, and clickable skill tags.
- Filters stay selected after searching or paging.
- Results count with "Clear filters" link. Grid of project cards, paginated.
- Archive view lists completed projects with the year visible.
- Empty state: "No projects match. Try a different keyword or clear a filter."

### 7. Project detail — `project_detail.html` (`/projects/<id>`)
- Left: status, category, year, title, full description, skills, repo link (opens in a new tab with `rel="noopener noreferrer"`).
- Right: owner card and team list (owner and members).
- Actions depend on the viewer:
  - Logged out: "Log in to request to join"
  - Owner: Edit and Delete (delete asks for confirmation)
  - Member: "You're on this team"
  - Completed project: "This project is completed and archived"
  - Others: "Request to join" (disabled with "Request pending" if pending)

### 8. Create / edit project — `create_project.html` (`/projects/new`, `/projects/<id>/edit`)
- Fields: title, short description (140 chars), full description, category, status, skills needed (chips), repository URL (optional, http/https).
- Inline errors, focus moves to the first invalid field. Non-owners get the 403 page.

### 9. Team finder — `team_finder.html` (`/team-finder`)
- One search box (name, department, skill, interest) and skill chips to filter.
- Student cards: initials avatar, name, department and year, short bio, skills, interests, "View profile", and "Collaborate".
- Shows only public details. Your own card is not listed.

### 10. Requests — `requests.html` (`/requests`)
- Tabs: **Received** and **Sent**, each with a count.
- Each row: person, project (or "Collaboration request"), note, status badge.
- Received and pending: Accept, Reject. Sent and pending: Cancel.
- Final statuses show no actions.

### Error pages
`403.html`, `404.html`, `500.html`: large code, one friendly sentence, "Back to home" button. Never show stack traces.

---

## 6. Interaction Rules

| Action | Behaviour |
|---|---|
| Search typing | Debounce about 250ms, then update results without a full reload |
| Filter change | Reset to page 1 and update results |
| Send request | Modal, optional note (max 300), loading button, success toast |
| Accept / Reject / Cancel | `fetch()` POST with CSRF token, update row and badge, toast |
| Delete project | Confirm modal, then toast and redirect to `/projects` |
| Form errors | Inline message and red border, never only a toast |

Server rules from requirements section 9 are always enforced by Flask. The UI only mirrors them (for example by disabling buttons) so users get early feedback.

## 7. Responsive Rules

| Width | Layout |
|---|---|
| Under 760px | Hamburger menu, single-column grids, toolbar stacked |
| 760–1080px | 2-column card grids |
| Over 1080px | 3-column card grids, centered container |

Two-column pages (detail, dashboard) stack under 800px.

## 8. Accessibility Checklist

- [ ] "Skip to content" link as first focusable element
- [ ] One `<h1>` per page, headings in order
- [ ] Landmarks: `<header>`, `<nav>`, `<main>`, `<footer>`
- [ ] Labels for all inputs, errors linked with `role="alert"`
- [ ] Visible focus outline (3px) on all interactive elements
- [ ] Modals trap focus, close on Esc, return focus on close
- [ ] Toast region uses `aria-live="polite"`
- [ ] Respect `prefers-reduced-motion`
- [ ] Contrast at least 4.5:1 for text

## 9. Security Notes for the UI

- Jinja auto-escape stays on. **Never use `|safe`** on user content.
- Every form and `fetch()` call sends the CSRF token (hidden input or `X-CSRFToken` header).
- Do not render `password_hash` or email of other users anywhere.
- Profile image is an `<img src>` from a validated http/https URL; show initials if it fails to load.

## 10. File Map

| File | Contains |
|---|---|
| `templates/base.html` | Navbar, flash messages, footer, toast container |
| `templates/*.html` | One per page in section 5, extending `base.html` |
| `static/css/style.css` | Tokens (section 2), components (section 4), responsive rules |
| `static/js/main.js` | Nav toggle, debounce search, chip input, modal, toast, request actions |

## 11. Out of Scope for v1 UI

Dark mode, animations beyond hover and skeleton, drag and drop, image upload, real-time chat, notifications beyond the nav count.
