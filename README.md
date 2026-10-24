# Personal AI Skills

**Shaxsiy AI agent skill’lar to‘plami** — tajriba va loyihalar asosida yig‘ilgan, Cursor va boshqa AI agentlar uchun qo‘llanmalar.

**Personal collection of AI agent skills** — guides built from real project experience, for Cursor and other AI coding agents.

---

## Maqsad / Purpose

Bu repozitoriy agentlarga aniq vazifalar (UI/UX, kod sifati, domen-specific ishlar) bo‘yicha qanday ishlash kerakligini tushuntiruvchi `SKILL.md` fayllarini saqlaydi. Skill’lar versiyalanadi, nusxalanadi va kerak bo‘lganda yangilanadi.

This repository holds `SKILL.md` files that instruct agents how to work on specific tasks (UI/UX, code quality, domain workflows). Skills are versioned, copied, and updated as practices evolve.

---

## Skill’lar / Skills

| Skill | Qisqacha / Summary |
|-------|-------------------|
| [`crm-erp-ui-ux`](./crm-erp-ui-ux/) | CRM/ERP veb interfeyslari (React): app shell, data grid, formalar, accessibility, operational dashboard dizayn. |
| [`mobile-ux-pro`](./mobile-ux-pro/) | iPhone va Android (SwiftUI, Compose), Flutter, React Native uchun mobil UX/UI: holat, navigatsiya, formalar, ruxsatlar, onboarding, accessibility. / Mobile UX/UI for iOS, Android, Flutter and React Native: screen states, navigation, forms, permissions, onboarding, accessibility. |
| [`pragmatic-clean-code`](./pragmatic-clean-code/) | O‘qilishi oson, maintainable kod: SOLID, DRY, KISS, YAGNI, refaktoring va arxitektura chegaralari. |
| [`anti-slop-video`](./anti-slop-video/) | AI-slop belgilarisiz video/reels: aniq skript, o‘ziga xos vizual, jonli harakat va ovoz, QA-gate va copy linter. / Make video that doesn’t read as AI slop: specific scripts, distinct visuals, organic motion and voice, QA gate and copy linter. |
| [`anti-slop-voice`](./anti-slop-voice/) | AI/TTS ovozini "robotcha"likdan xalos qilish: ona tili ovozi, to‘g‘ri temp, buzmaydigan post-zanjir, mix maqsadlari, QC skripti. / Natural, non-robotic TTS voiceover for videos: native voice, real pace, damage-free post chain, mix targets, objective QC script. |

Har bir papkada `SKILL.md` — agent uchun asosiy ko‘rsatma; qo‘shimcha `reference.md`, `examples.md` va `agents/` bo‘lishi mumkin.

Each folder contains a primary `SKILL.md`; optional `reference.md`, `examples.md`, and `agents/` config may be included.

---

## Tuzilma / Structure

```
personal-ai-skills/
├── README.md
├── .gitignore
├── crm-erp-ui-ux/
│   ├── SKILL.md
│   ├── reference.md
│   └── examples.md
└── pragmatic-clean-code/
    ├── SKILL.md
    └── agents/
        └── openai.yaml
```

**Odatiy qoida:** bitta skill = bitta papka, nomi skill `name` maydoniga mos.

**Convention:** one skill per directory; directory name matches the skill `name` in frontmatter.

---

## Foydalanish / Usage

Skill’ni agent muhitiga nusxalang (masalan, Cursor skills papkasi) yoki repodan to‘g‘ridan-to‘g‘ri o‘qing. Agent vazifa matnida skill nomi yoki tegishli kalit so‘zlar bo‘lsa, tegishli `SKILL.md` ni qo‘llaydi.

Copy a skill into your agent environment (e.g. Cursor skills folder) or reference this repo directly. Agents apply the relevant `SKILL.md` when the task matches the skill description or triggers.

---

## Litsenziya

Shaxsiy foydalanish va o‘rganish uchun. Tashqi loyihalarda ishlatishdan oldin o‘z litsenziyangizni qo‘shing.

Personal use and learning. Add your own license if you publish or reuse in other projects.
