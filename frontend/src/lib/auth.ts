import React, { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";

export function useAuth() {
  const router = useRouter();

  const isAuthenticated = useCallback(() => {
    if (typeof window !== "undefined") {
      return !!localStorage.getItem("auth_token");
    }
    return false;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("username");
    router.push("/login");
  }, [router]);

  const getToken = useCallback(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("auth_token");
    }
    return null;
  }, []);

  return {
    isAuthenticated: isAuthenticated(),
    logout,
    getToken,
  };
}

// Export guard for routes - check if user is authenticated before rendering
export function useRequireAuth() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("auth_token");
      if (!token) {
        router.push("/login");
      }
    }
    setIsLoading(false);
  }, [router]);

  return isLoading;
}

