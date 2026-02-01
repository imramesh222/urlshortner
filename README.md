# URL Shortener 🔗

A full-featured URL shortening service built with Django that allows users to create, manage, and track shortened URLs with comprehensive analytics.

## ✨ Features

### Core Features
- **URL Shortening**: Convert long URLs into short, manageable links
- **Custom Short Codes**: Create personalized short codes for your URLs
- **QR Code Generation**: Generate QR codes for easy sharing
- **URL Expiration**: Set expiration dates for temporary links
- **One-Time Links**: Create links that deactivate after first use
- **Password Protection**: Secure your links with passwords

### User Management
- **User Authentication**: Complete registration and login system
- **User Dashboard**: Centralized view of all your shortened URLs
- **Profile Management**: Update account settings and preferences
- **Email Verification**: Secure account verification system
- **Password Reset**: Easy password recovery

### Analytics & Tracking
- **Click Analytics**: Detailed click tracking and statistics
- **Visitor Insights**: Track unique visitors and repeat visits
- **Referrer Tracking**: See where your traffic is coming from
- **Geographic Data**: Track visitor locations (with GeoIP)
- **Time-based Analytics**: View clicks over time with charts
- **Export Data**: Export analytics to CSV, JSON, or Excel

### API
- **RESTful API**: Full API for programmatic access
- **API Authentication**: Secure token-based authentication
- **API Documentation**: Complete API endpoint documentation

## 🛠️ Tech Stack

- **Backend**: Django 4.2.7
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Authentication**: Django Allauth
- **Forms**: Django Crispy Forms with Bootstrap 5
- **API**: Django REST Framework
- **Additional**: django-widget-tweaks, python-dotenv

## 📋 Prerequisites

- Python 3.13 or higher
- pip (Python package installer)
- Virtual environment (recommended)
- Git

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/imramesh222/urlshortner.git
cd urlshortner
```

### 2. Create and activate a virtual environment
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root directory:
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
BASE_URL=http://localhost:8000
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Create a superuser
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```

### 8. Access the application
- **Main site**: http://127.0.0.1:8000/
- **Admin interface**: http://127.0.0.1:8000/admin/
- **API endpoints**: http://127.0.0.1:8000/api/

## 📁 Project Structure

```
urlshortner/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
├── db.sqlite3
│
├── shortener/                  # Main URL shortener app
│   ├── migrations/
│   ├── templates/
│   │   ├── base.html
│   │   └── shortener/
│   │       ├── home.html
│   │       ├── dashboard.html
│   │       ├── analytics.html
│   │       ├── url_list.html
│   │       └── ...
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── shortener_filters.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── models.py              # URL and Click models
│   ├── views.py               # Main views
│   ├── urls.py                # URL routing
│   ├── forms.py               # Forms
│   ├── utils.py               # Utility functions
│   ├── admin.py               # Admin configuration
│   ├── context_processors.py # Template context processors
│   └── serializers.py         # API serializers
│
├── accounts/                   # User authentication app
│   ├── migrations/
│   ├── templates/
│   │   └── accounts/
│   │       ├── login.html
│   │       ├── signup.html
│   │       ├── profile.html
│   │       ├── account_settings.html
│   │       └── ...
│   ├── models.py              # Custom User model
│   ├── views.py               # Auth views
│   ├── forms.py               # Auth forms
│   ├── urls.py                # Auth routing
│   └── tokens.py              # Token generation
│
├── templates/                  # Global templates
│   └── base.html
│
└── urlshortener/              # Project settings
    ├── __init__.py
    ├── settings.py            # Django settings
    ├── urls.py                # Main URL configuration
    ├── wsgi.py
    └── asgi.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base URL for shortened links
BASE_URL=http://localhost:8000

# Database (optional - defaults to SQLite)
# DATABASE_URL=postgresql://user:password@localhost/dbname

# Email Settings (optional)
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-password
# EMAIL_USE_TLS=True
```

## 📖 Usage

### Creating a Short URL

1. Navigate to the home page
2. Paste your long URL
3. (Optional) Customize the short code
4. (Optional) Set advanced options:
   - Expiration date
   - Password protection
   - One-time use
5. Click "Shorten"

### Viewing Analytics

1. Go to your dashboard
2. Click on any shortened URL
3. View detailed analytics including:
   - Total clicks
   - Unique visitors
   - Click timeline
   - Referrer sources
   - Geographic distribution

### Using the API

```python
import requests

# Create a short URL
response = requests.post(
    'http://localhost:8000/api/urls/',
    headers={'Authorization': 'Token your-api-token'},
    json={'original_url': 'https://example.com'}
)

# Get URL details
response = requests.get(
    'http://localhost:8000/api/urls/abc123/',
    headers={'Authorization': 'Token your-api-token'}
)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Ramesh Rawat**
- GitHub: [@imramesh222](https://github.com/imramesh222)

## 🙏 Acknowledgments

- Django framework and community
- Bootstrap for the UI components
- All contributors and users of this project

## 📧 Support

For support, email your-email@example.com or open an issue in the GitHub repository.
