# Streamlit Frontend Component

## Purpose

The Streamlit frontend provides a user-friendly web interface for the NL2SQL system. It allows users to input natural language questions and view the resulting SQL queries and data in an accessible format.

## Functionality

- **User Input**: Provides a clean interface for entering natural language questions
- **Result Display**: Shows generated SQL and query results in a tabular format
- **Settings Management**: Allows configuration of API URL and display options
- **History Tracking**: Maintains a record of recent queries for reference

## Key Features

- Responsive web interface with clean, minimal styling
- SQL visibility toggle for transparency
- CSV export functionality for result data
- Query timing information
- Error handling and display
- Query history with expandable entries

## Interface Components

### Sidebar Settings
- API base URL configuration
- Option to show/hide generated SQL
- Option to enable/disable CSV download
- Help text for API setup

### Main Interface
- Question input field with placeholder examples
- Run button to execute the query
- Result display area with timing information
- Generated SQL code display (when enabled)
- Data table visualization
- CSV download button (when enabled)
- Error display area

### History Section
- Chronological list of recent queries
- Expandable entries showing full details
- Performance timing for each query

## How It Works

1. User enters a natural language question in the input field
2. When Run is clicked, the question is sent to the backend API
3. The frontend displays a loading spinner during processing
4. Results are stored in session state for history tracking
5. Success results show the generated SQL (if enabled) and data table
6. Error results display the error message with details
7. All queries are added to the history section

## User Experience

- Clean, minimal styling without distracting elements
- Responsive layout that works on different screen sizes
- Clear visual hierarchy with section titles
- Performance timing to inform users about query speed
- Download functionality for working with results
- Error messages that help users understand issues

## Technical Implementation

- Uses Streamlit's session state for query history
- Makes HTTP requests to the FastAPI backend
- Converts API responses to pandas DataFrames for display
- Implements proper error handling for network requests
- Uses custom CSS for consistent styling