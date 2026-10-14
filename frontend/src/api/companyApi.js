import axiosClient from "./axiosClient";

export const fetchCompanies = (search = "") =>
  axiosClient.get("/companies", { params: search ? { q: search } : {} });

export const fetchCompanyDetail = (id) => axiosClient.get(`/companies/${id}`);

export const createCompany = (payload) => axiosClient.post("/companies", payload);
export const updateCompany = (id, payload) => axiosClient.put(`/companies/${id}`, payload);
export const deleteCompany = (id) => axiosClient.delete(`/companies/${id}`);

export const addRole = (companyId, title) =>
  axiosClient.post(`/companies/${companyId}/roles`, { title });
export const deleteRole = (roleId) => axiosClient.delete(`/companies/roles/${roleId}`);

export const submitCompany = (name, confirmNew = false) =>
  axiosClient.post("/companies/submit", { name, confirm_new: confirmNew });
export const submitRole = (companyId, title, confirmNew = false) =>
  axiosClient.post(`/companies/${companyId}/roles/submit`, { title, confirm_new: confirmNew });
