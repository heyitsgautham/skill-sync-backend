# SkillSync Backend - Copilot Instructions

## Project Overview
SkillSync is an intelligent internship matching platform that connects students with companies using AI-powered recommendations. The system uses RAG (Retrieval-Augmented Generation) with LLM to analyze student resumes and internship postings for optimal matching.

## Tech Stack
- **Backend Framework**: Node.js/Express 
- **Database**: PostgreSQL/MongoDB
- **AI/ML**: RAG system with LLM integration for intelligent matching
- **Authentication**: JWT-based auth with role-based access control

## Key Features
- **Student Management**: Profile creation, resume uploads, skill tracking, application management
- **Company Management**: Internship posting, student recommendations, applicant shortlisting
- **Admin Dashboard**: User management, analytics, RAG system controls
- **AI Matching Engine**: Resume parsing, skill extraction, semantic matching using RAG

## User Roles
1. **Student**: Register, build profile, apply for internships, receive AI recommendations
2. **Company**: Post internships, view matched candidates, manage applications
3. **Admin**: User management, system oversight, analytics, RAG maintenance

## Code Guidelines
- Follow RESTful API conventions
- Implement proper error handling and validation
- Use async/await for asynchronous operations
- Maintain clear separation of concerns (routes, controllers, services, models)
- Document API endpoints with clear comments
- Implement proper authentication and authorization middleware
- Write clean, maintainable code with meaningful variable names

## API Structure
- `/api/auth` - Authentication endpoints
- `/api/students` - Student profile and application management
- `/api/companies` - Company and internship management
- `/api/admin` - Admin operations and analytics
- `/api/recommendations` - AI-powered matching endpoints

## Security
- Validate all user inputs
- Implement rate limiting
- Secure file uploads (resume handling)
- Use environment variables for sensitive data
- Implement RBAC for all protected routes

## General Rules
- Ensure code is modular, reusable and simple to understand 
- Write unit tests for critical components
- Dont create any .md files unless specifically instructed
- Never start an server or kill an server, I will handle that
- Never change the application ports or database configurations
- Create all scripts inside the scripts/ directory
- Create all test files inside the tests/ directory
- Never push anything directly to main branch, always create a new branch for changes and raise a PR