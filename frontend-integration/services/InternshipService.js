/**
 * Internship API Service
 * Handles all API calls related to internship management
 */

import axios from 'axios';

// API Base URL - configure via environment variable
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Get authentication token from localStorage
 */
const getAuthToken = () => {
  return localStorage.getItem('token') || '';
};

/**
 * Common axios config with auth headers
 */
const getAxiosConfig = () => ({
  headers: {
    'Authorization': `Bearer ${getAuthToken()}`,
    'Content-Type': 'application/json'
  }
});

/**
 * Internship API Service
 */
const InternshipService = {
  /**
   * Extract skills from job description using AI
   * @param {string} jobDescription - The job description text
   * @returns {Promise<{required_skills: string[], preferred_skills: string[]}>}
   */
  extractSkills: async (jobDescription) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/internship/extract-skills`,
        { job_description: jobDescription },
        getAxiosConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error extracting skills:', error);
      throw error;
    }
  },

  /**
   * Create a new internship posting
   * @param {Object} internshipData - Internship details
   * @returns {Promise<Object>} Created internship
   */
  createInternship: async (internshipData) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/internship/post`,
        internshipData,
        getAxiosConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error creating internship:', error);
      throw error;
    }
  },

  /**
   * Update an existing internship
   * @param {number} internshipId - ID of the internship
   * @param {Object} internshipData - Updated internship details
   * @returns {Promise<Object>} Updated internship
   */
  updateInternship: async (internshipId, internshipData) => {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/internship/${internshipId}`,
        internshipData,
        getAxiosConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error updating internship:', error);
      throw error;
    }
  },

  /**
   * Get all active internships
   * @param {number} skip - Number of records to skip (pagination)
   * @param {number} limit - Maximum number of records to return
   * @returns {Promise<Array>} List of internships
   */
  getInternships: async (skip = 0, limit = 50) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/internship/list?skip=${skip}&limit=${limit}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching internships:', error);
      throw error;
    }
  },

  /**
   * Get internship by ID
   * @param {number} internshipId - ID of the internship
   * @returns {Promise<Object>} Internship details
   */
  getInternshipById: async (internshipId) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/internship/${internshipId}`,
        getAxiosConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching internship:', error);
      throw error;
    }
  },

  /**
   * Get internships posted by current company
   * @returns {Promise<Array>} List of company's internships
   */
  getMyInternships: async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/internship/my-posts`,
        getAxiosConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching my internships:', error);
      throw error;
    }
  },

  /**
   * Delete/deactivate an internship
   * @param {number} internshipId - ID of the internship
   * @returns {Promise<void>}
   */
  deleteInternship: async (internshipId) => {
    try {
      await axios.delete(
        `${API_BASE_URL}/internship/${internshipId}`,
        getAxiosConfig()
      );
    } catch (error) {
      console.error('Error deleting internship:', error);
      throw error;
    }
  },

  /**
   * Get AI-powered internship recommendations (for students)
   * @param {number} topK - Number of recommendations to return
   * @returns {Promise<Array>} List of recommended internships with match scores
   */
  getRecommendations: async (topK = 10) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/internship/match?top_k=${topK}`,
        getAxiosConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      throw error;
    }
  }
};

export default InternshipService;
