import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import { useAuthStore } from "@/stores/authStore";
import type { User } from "@/types";

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  return useMutation({
    mutationFn: async (data: { email: string; password: string }) => {
      const res = await apiClient.post<{ access_token: string; user: User }>(
        "/auth/login",
        { email: data.email, password: data.password }
      );
      return res.data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, {
        id: data.user.id,
        email: data.user.email,
        role: data.user.role,
        fullName: data.user.full_name,
      });
    },
  });
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth);
  return useMutation({
    mutationFn: async (data: {
      email: string;
      password: string;
      full_name: string;
    }) => {
      const res = await apiClient.post<{ access_token: string; user: User }>(
        "/auth/register",
        data
      );
      return res.data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, {
        id: data.user.id,
        email: data.user.email,
        role: data.user.role,
        fullName: data.user.full_name,
      });
    },
  });
}

export function useCurrentUser() {
  const token = useAuthStore((s) => s.token);
  const setAuth = useAuthStore((s) => s.setAuth);
  return useQuery({
    queryKey: ["currentUser"],
    queryFn: async () => {
      const res = await apiClient.get<User>("/users/me");
      const user = res.data;
      if (token) {
        setAuth(token, {
          id: user.id,
          email: user.email,
          role: user.role,
          fullName: user.full_name,
        });
      }
      return user;
    },
    enabled: !!token,
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const queryClient = useQueryClient();
  return () => {
    logout();
    queryClient.clear();
  };
}

export function useGoogleLogin() {
  return useMutation({
    mutationFn: async () => {
      const res = await apiClient.get<{ url: string }>("/auth/google/login");
      return res.data;
    },
  });
}

export function useGoogleCallback() {
  const setAuth = useAuthStore((s) => s.setAuth);
  return useMutation({
    mutationFn: async (code: string) => {
      const res = await apiClient.post<{
        access_token: string;
        refresh_token: string;
      }>("/auth/google/callback", { code });
      return res.data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, null);
    },
  });
}
