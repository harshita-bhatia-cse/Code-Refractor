import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ingestAuthFromHash } from "../lib/auth.js";

export function RequireAuth({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    ingestAuthFromHash();
    const token = sessionStorage.getItem("jwt_token") || "";
    console.log("Token:", token);
    if (!token) {
      navigate("/", { replace: true, state: { from: location.pathname } });
    }
  }, [navigate, location.pathname]);

  return children;
}

