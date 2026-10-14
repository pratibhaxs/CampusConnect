import axiosClient from "./axiosClient";

export const fetchUsers = (params) => axiosClient.get("/admin/users", { params });
export const deleteUser = (id) => axiosClient.delete(`/admin/users/${id}`);

export const fetchSuggestions = () => axiosClient.get("/admin/suggestions");
export const fetchDuplicates = () => axiosClient.get("/admin/duplicates");
export const approveCompany = (id) => axiosClient.post(`/admin/companies/${id}/approve`);
export const approveRole = (id) => axiosClient.post(`/admin/roles/${id}/approve`);
export const mergeCompanies = (sourceId, targetId) =>
  axiosClient.post("/admin/companies/merge", { source_id: sourceId, target_id: targetId });
