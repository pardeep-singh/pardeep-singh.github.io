# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal website for Pardeep Singh, Engineering Lead at Srotas Health. The site is built as a static HTML website hosted on GitHub Pages and showcases professional experience, projects, and personal information.

## Architecture

The website follows a simple static HTML structure:

- **Navigation**: Consistent header navigation across all pages linking to the main sections
- **Main Content**: Each page has a main section with specific content for that page
- **Styling**: Single `style.css` file provides consistent styling across all pages
- **Assets**: Images stored in the `images/` directory

## File Structure

- `index.html` - Home page: short bio, photo, "Lately" list, contact
- `experience.html` - Work history, education and Coursera certificates (work history sourced from the latest CV PDF)
- `projects.html` - Open source contributions, own GitHub projects, Kaggle notebooks/datasets
- `quotes.html` - Favourite quotes (`figure.quote` blocks)
- Blog page removed until there is a first post (old placeholder is in git history)
- `style.css` - Single stylesheet: serif type, one accent colour, dated `.items` lists
- `images/` - Directory containing profile photo and other assets

## Development Notes

- This is a GitHub Pages site, so deployment is automatic when changes are pushed to the main branch
- The site uses semantic HTML5 structure with proper accessibility considerations
- Layout is modelled on nadh.in: one white sheet on a grey page, EB Garamond (Google Fonts), accent `#ff3300`; colours are CSS variables in `:root`
- No build process or package manager is required - direct HTML/CSS/JS editing
- All pages share the same header navigation and footer structure

## Content Management

- Professional experience and skills are maintained in `experience.html`
- Dated lists (experience, projects, "Lately") use `<ul class="items">` with a `.date` column and `.body`
- Header nav and footer links are duplicated in every page; update all pages together