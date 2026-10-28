# YORU-Explain's documents

The documentation site of [YORU-Explain](https://github.com/Kamikouchi-lab/YORU-Explain),
published at <https://kamikouchi-lab.github.io/YORU-Explain_doc/>.

It is a [Jekyll](https://jekyllrb.com/) site of the YORU family, next to the
[YORU](https://kamikouchi-lab.github.io/YORU_doc/) and
[YORU Tracker](https://kamikouchi-lab.github.io/YORU-Tracker_doc/) documentation.
It keeps Lanyon's layout and is coloured like the application's window: YORU's
navy with YORU-Explain's hot pink (the tokens at the top of `public/css/explain.css`),
dark by default with a light theme.

| Folder / file | Content |
|---|---|
| `index.md` | Home |
| `_guides/` | User guide (sidebar order: `order:` in the front matter) |
| `_methods/` | How it works |
| `_reference/` | Reference |
| `_devnotes/` | Development notes |
| `troubleshooting.md`, `screenshots.md` | Q and A, Screenshots |
| `_data/navigation.yml` | The tab bar and the sidebar groups |
| `_data/ecosystem.yml` | The YORU family (Home, sidebar, footer); keep it in step with YORU-Tracker_doc's |
| `_config.yml` | Versions: `version`, `yoru_requirement`, and `explain_branch` (the branch the install commands clone until the DearPyGui window is merged into YORU-Explain's `main`) |
| `imgs/`, `logos/`, `public/` | Screenshots and figures, logos, favicon, CSS and JavaScript |
| `scripts/` | `make_screenshots.py` (the screenshots in `imgs/`, made with YORU-Explain itself) and `make_logo.py` (the logo and icons, from YORU's logo) |

## Preview locally

GitHub Pages builds the site with the `github-pages` gem (Jekyll 3.10):

```
gem install github-pages webrick
jekyll serve
```

and open <http://127.0.0.1:4000/YORU-Explain_doc/>.

## Publish

`.github/workflows/jekyll-gh-pages.yml` builds and deploys the site on every
push to `main`. In the repository's **Settings → Pages**, set **Source** to
**GitHub Actions**.
