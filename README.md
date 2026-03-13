# Expense Tracker (Streamlit)

This project is a simple **expense tracking application** developed using **Python and Streamlit**.
It allows users to record their daily expenses, automatically categorize them using keywords, and store the information in a **SQLite database**. The application provides a simple interface where users can add expenses and keep track of their spending.

---

## Features

### 1. Add and Record Expenses

Users can enter the details of an expense such as **amount, description, and date**.
Once submitted, the expense is stored in the database so it can be accessed later. This helps maintain a record of daily spending.

### 2. Automatic Category Detection

The application uses a **keyword-based categorization system**.
When a user enters an expense description (for example: *Uber*, *Netflix*, *groceries*, etc.), the system checks for certain keywords and automatically assigns a suitable category such as:

* Transport
* Subscriptions
* Groceries
* Salary
* Rent
* Entertainment
* Food

This reduces the need for the user to manually select categories for every expense.

### 3. SQLite Database Storage

All expense records are stored in a **SQLite database (vera.db)**.
Using a database ensures that the data is saved permanently and can be accessed whenever the application is opened again.

### 4. Interactive Streamlit Interface

The application is built using **Streamlit**, which provides a simple and interactive web interface.
Users can interact with the application through their browser without needing to run complex commands or install additional software.

### 5. Organized Expense Records

Expenses entered by the user are organized and displayed clearly within the application.
This makes it easier to review spending and understand where most of the money is being spent.

### 6. Modular Code Structure

The project is structured into separate files to make the code easier to understand and maintain:

* `streamlit_app.py` handles the user interface
* `db.py` manages database operations
* `utils.py` contains helper functions such as keyword-based categorization

This modular approach improves readability and allows easier future development.

---

## Technologies Used

* Python
* Streamlit
* SQLite
* Datetime utilities
* Basic Python data processing

---

## Project Structure

```
expense-tracker/
│
├── streamlit_app.py     # Main application file
├── db.py                # Database functions and queries
├── utils.py             # Helper functions and category mapping
├── vera.db              # SQLite database file
├── requirements.txt     # Required Python packages
└── README.md            # Project documentation
```

---

## Setup Instructions

### 1. Clone the repository

```
git clone https://github.com/yourusername/expense-tracker-streamlit.git
cd expense-tracker-streamlit
```

### 2. Create a virtual environment

```
python -m venv ve
```

Activate it:

Windows

```
ve\Scripts\activate
```

Mac/Linux

```
source ve/bin/activate
```

### 3. Install required packages

```
pip install -r requirements.txt
```

### 4. Run the application

```
streamlit run streamlit_app.py
```

The application will start and open in your browser.

---

## How the Application Works

1. The user enters expense details such as amount, description, and date.
2. The application checks the description for certain keywords to determine the expense category.
3. The expense is stored in the SQLite database.
4. The stored data is displayed in the Streamlit interface for easy tracking.

---

## Team Members

* Aaron Fernandes
* Edwin Pious
* Rugved Hinge
* Vedant Deshmuskh
---

## Possible Improvements

Future versions of the application could include:

* Expense graphs and visualizations
* Monthly expense summaries
* Budget planning features
* Exporting expense reports to CSV or PDF
* User authentication and multiple user accounts

---

This project was developed as a learning exercise to understand **Streamlit applications, database management, and building simple financial tracking tools using Python**.
