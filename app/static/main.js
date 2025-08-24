/* static/css/style.css */
/* General Styles */
body {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

main {
    flex: 1;
}

/* Navigation */
.navbar-brand {
    font-weight: 600;
}

.nav-link {
    font-weight: 500;
}

/* Cards */
.card {
    transition: transform 0.2s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card:hover {
    transform: translateY(-2px);
}

.feature-card {
    border: none;
    border-radius: 10px;
    padding: 1.5rem;
}

/* Forms */
.form-control:focus {
    box-shadow: 0 0 0 0.2rem rgba(0,123,255,0.25);
}

.search-form {
    background: rgba(255,255,255,0.9);
    border-radius: 10px;
    padding: 20px;
}

/* Tables */
.table-responsive {
    margin: 0;
    padding: 0;
    width: 100%;
    overflow-x: auto;
}

.table th {
    background-color: #f8f9fa;
    font-weight: 600;
}

/* Status Badges */
.badge {
    padding: 0.5em 1em;
}

.status-badge-ontime {
    background-color: #28a745;
}

.status-badge-delayed {
    background-color: #ffc107;
}

.status-badge-cancelled {
    background-color: #dc3545;
}

/* Dashboard Cards */
.dashboard-card {
    border-radius: 10px;
    margin-bottom: 20px;
}

.dashboard-card .card-header {
    border-radius: 10px 10px 0 0;
}

/* Charts */
.chart-container {
    position: relative;
    margin: auto;
    height: 300px;
    width: 100%;
}

/* Autocomplete Styling */
.ui-autocomplete {
    max-height: 200px;
    overflow-y: auto;
    overflow-x: hidden;
    z-index: 9999;
}

.ui-autocomplete .ui-menu-item {
    padding: 8px 12px;
    border-bottom: 1px solid #eee;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
    .search-form {
        padding: 15px;
    }

    .card-body {
        padding: 1rem;
    }
}

/* Print Styles */
@media print {
    .no-print {
        display: none;
    }

    .card {
        box-shadow: none;
        border: 1px solid #ddd;
    }
}