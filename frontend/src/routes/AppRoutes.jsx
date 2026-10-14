import { Routes, Route, Navigate } from "react-router-dom";
import Login from "../pages/auth/Login";
import Register from "../pages/auth/Register";
import StudentDashboard from "../pages/student/StudentDashboard";
import SavedItems from "../pages/student/SavedItems";
import AlumniDashboard from "../pages/alumni/AlumniDashboard";
import SubmitExperience from "../pages/alumni/SubmitExperience";
import MyExperiences from "../pages/alumni/MyExperiences";
import EditExperience from "../pages/alumni/EditExperience";
import AdminDashboard from "../pages/admin/AdminDashboard";
import ManageCompanies from "../pages/admin/ManageCompanies";
import ApproveExperiences from "../pages/admin/ApproveExperiences";
import Reports from "../pages/admin/Reports";
import Suggestions from "../pages/admin/Suggestions";
import ManageUsers from "../pages/admin/ManageUsers";
import Account from "../pages/Account";
import Statistics from "../pages/admin/Statistics";
import CompanyList from "../pages/CompanyList";
import CompanyPage from "../pages/CompanyPage";
import ExperienceDetail from "../pages/ExperienceDetail";
import SearchExperiences from "../pages/SearchExperiences";
import QuestionRepository from "../pages/QuestionRepository";
import ProtectedRoute from "./ProtectedRoute";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Any logged-in user (student/alumni/admin) can browse companies and experiences */}
      <Route path="/companies" element={<ProtectedRoute><CompanyList /></ProtectedRoute>} />
      <Route path="/companies/:id" element={<ProtectedRoute><CompanyPage /></ProtectedRoute>} />
      <Route path="/experiences/:id" element={<ProtectedRoute><ExperienceDetail /></ProtectedRoute>} />
      <Route path="/search" element={<ProtectedRoute><SearchExperiences /></ProtectedRoute>} />
      <Route path="/questions" element={<ProtectedRoute><QuestionRepository /></ProtectedRoute>} />

      <Route path="/account" element={<ProtectedRoute allowedRoles={["student", "alumni"]}><Account /></ProtectedRoute>} />

      <Route path="/student" element={<ProtectedRoute allowedRoles={["student"]}><StudentDashboard /></ProtectedRoute>} />
      <Route path="/student/saved" element={<ProtectedRoute allowedRoles={["student"]}><SavedItems /></ProtectedRoute>} />

      <Route path="/alumni" element={<ProtectedRoute allowedRoles={["alumni"]}><AlumniDashboard /></ProtectedRoute>} />
      <Route path="/alumni/submit-experience" element={<ProtectedRoute allowedRoles={["alumni"]}><SubmitExperience /></ProtectedRoute>} />
      <Route path="/alumni/my-experiences" element={<ProtectedRoute allowedRoles={["alumni"]}><MyExperiences /></ProtectedRoute>} />
      <Route path="/alumni/edit-experience/:id" element={<ProtectedRoute allowedRoles={["alumni"]}><EditExperience /></ProtectedRoute>} />

      <Route path="/admin" element={<ProtectedRoute allowedRoles={["admin"]}><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/companies" element={<ProtectedRoute allowedRoles={["admin"]}><ManageCompanies /></ProtectedRoute>} />
      <Route path="/admin/experiences" element={<ProtectedRoute allowedRoles={["admin"]}><ApproveExperiences /></ProtectedRoute>} />
      <Route path="/admin/reports" element={<ProtectedRoute allowedRoles={["admin"]}><Reports /></ProtectedRoute>} />
      <Route path="/admin/suggestions" element={<ProtectedRoute allowedRoles={["admin"]}><Suggestions /></ProtectedRoute>} />
      <Route path="/admin/users" element={<ProtectedRoute allowedRoles={["admin"]}><ManageUsers /></ProtectedRoute>} />
      <Route path="/admin/statistics" element={<ProtectedRoute allowedRoles={["admin"]}><Statistics /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
