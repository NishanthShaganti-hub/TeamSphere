# Student Project & Team Finder — Colour Guide (v2)

Replaces the colour tokens in section 2 of `ui-design-v2.md`. Everything else in that guide (layout, components, behaviour) still applies.

**Direction:** confident and friendly, not pale. A deep **indigo** brand colour, a **teal** secondary, and four small accent colours (violet, sky, amber, rose) used for categories, tags, avatars and highlights. Surfaces stay light so text is easy to read.

---

## 1. Palette

| Role | Token | Hex | Used for |
|---|---|---|---|
| Brand | `--primary` | `#3b43b5` | Primary buttons, links, active nav, selected filters |
| Brand dark | `--primary-hover` | `#2c3390` | Hover, hero gradient start |
| Brand tint | `--primary-soft` | `#eceefc` | Tag and hover backgrounds |
| Secondary | `--teal` | `#0f766e` | "Collaborate" buttons, team/people accents, hero gradient end |
| Secondary tint | `--teal-soft` | `#dcf4f0` | Personal-category pill, tags |
| Accent | `--violet` / `--violet-soft` | `#6d28d9` / `#efe7ff` | Hackathon pill, tags |
| Accent | `--sky` / `--sky-soft` | `#0369a1` / `#dff1fc` | Academic pill, tags |
| Accent | `--amber` / `--warn-soft` | `#d97706` / `#fef0c7` | In-progress rail, research pill, pending |
| Accent | `--rose` | `#be123c` | Notification count, errors, rejected |
| Page | `--bg` | `#f4f5fb` | Page background (cool, slightly blue-tinted) |
| Surface | `--surface` | `#ffffff` | Cards, navbar, inputs |
| Text | `--text` | `#1b1f3b` | Headings and body (deep navy, not pure black) |
| Muted text | `--muted` | `#555b7a` | Secondary text |
| Lines | `--border` / `--border-strong` | `#dfe2f0` / `#b9bfdc` | Card borders / input borders |
| Success | `--success` / `--success-soft` | `#166534` / `#dcf5e5` | Looking for teammates, accepted |
| Warning | `--warn` / `--warn-soft` | `#92400e` / `#fef0c7` | In progress, pending |
| Danger | `--danger` / `--danger-soft` | `#be123c` / `#ffe4ea` | Delete, rejected, errors |
| Footer | n/a | `#1b1f3b` | Dark footer, text `#c9cde8` |

### Copy-paste tokens (`style.css`)

```css
:root{
  --bg:#f4f5fb; --surface:#ffffff; --text:#1b1f3b; --muted:#555b7a;
  --border:#dfe2f0; --border-strong:#b9bfdc;
  --primary:#3b43b5; --primary-hover:#2c3390; --primary-soft:#eceefc;
  --teal:#0f766e; --teal-hover:#0b5a54; --teal-soft:#dcf4f0;
  --violet:#6d28d9; --violet-soft:#efe7ff;
  --sky:#0369a1; --sky-soft:#dff1fc;
  --amber:#d97706; --rose:#be123c;
  --danger:#be123c; --danger-soft:#ffe4ea;
  --success:#166534; --success-soft:#dcf5e5;
  --warn:#92400e; --warn-soft:#fef0c7;
  --radius:12px;
  --shadow:0 1px 2px rgba(27,31,59,.06),0 6px 18px rgba(27,31,59,.07);
}
```

---

## 2. Where colour is used

| Element | Colour treatment |
|---|---|
| **Navbar** | White with a 4px indigo-to-teal strip on top; logo mark uses the same gradient; active link is indigo on a soft indigo pill; request count badge is rose |
| **Landing hero** | Indigo-to-teal gradient banner with white text, live counts (projects, students, archive), white and outlined buttons |
| **How-it-works cards** | Coloured top border: indigo, teal, violet, amber |
| **Project card** | 5px left **status rail**: green = looking for teammates, amber = in progress, blue-grey = completed. Category pill: violet = hackathon, sky = academic, teal = personal, amber = research |
| **Student card** | Teal left rail, coloured initials avatar, teal "Collaborate" button |
| **Skill tags** | Six tints (indigo, teal, violet, sky, amber, rose) picked from the skill text, so the same skill is always the same colour |
| **Avatars** | Solid colour chosen by `user.id % 6`, white initials |
| **Dashboard stats** | Left border and number coloured indigo, teal, amber |
| **Primary buttons** | Indigo. **Secondary:** white with border. **Collaborate:** teal. **Danger:** white with rose text |
| **Footer** | Deep navy with light text |

Rules:
- Colour never carries meaning alone. Status badges and category pills always include text.
- Use **at most one** strong colour block per screen section (the hero is the only large one).
- Keep body text on white or `--bg`. Do not put paragraph text on coloured tints other than the soft tints above.
- Tag colours are decoration. They must not imply importance.

### Skill tag colour helper

```js
const tagCls = s => "t" + ([...s].reduce((a, c) => a + c.charCodeAt(0), 0) % 6);
```

In Jinja, add a small filter (for example `skill_color`) that returns `t0` to `t5` using the same sum-of-characters rule, so server-rendered pages match the preview.

---

## 3. Contrast check

Ratios computed with the WCAG formula (AA needs 4.5 or more for normal text).

| Pair | Ratio |
|---|---|
| Text `#1b1f3b` on page `#f4f5fb` | 14.8 |
| Muted `#555b7a` on white | 6.6 |
| White on primary `#3b43b5` | 7.9 |
| White on teal `#0f766e` | 5.5 |
| Primary on primary-soft | 6.9 |
| Success `#166534` on `#dcf5e5` | 6.2 |
| Warn `#92400e` on `#fef0c7` | 6.2 |
| Danger `#be123c` on `#ffe4ea` | 5.2 |
| Tag text on tag tints (all six) | 6.5 to 9.2 |
| White on avatar colours (lowest: amber `#b45309`) | 5.0 |
| Hero text `#eef0ff` on gradient (lowest, teal end) | 4.8 |
| Footer text `#c9cde8` on `#1b1f3b` | 10.2 |

Re-check any new colour pair before adding it.

---

## 4. Easy theme swaps

Everything uses the tokens above, so changing the brand is a three-line edit. Both options keep AA contrast with white button text.

| Theme | `--primary` | `--primary-hover` | `--primary-soft` | Secondary (`--teal`) |
|---|---|---|---|---|
| **Indigo + Teal** (default) | `#3b43b5` | `#2c3390` | `#eceefc` | `#0f766e` |
| **Ocean** (teal-led) | `#0f766e` | `#0b5a54` | `#dcf4f0` | `#3b43b5` |
| **Plum** (violet-led) | `#6d28d9` | `#5b21b6` | `#efe7ff` | `#0f766e` |

For the hero gradient, update its three colour stops to match: darker brand, brand, secondary.

---

## 5. Hero gradient (copy-paste)

```css
.hero{
  padding:3rem 2rem; border-radius:18px; color:#fff;
  background:linear-gradient(135deg,#2c3390 0%,#3b43b5 55%,#0f766e 130%);
}
```

Keep headline white and body text `#eef0ff`. Buttons: white fill with indigo text, and a transparent one with a white outline.
