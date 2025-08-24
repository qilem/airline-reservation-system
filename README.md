# Airline Ticket Reservation System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-Flask-green.svg" alt="Flask Framework">
  <img src="https://img.shields.io/badge/Database-MySQL-orange.svg" alt="MySQL Database">
  <img src="https://img.shields.io/badge/License-MIT-lightgrey.svg" alt="License">
</p>

A full-stack airline ticketing platform built with Python, Flask, and MySQL. This system features robust role-based access control, real-time flight management, and detailed analytics, catering to customers, booking agents, and airline staff.

## Table of Contents

- [About The Project](#about-the-project)
- [Key Features](#-key-features)
  - [For Customers](#-for-customers)
  - [For Booking Agents](#-for-booking-agents)
  - [For Airline Staff](#-for-airline-staff)
  - [Public Access](#-public-access)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [License](#license)
- [Contact](#contact)

## About The Project

This project is a multi-user airline reservation system designed to simulate the complex operations of a real-world airline. It provides distinct interfaces and functionalities for different user roles, all managed through a centralized backend and database. The architecture emphasizes security, scalability, and a clear separation of concerns, with parameterized SQL queries to prevent injection attacks and a modular structure for easy maintenance.

## ✨ Key Features

The system is designed with four distinct user roles, each with a tailored set of permissions and features:

### 👤 For Customers
- **Flight Search:** Search for available flights by source, destination, and date.
- **Ticket Purchasing:** Securely book and purchase tickets for selected flights.
- **Booking History:** View a complete history of all past and upcoming flights.
- **📊 Spending Tracker:** Monitor purchase history and view monthly spending reports to manage travel budgets.

### 🧑‍💼 For Booking Agents
- **Book for Customers:** Search and book flights on behalf of registered customers.
- **📈 Commission Dashboard:** Track commission earnings from ticket sales in real-time within a specified date range.
- **Top Customer Analytics:** Identify and view top customers based on the number of tickets purchased or commission generated.

### ✈️ For Airline Staff
- **Complete Flight Management:** Create, update, and manage flight schedules, including changing flight statuses (e.g., delayed, on-time).
- **Fleet & Airport Management:** Add new airplanes and airports to the system to expand the airline's network.
- **User & Permission Control:** Approve new staff/agent accounts and grant specific operational permissions.
- **Comprehensive Reporting:** Generate detailed reports on ticket sales, total revenue, and popular destinations to drive business decisions.




</details>

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

Make sure you have the following installed on your system:
- Python (3.9+ recommended)
- MySQL Server
- Git

### Installation

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/qilem/airline-reservation-system.git]
    cd airline-reservation-system
    ```

2.  **Create and activate a Python virtual environment:**
    ```sh
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Set up the MySQL Database:**
    - Start your MySQL server.
    - Create a new database for the project (e.g., `airline_db`).
    - Import the database schema and initial data from the `air.sql` file:
      ```sh
      mysql -u your_mysql_user -p your_database_name < air.sql
      ```

4.  **Configure Environment Variables:**
    - Open the `config.py` file.
    - Update the database connection settings (username, password, database name) to match your local MySQL setup.

5.  **Run the application:**
    ```sh
    python run.py
    ```
    The application should now be running at `http://127.0.0.1:5000`.


<img width="2480" height="1203" alt="屏幕截图 2025-08-24 090447" src="https://github.com/user-attachments/assets/dc473658-709c-4201-acb3-54a1afd0b1b0" />
<img width="2472" height="1203" alt="屏幕截图 2025-08-24 090945" src="https://github.com/user-attachments/assets/0c41f111-4a2d-41c0-82af-3415d51a5ac6" />
<img width="2471" height="1189" alt="屏幕截图 2025-08-24 092206" src="https://github.com/user-attachments/assets/9fa999ea-b45e-4bf7-8938-a72b729001e1" />
<img width="2477" height="1191" alt="屏幕截图 2025-08-24 092406" src="https://github.com/user-attachments/assets/ed42ec88-faad-4c72-b0bc-261fb563947e" />





