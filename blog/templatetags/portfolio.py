import re

from django import template
from django.templatetags.static import static
from django.utils.html import escape, urlize
from django.utils.safestring import mark_safe

register = template.Library()

# Official brand colours (from Simple Icons, CC0). Dark brands are lifted so
# they stay visible on the near-black background.
BRAND = {
    "python": "#3776AB", "django": "#44B78B", "fastapi": "#009688",
    "nodedotjs": "#5FA04E", "express": "#E6E6E6", "react": "#61DAFB",
    "typescript": "#3178C6", "javascript": "#F7DF1E", "html5": "#E34F26",
    "css3": "#1572B6", "mongodb": "#47A248", "postgresql": "#4169E1",
    "sqlite": "#4FA3D9", "redis": "#FF4438", "linux": "#FCC624",
    "docker": "#2496ED", "nginx": "#009639", "gunicorn": "#499848",
    "git": "#F05032", "github": "#E6E6E6", "jsonwebtokens": "#D63AFF",
    "stripe": "#635BFF", "mui": "#007FFF", "digitalocean": "#0080FF",
    "telegram": "#26A5E4", "gnubash": "#4EAA25", "redux": "#764ABC",
    "swagger": "#85EA2D", "postman": "#FF6C37",
}

# Fallback name → icon mapping for skills without an explicit icon.
NAME_TO_ICON = [
    (r"rest framework|drf", "django"), (r"django", "django"), (r"fastapi", "fastapi"),
    (r"python", "python"), (r"node", "nodedotjs"), (r"express", "express"),
    (r"react native", "react"), (r"react", "react"), (r"typescript", "typescript"),
    (r"javascript", "javascript"), (r"html", "html5"), (r"css", "css3"),
    (r"mongo", "mongodb"), (r"postgres", "postgresql"), (r"sqlite", "sqlite"),
    (r"redis", "redis"), (r"linux|shell", "linux"), (r"docker", "docker"),
    (r"nginx", "nginx"), (r"gunicorn", "gunicorn"), (r"github", "github"),
    (r"\bgit\b", "git"), (r"jwt", "jsonwebtokens"), (r"stripe", "stripe"),
    (r"material ui|\bmui\b", "mui"), (r"digitalocean", "digitalocean"),
    (r"telegram", "telegram"), (r"redux", "redux"),
]


def resolve_icon(name, explicit=""):
    if explicit:
        return explicit
    low = (name or "").lower()
    for pattern, icon in NAME_TO_ICON:
        if re.search(pattern, low):
            return icon
    return ""


@register.simple_tag
def tech_icon(name, explicit=""):
    """Render a brand-coloured monochrome icon (CSS mask) or a monogram."""
    icon = resolve_icon(name, explicit)
    if not icon:
        letters = "".join(w[0] for w in re.findall(r"[A-Za-z]+", name or "")[:2]).upper() or "•"
        return mark_safe(f'<span class="ti ti--mono" aria-hidden="true">{escape(letters)}</span>')
    color = BRAND.get(icon, "#E6E6E6")
    url = static(f"icons/tech/{icon}.svg")
    return mark_safe(
        f'<span class="ti" aria-hidden="true" style="--ti-c:{color};--ti-u:url(\'{url}\')"></span>'
    )


@register.filter
def rich_text(value):
    """Tiny, safe formatter: paragraphs, '## ' headings, ``` code fences, links.

    All user text is escaped first, so admin content can't inject HTML.
    """
    if not value:
        return ""
    out, para, code, in_code = [], [], [], False

    def flush_para():
        if para:
            html = urlize(escape(" ".join(para)), nofollow=True, autoescape=False)
            out.append(f"<p>{html}</p>")
            para.clear()

    for line in value.replace("\r\n", "\n").split("\n"):
        if line.strip().startswith("```"):
            if in_code:
                out.append(f"<pre><code>{escape(chr(10).join(code))}</code></pre>")
                code.clear()
            else:
                flush_para()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
        elif line.startswith("## "):
            flush_para()
            out.append(f"<h2>{escape(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            flush_para()
            out.append(f"<h3>{escape(line[4:].strip())}</h3>")
        elif line.strip().startswith(("- ", "* ")):
            flush_para()
            item = urlize(escape(line.strip()[2:]), nofollow=True, autoescape=False)
            if out and out[-1].endswith("</ul>"):
                out[-1] = out[-1][:-5] + f"<li>{item}</li></ul>"
            else:
                out.append(f"<ul><li>{item}</li></ul>")
        elif not line.strip():
            flush_para()
        else:
            para.append(line.strip())
    if in_code and code:
        out.append(f"<pre><code>{escape(chr(10).join(code))}</code></pre>")
    flush_para()
    return mark_safe("\n".join(out))


@register.filter
def split_words(value):
    return (value or "").split()
