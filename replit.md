# MB Print Box Generator

## Overview
A Flask web application that generates PDF box/packaging designs. Users input box dimensions (X, Y, Z) and the application generates a printable PDF with cutting and folding lines for the box pattern.

## Project Architecture
- **Backend**: Python 3.11 with Flask
- **PDF Generation**: Uses svgwrite to create SVG drawings and cairosvg to convert to PDF
- **Port**: 5000

## Key Files
- `app.py` - Main Flask application with routes
- `generator.py` - SVG generation logic for box patterns
- `segments_full.py` - Contains segment definitions for box cutting/folding lines
- `templates/index.html` - Frontend form for inputting box dimensions
- `templates/*.png, *.jpg` - Logo and image assets

## Dependencies
- flask - Web framework
- svgwrite - SVG creation
- cairosvg - SVG to PDF conversion
- pycairo - Cairo graphics library bindings
- gunicorn - Production WSGI server

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
