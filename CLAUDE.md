# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal website for Pardeep Singh, a Lead Machine Learning Engineer at Fairmatic. The site is built as a static HTML website hosted on GitHub Pages and showcases professional experience, projects, and personal information.

## Architecture

The website follows a simple static HTML structure:

- **Navigation**: Consistent header navigation across all pages linking to the main sections
- **Main Content**: Each page has a main section with specific content for that page
- **Styling**: Single `style.css` file provides consistent styling across all pages
- **Assets**: Images stored in the `images/` directory

## File Structure

- `index.html` - Home page with complete professional profile, experience, education, and skills
- `projects.html` - Projects page with tables for Kaggle and GitHub projects (placeholder content)
- `quotes.html` - Quotes page (under construction)
- `resources.html` - Resources page (under construction)
- `blog.html` - Blog page (under construction)
- `style.css` - Main stylesheet with responsive design patterns
- `images/` - Directory containing profile photo and other assets

## Development Notes

- This is a GitHub Pages site, so deployment is automatic when changes are pushed to the main branch
- The site uses semantic HTML5 structure with proper accessibility considerations
- CSS uses flexbox for layout (particularly visible in the home section)
- No build process or package manager is required - direct HTML/CSS/JS editing
- All pages share the same header navigation and footer structure

## Content Management

- Professional experience and skills are maintained in `index.html`
- Project pages use table structure for organized display
- Several pages are marked as "under construction" and need content
- Contact information and social links are in the footer of the home page