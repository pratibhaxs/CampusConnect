import axiosClient from "./axiosClient";

export const registerUser = (payload) => axiosClient.post("/auth/register", payload);
export const loginUser = (payload) => axiosClient.post("/auth/login", payload);
export const fetchCurrentUser = () => axiosClient.get("/auth/me");
export const deleteMyAccount = (password) => axiosClient.delete("/auth/me", { data: { password } });
