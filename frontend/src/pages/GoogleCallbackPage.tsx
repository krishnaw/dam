import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useGoogleCallback } from "@/api/useAuth";

export function GoogleCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const callbackMutation = useGoogleCallback();
  const [error, setError] = useState("");
  const calledRef = useRef(false);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    const code = searchParams.get("code");
    if (!code) {
      navigate("/login", { replace: true });
      return;
    }

    callbackMutation.mutate(code, {
      onSuccess: () => {
        navigate("/", { replace: true });
      },
      onError: (err) => {
        setError(
          err instanceof Error ? err.message : "Google sign-in failed"
        );
        setTimeout(() => navigate("/login", { replace: true }), 3000);
      },
    });
  }, []);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Completing sign in...</p>
    </div>
  );
}
