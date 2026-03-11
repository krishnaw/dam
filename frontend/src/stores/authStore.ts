import { create } from "zustand";

interface AuthState {
  token: string | null;
  user: { id: string; email: string; role: string; fullName: string } | null;
  setAuth: (token: string, user: AuthState["user"]) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("dam_token"),
  user: null,
  setAuth: (token, user) => {
    localStorage.setItem("dam_token", token);
    set({ token, user });
  },
  logout: () => {
    localStorage.removeItem("dam_token");
    set({ token: null, user: null });
  },
}));
