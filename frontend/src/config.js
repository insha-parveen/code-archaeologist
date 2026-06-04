// Central API configuration
// In development: points to local backend
// In production: reads from environment variable
// Set VITE_API_BASE in your .env file to override

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000"

export default API_BASE
