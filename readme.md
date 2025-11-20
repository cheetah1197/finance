# MetricMinder 📊

> **Status:** 🚧 In Active Development / Prototype Phase

MetricMinder is a Python-based web application designed to aggregate, process, and visualize macroeconomic indicators (GDP, Inflation, Trade Data) for over 200 countries. The goal is to simplify economic research by providing a central dashboard for critical data points.

## 🎯 Project Goals
- **Automated Data Collection:** Scraping and cleaning economic data sources.
- **Persistence:** Storing historical data in a structured PostgreSQL database.
- **Visualization:** Rendering interactive charts for comparative economic analysis.
- **Future Transition:** Decoupling Frontend to React.js for enhanced UX.

## 🛠 Tech Stack
- **Backend:** Python 3.11+, FastAPI
- **Database:** PostgreSQL
- **Containerization:** Docker & Docker Compose
- **Frontend:** HTML/CSS (Jinja2 Templates) / JavaScript

## 🚀 Setup (Local Development)
```bash
# Clone the repository
git clone [https://github.com/DEIN_USERNAME/metricminder.git](https://github.com/DEIN_USERNAME/metricminder.git)

# Run with Docker 
docker-compose up --build