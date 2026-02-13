# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal GitHub Pages site (jimg72.github.io) serving as a blog, sports card collection tracker (TCDB.com, eBay, COMC), and personal start page.

## Build & Development Commands

```bash
bundle install              # Install dependencies
bundle exec jekyll serve    # Local dev server at http://127.0.0.1:4000
bundle exec jekyll build    # Build static site to _site/
```

Deployed automatically by GitHub Pages on push to `master`.

## Tech Stack

- **Static site generator**: Jekyll with Minima theme (remote_theme: jekyll/minima@v2.5.2)
- **Data**: YAML files in `_data/` drive templated pages via Liquid
- **Styling**: Bootstrap CSS with custom overrides; automatic dark mode (7pm-7am) via inline JS in layouts
- **Layouts**: `bootstrap_grid1.html` and `bootstrap_grid2.html` are standalone Bootstrap layouts (no Minima inheritance) used by data-driven pages; blog posts use Minima's default layout

## Architecture

Pages like `baseball.html`, `football.html`, `ebay.html`, `search.html`, and `start.html` are **data-driven**: they iterate over YAML files in `_data/` to render link grids using Bootstrap card layouts. To add/modify links, edit the corresponding YAML file rather than the HTML.

Key data file mappings:
- `baseball.html` → `baseball1.yaml`, `baseball2.yaml`
- `baseball_rebel_pros.html` → `baseball-pros.yaml`, `baseball-minors.yaml`, `baseball-released.yaml`, `baseball-retired.yaml`
- `football.html` → `football1.yaml`, `football2.yaml`
- `ebay.html` → `ebay.yaml`
- `search.html` → `search.yaml`
- `start.html` → `bookmarks.yaml`, `football1.yaml`, `baseball1.yaml`

Blog posts go in `_posts/` using standard Jekyll front matter and the Minima theme layout.

## Conventions

- YAML data files use the `.yaml` extension
- `_includes/custom-head.html` injects into Minima's `<head>` for blog pages
- `assets/images/bb/` contains headshots for the baseball_rebel_pros page
