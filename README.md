# TutorFinder

TutorFinder is a Django web application that connects students and tutors for structured 1:1 learning. Students can discover tutors by subject, send connection requests, and manage sessions. Tutors can manage profiles, availability, requests, and session approvals.

## Features

- Role-based authentication (`student` and `tutor`)
- Student and tutor registration flows
- Tutor discovery by subject
- Connection request workflow
- Session request, approval, and completion tracking
- Tutor rating and feedback after sessions
- Student and tutor dashboards
- Profile management for both user roles

## Tech Stack

- Python 3.13
- Django 5.x
- SQLite (default database)
- Bootstrap + Django templates

## Project Structure

- `manage.py` - Django management entry point
- `tutorfinder/settings.py` - project settings
- `tutorfinder/urls.py` - root URL configuration
- `users/` - core app (models, views, forms, URLs)
- `templates/` - HTML templates
- `static/` - static assets
- `media/` - uploaded profile images

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ad4rsh432/Tutor_finder_.git
cd Tutor_finder_/tutorfinder



