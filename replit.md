# MB Print Box Generator

## Overview
A Flask web application with two tools:
1. **Box Generator (Oklejka)** - Generates PDF box/packaging designs with cutting and folding lines
2. **Card Generator (Karty)** - Placeholder for card generation (in development)

Users can switch between tools using a tabbed interface and select their preferred language (PL/EN) with a global language toggle.

## Project Architecture
- **Backend**: Python 3.11 with Flask
- **PDF Generation**: Uses svgwrite to create SVG drawings and cairosvg to convert to PDF
- **Frontend**: Bootstrap 5 with JavaScript for dynamic language switching and tab navigation
- **Port**: 5000

## Key Features
- **Global Language Switcher**: PL/EN toggle at top right that instantly switches all interface labels without page reload
- **Tabbed Interface**: Separate tabs for "BOX (Oklejka)" and "CARD (Karty)" tools
- **Responsive Design**: Clean, mobile-friendly Bootstrap layout
- **Language Persistence**: Selected language is sent with every form submission via hidden input field

## Routes
- `GET/POST /` - Main page with BOX Generator form
- `POST /generate-card` - Card Generator endpoint that generates PDF templates with bleeds and safe areas

## Key Files
- `app.py` - Main Flask application with routes for BOX and CARD generators
- `generator.py` - SVG generation logic for box patterns
- `cards.py` - Card template generator with bleeds and safe areas
- `segments_full.py` - Contains segment definitions for box cutting/folding lines
- `templates/index.html` - Tabbed interface with both BOX and CARD forms, language switcher, JavaScript for dynamic UI
- `templates/*.png, *.jpg` - Logo and image assets

## Dependencies
- flask - Web framework
- svgwrite - SVG creation
- cairosvg - SVG to PDF conversion
- pycairo - Cairo graphics library bindings
- gunicorn - Production WSGI server
- reportlab - PDF generation for card templates

## System Dependencies
- cairo - Required for cairosvg PDF rendering
- pkg-config - Build tool for dependencies

## Running the Application
The Flask App workflow runs `python app.py` which starts the development server on port 5000.

## Deployment
Uses gunicorn as the production WSGI server:
```
gunicorn --bind=0.0.0.0:5000 --reuse-port app:app
```
