# Student Analysis System for Chexam

This document provides information about the Student Analysis System implemented in the Chexam application.

## Overview

The Student Analysis System allows teachers to:

1. Manage student records (add, view, delete)
2. Generate random test data for demonstration purposes
3. Analyze individual student performance against answer keys
4. View class-wide analysis and statistics

## Features

### Student Management
- Add new students with unique names
- View a list of all students
- Delete students
- Initialize example data with 30 random students

### Student Analysis
- Compare student answers with the correct answer key
- Calculate scores and percentages
- Identify correctly and incorrectly answered questions
- Generate insights about student strengths and weaknesses
- Provide personalized suggestions for improvement

### Class Analysis
- Calculate class average score and passing rate
- Identify highest and lowest scores
- Determine most frequently missed questions
- Identify best understood questions
- Generate insights about class strengths and weaknesses
- Provide teaching suggestions based on overall performance

## How to Use

### Student Management Screen
1. From the home screen, click "Student Management"
2. To add a student: Enter a name in the text field and click "Add Student"
3. To select a student: Click on a student name in the list
4. To delete a student: Select a student and click "Delete Selected Student"
5. To initialize example data: Click "Initialize 30 Example Students"

### Analyzing a Student
1. In the Student Management screen, select a student
2. Select an answer key (if multiple are available)
3. Click "Analyze Selected Student"
4. View the analysis results on the right side of the screen

### Class Analysis Screen
1. From the home screen, click "Class Analysis"
2. Select an answer key (if multiple are available)
3. Click "Analyze All Students"
4. View the class-wide analysis results

## Implementation Notes

The analysis system uses a combination of:

1. Gemini API (when available) for AI-powered analysis
2. A fallback mock analysis system when the Gemini API is unavailable

The mock analysis system provides similar functionality to the Gemini API, including:
- Score calculation
- Identification of strengths and weaknesses
- Generation of suggestions
- Class-wide statistical analysis

## Database Structure

The system uses SQLite with the following tables:

- `students`: Stores student information
- `student_answers`: Stores student answers for specific answer keys
- `analysis_results`: Stores analysis results for each student

## Future Improvements

Potential future enhancements:
- Export analysis results to PDF or CSV
- Track student progress over time
- Generate visual charts and graphs
- Compare performance across different tests
- Group students by performance level
