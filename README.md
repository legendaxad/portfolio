# Ahadjon — Portfolio

Personal portfolio of a Python Backend & Full-Stack Developer. It's a server-rendered
Django site with a WebGL hero, GSAP scroll storytelling and an admin-managed content model.

## Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Backend | Django 6, SQLite | Already in place; admin-managed content |
| Templates | Django templates (SSR) | Fast first paint, SEO, works without JS |
| Motion | GSAP 3.12 + ScrollTrigger (self-hosted in `blog/static/vendor`) | Pinned horizontal reel, scrubbed timelines |
| Hero | Raw WebGL fragment shader (`blog/static/js/hero-shader.js`) | No Three.js needed for a full-screen quad |
| Icons | Simple Icons (CC0) SVGs in `blog/static/icons/tech` | Official brand marks, rendered as CSS masks |
| Fonts | Geist, Geist Mono, Instrument Serif (Google Fonts) | |

No Node build step and no new Python packages; `gunicorn` is only for production.

## Project layout

```
blog/
  models.py            PersonalInfo (singleton), SkillCategory/Skill, Project (+ProjectImage gallery),
                       JourneyMilestone, Certificate, Question (FAQ), Contact, BlogCategory/BlogPost
  views.py             home + contact (AJAX & non-JS), project/post detail, GitHub proxy, robots
  github.py            Cached server-side GitHub REST client (stale fallback, optional token)
  forms.py             Contact form: validation, honeypot, signed timing token
  sitemaps.py          /sitemap.xml
  templatetags/portfolio.py   tech icons, safe `rich_text` formatter
  management/commands/sync_portfolio_content.py   idempotent, verified content refresh
  templates/blog/sections/*.html   one file per home-page section
  static/css/site.css  design system (tokens → components)
  static/js/site.js    interactions (nav, cursor, reel, filters, carousel, contact, GitHub…)
templates/base.html, components/, 404.html
```

## Running locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py sync_portfolio_content --dry-run   # preview content updates
python manage.py sync_portfolio_content             # apply (idempotent, never deletes)
python manage.py runserver
python manage.py test blog
```

## Managing content (Django Admin → /admin/)

- **Personal Profile & Site Settings**: name, hero title (wrap a phrase in `*asterisks*` to accent it),
  bio paragraphs, education, availability, email, GitHub/LinkedIn/Telegram, avatar, CV.
- **Projects**: title, slug, short + full description (blank lines = paragraphs, `## ` headings,
  `- ` lists; URLs auto-link), cover image, gallery images (inline), linked technologies or a
  comma-separated stack, GitHub / live URLs, category, status, featured, published, order, accent colour.
  Featured projects appear in the pinned horizontal reel; all published projects appear in the grid.
  A project without a cover gets a generated placeholder instead of a broken image.
- **Skill categories / Skills**: mark one category as *primary* to make it the large tile; `icon` is the
  file name in `static/icons/tech` (auto-detected from the name when blank).
- **Journey milestones**: `kind` = Education / Independent projects / Current learning.
- **Certificates, FAQs, Contacts** (mark as read), **Blog categories / posts** (draft → published; staff can
  preview drafts at their URL).

## Deploying (Gunicorn + Nginx on Linux)

1. Pull the code, then `pip install -r requirements.txt`.
2. Provide environment variables (see `.env.example`), e.g. in the systemd unit:
   ```ini
   [Service]
   EnvironmentFile=/srv/portfolio/.env
   WorkingDirectory=/srv/portfolio
   ExecStart=/srv/portfolio/venv/bin/gunicorn config.wsgi:application --bind unix:/run/portfolio.sock --workers 3
   ```
3. `python manage.py migrate && python manage.py collectstatic --noinput`
4. Optionally run `python manage.py sync_portfolio_content --dry-run`, then without the flag.
5. Nginx:
   ```nginx
   location /static/ { alias /srv/portfolio/staticfiles/; expires 30d; add_header Cache-Control "public"; }
   location /media/  { alias /srv/portfolio/media/; expires 7d; }
   location / {
       proxy_pass http://unix:/run/portfolio.sock;
       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
   }
   ```
6. The GitHub section caches API responses in `.cache/` (file cache shared by all workers).
   Make sure the app user can write there, or set `DJANGO_CACHE_DIR`.

With `DJANGO_DEBUG=0`, secure cookies, `nosniff` and the referrer policy are enabled automatically.
The custom 404 page is only used when DEBUG is off.
