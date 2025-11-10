import React, { useState } from 'react';
import axios from 'axios';
import './CreateInternshipForm.css';

const CreateInternshipForm = () => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    required_skills: [],
    preferred_skills: [],
    location: '',
    duration: '',
    stipend: '',
    min_experience: 0,
    max_experience: 5,
    required_education: ''
  });

  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMethod, setUploadMethod] = useState('document'); // 'document' or 'manual'
  const [newSkill, setNewSkill] = useState({ required: '', preferred: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Get API base URL from environment or use default
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Get auth token from localStorage
  const getAuthToken = () => localStorage.getItem('token');

  /**
   * Handle document upload and parse internship details
   */
  const handleDocumentUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['.pdf', '.docx', '.doc', '.txt'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!allowedTypes.includes(fileExt)) {
      setError('Invalid file type. Please upload PDF, DOCX, DOC, or TXT files.');
      setTimeout(() => setError(''), 5000);
      return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setError('File is too large. Maximum size is 10MB.');
      setTimeout(() => setError(''), 5000);
      return;
    }

    setUploading(true);
    setError('');

    try {
      const formDataUpload = new FormData();
      formDataUpload.append('file', file);

      const response = await axios.post(
        `${API_BASE_URL}/internship/parse-document`,
        formDataUpload,
        {
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      const extractedData = response.data;

      // Pre-fill form with extracted data
      setFormData({
        title: extractedData.title || '',
        description: extractedData.description || '',
        required_skills: extractedData.required_skills || [],
        preferred_skills: extractedData.preferred_skills || [],
        location: extractedData.location || '',
        duration: extractedData.duration || '',
        stipend: extractedData.stipend || '',
        min_experience: extractedData.min_experience || 0,
        max_experience: extractedData.max_experience || 5,
        required_education: extractedData.required_education || ''
      });

      setSuccess('✅ Document parsed successfully! Please review and edit the details below.');
      setTimeout(() => setSuccess(''), 5000);

    } catch (err) {
      console.error('Error uploading document:', err);
      setError(
        err.response?.data?.detail || 
        'Failed to parse document. Please try manual entry or try again.'
      );
    } finally {
      setUploading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  /**
   * Extract skills from job description using AI
   */
  const handleExtractSkills = async () => {
    if (!formData.description || formData.description.length < 50) {
      setError('Please write a job description of at least 50 characters before extracting skills.');
      return;
    }

    setExtracting(true);
    setError('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/internship/extract-skills`,
        { job_description: formData.description },
        {
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setFormData({
        ...formData,
        required_skills: response.data.required_skills || [],
        preferred_skills: response.data.preferred_skills || []
      });

      setSuccess('Skills extracted successfully! You can now edit them.');
      setTimeout(() => setSuccess(''), 3000);

    } catch (err) {
      console.error('Error extracting skills:', err);
      setError(
        err.response?.data?.detail || 
        'Failed to extract skills. Please try again or add skills manually.'
      );
    } finally {
      setExtracting(false);
    }
  };

  /**
   * Add a skill to required or preferred list
   */
  const addSkill = (type) => {
    const skillValue = newSkill[type].trim();
    if (!skillValue) return;

    const skillList = type === 'required' ? 'required_skills' : 'preferred_skills';
    
    // Check if skill already exists (case-insensitive)
    const exists = formData[skillList].some(
      skill => skill.toLowerCase() === skillValue.toLowerCase()
    );

    if (exists) {
      setError(`Skill "${skillValue}" already exists in ${type} skills.`);
      setTimeout(() => setError(''), 3000);
      return;
    }

    setFormData({
      ...formData,
      [skillList]: [...formData[skillList], skillValue]
    });

    setNewSkill({ ...newSkill, [type]: '' });
  };

  /**
   * Remove a skill from required or preferred list
   */
  const removeSkill = (type, index) => {
    const skillList = type === 'required' ? 'required_skills' : 'preferred_skills';
    setFormData({
      ...formData,
      [skillList]: formData[skillList].filter((_, i) => i !== index)
    });
  };

  /**
   * Move skill from one category to another
   */
  const moveSkill = (skill, fromType) => {
    const fromList = fromType === 'required' ? 'required_skills' : 'preferred_skills';
    const toList = fromType === 'required' ? 'preferred_skills' : 'required_skills';

    // Remove from source
    const updatedFromList = formData[fromList].filter(s => s !== skill);

    // Add to destination (if not already there)
    const updatedToList = formData[toList].includes(skill) 
      ? formData[toList] 
      : [...formData[toList], skill];

    setFormData({
      ...formData,
      [fromList]: updatedFromList,
      [toList]: updatedToList
    });
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/internship/post`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setSuccess('Internship posted successfully!');
      
      // Reset form after 2 seconds
      setTimeout(() => {
        setFormData({
          title: '',
          description: '',
          required_skills: [],
          preferred_skills: [],
          location: '',
          duration: '',
          stipend: '',
          min_experience: 0,
          max_experience: 5,
          required_education: ''
        });
        setSuccess('');
      }, 2000);

    } catch (err) {
      console.error('Error posting internship:', err);
      setError(
        err.response?.data?.detail || 
        'Failed to post internship. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle key press for adding skills
   */
  const handleSkillKeyPress = (e, type) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addSkill(type);
    }
  };

  return (
    <div className="create-internship-form">
      <h2>Create Internship Posting</h2>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* Upload Method Toggle */}
      <div className="upload-method-selector">
        <h3>Choose Input Method:</h3>
        <div className="method-buttons">
          <button
            type="button"
            className={`method-btn ${uploadMethod === 'document' ? 'active' : ''}`}
            onClick={() => setUploadMethod('document')}
          >
            <span className="method-icon">📄</span>
            <span className="method-text">Upload Document</span>
            <small>AI auto-fills all details</small>
          </button>
          <button
            type="button"
            className={`method-btn ${uploadMethod === 'manual' ? 'active' : ''}`}
            onClick={() => setUploadMethod('manual')}
          >
            <span className="method-icon">✍️</span>
            <span className="method-text">Enter Manually</span>
            <small>Fill form by hand</small>
          </button>
        </div>
      </div>

      {/* Document Upload Section */}
      {uploadMethod === 'document' && (
        <div className="document-upload-section">
          <div className="upload-area">
            <h3>📄 Upload Job Description</h3>
            <p className="upload-description">
              Upload a PDF, DOCX, DOC, or TXT file containing the job description. 
              Our AI will automatically extract all details including title, description, 
              skills, location, duration, and compensation.
            </p>
            <div className="file-input-wrapper">
              <input
                type="file"
                id="document-upload"
                accept=".pdf,.docx,.doc,.txt"
                onChange={handleDocumentUpload}
                disabled={uploading}
                className="file-input"
              />
              <label htmlFor="document-upload" className={`file-input-label ${uploading ? 'uploading' : ''}`}>
                {uploading ? (
                  <>
                    <span className="spinner"></span>
                    <span>Parsing document...</span>
                  </>
                ) : (
                  <>
                    <span className="upload-icon">⬆️</span>
                    <span>Click to upload or drag & drop</span>
                    <small>PDF, DOCX, DOC, TXT (Max 10MB)</small>
                  </>
                )}
              </label>
            </div>
            {uploading && (
              <p className="upload-status">
                🔄 Uploading and parsing document... This may take a few seconds.
              </p>
            )}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Title Field */}
        <div className="form-group">
          <label htmlFor="title">Internship Title *</label>
          <input
            type="text"
            id="title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="e.g., Full Stack Developer Intern"
            required
          />
        </div>

        {/* Job Description Field */}
        <div className="form-group">
          <label htmlFor="description">Job Description *</label>
          <textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Enter detailed job description including responsibilities, requirements, and qualifications..."
            rows={10}
            required
          />
          <small className="form-hint">
            {formData.description.length} characters 
            {formData.description.length < 50 && ` (minimum 50 required for skill extraction)`}
          </small>
        </div>

        {/* Extract Skills Button */}
        <div className="form-group">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleExtractSkills}
            disabled={extracting || formData.description.length < 50}
          >
            {extracting ? (
              <>
                <span className="spinner"></span>
                Extracting Skills...
              </>
            ) : (
              <>
                🔍 Extract Skills from Description
              </>
            )}
          </button>
          <small className="form-hint">
            AI will automatically categorize skills into required and preferred
          </small>
        </div>

        {/* Required Skills Section */}
        <div className="form-group skills-section">
          <label>
            <span className="required-badge">✅</span> Required Skills *
          </label>
          <div className="skills-container">
            {formData.required_skills.map((skill, index) => (
              <span key={index} className="skill-tag required">
                {skill}
                <button
                  type="button"
                  className="skill-remove"
                  onClick={() => removeSkill('required', index)}
                  title="Remove skill"
                >
                  ×
                </button>
                <button
                  type="button"
                  className="skill-move"
                  onClick={() => moveSkill(skill, 'required')}
                  title="Move to preferred"
                >
                  ⇩
                </button>
              </span>
            ))}
          </div>
          <div className="skill-input-group">
            <input
              type="text"
              value={newSkill.required}
              onChange={(e) => setNewSkill({ ...newSkill, required: e.target.value })}
              onKeyPress={(e) => handleSkillKeyPress(e, 'required')}
              placeholder="Add required skill (press Enter)"
            />
            <button
              type="button"
              className="btn btn-small"
              onClick={() => addSkill('required')}
            >
              + Add
            </button>
          </div>
          <small className="form-hint">
            {formData.required_skills.length} required skills added
          </small>
        </div>

        {/* Preferred Skills Section */}
        <div className="form-group skills-section">
          <label>
            <span className="preferred-badge">⭐</span> Preferred Skills
          </label>
          <div className="skills-container">
            {formData.preferred_skills.map((skill, index) => (
              <span key={index} className="skill-tag preferred">
                {skill}
                <button
                  type="button"
                  className="skill-remove"
                  onClick={() => removeSkill('preferred', index)}
                  title="Remove skill"
                >
                  ×
                </button>
                <button
                  type="button"
                  className="skill-move"
                  onClick={() => moveSkill(skill, 'preferred')}
                  title="Move to required"
                >
                  ⇧
                </button>
              </span>
            ))}
          </div>
          <div className="skill-input-group">
            <input
              type="text"
              value={newSkill.preferred}
              onChange={(e) => setNewSkill({ ...newSkill, preferred: e.target.value })}
              onKeyPress={(e) => handleSkillKeyPress(e, 'preferred')}
              placeholder="Add preferred skill (press Enter)"
            />
            <button
              type="button"
              className="btn btn-small"
              onClick={() => addSkill('preferred')}
            >
              + Add
            </button>
          </div>
          <small className="form-hint">
            {formData.preferred_skills.length} preferred skills added
          </small>
        </div>

        {/* Location Field */}
        <div className="form-group">
          <label htmlFor="location">Location</label>
          <input
            type="text"
            id="location"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            placeholder="e.g., Remote, San Francisco, CA, or Hybrid"
          />
        </div>

        {/* Duration Field */}
        <div className="form-group">
          <label htmlFor="duration">Duration</label>
          <input
            type="text"
            id="duration"
            value={formData.duration}
            onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
            placeholder="e.g., 3 months, 6 months"
          />
        </div>

        {/* Stipend Field */}
        <div className="form-group">
          <label htmlFor="stipend">Stipend</label>
          <input
            type="text"
            id="stipend"
            value={formData.stipend}
            onChange={(e) => setFormData({ ...formData, stipend: e.target.value })}
            placeholder="e.g., $1500/month, Unpaid, Negotiable"
          />
        </div>

        {/* Experience Range Fields */}
        <div className="form-group-row">
          <div className="form-group">
            <label htmlFor="min_experience">Min Experience (years)</label>
            <input
              type="number"
              id="min_experience"
              step="0.5"
              min="0"
              value={formData.min_experience}
              onChange={(e) => setFormData({ ...formData, min_experience: parseFloat(e.target.value) || 0 })}
              placeholder="0"
            />
          </div>
          <div className="form-group">
            <label htmlFor="max_experience">Max Experience (years)</label>
            <input
              type="number"
              id="max_experience"
              step="0.5"
              min="0"
              value={formData.max_experience}
              onChange={(e) => setFormData({ ...formData, max_experience: parseFloat(e.target.value) || 5 })}
              placeholder="5"
            />
          </div>
        </div>

        {/* Required Education Field */}
        <div className="form-group">
          <label htmlFor="required_education">Required Education</label>
          <input
            type="text"
            id="required_education"
            value={formData.required_education}
            onChange={(e) => setFormData({ ...formData, required_education: e.target.value })}
            placeholder="e.g., Currently pursuing Bachelor's in Computer Science"
          />
          <small className="form-hint">
            Specify education level, degree, or field of study requirements
          </small>
        </div>

        {/* Submit Buttons */}
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-cancel"
            onClick={() => window.history.back()}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Posting...
              </>
            ) : (
              'Post Internship'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateInternshipForm;
