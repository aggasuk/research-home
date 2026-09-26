"""Canonical Research Home shell, shared by scoped and full-site publishers."""
import re
from pathlib import Path

PAYLOAD = re.compile(r'const DATA = (.*?);\r?\nconst \$', re.S)


def render_navigation(page):
    payload = PAYLOAD.search(page)
    if not payload:
        raise ValueError('Missing saved Research Home payload')
    css = re.search(r'<style>(.*?)</style>', page, re.S).group(1)
    # Avoid accumulating the shell additions on repeated packaging.
    css = css.split('/* consolidated-navigation */')[0].strip()
    template = Path(__file__).with_name('navigation.html').read_text(encoding='utf-8')
    return template.replace('<!-- BASE_STYLE -->', css).replace('<!-- SAVED_DATA -->', payload.group(1))


def render_tracker(page):
    return page.replace('<title>Rates paper tracker</title>', '<title>Rates Trend</title>').replace(
        '<h1>Rates pullback paper tracker</h1>', '<h1>Rates Trend</h1>')
