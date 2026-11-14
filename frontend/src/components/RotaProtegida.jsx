import { Navigate } from "react-router-dom";
import { estaLogado } from "../api";

// Envolve as telas que exigem login: sem token, manda para /entrar.
export default function RotaProtegida({ children }) {
  if (!estaLogado()) return <Navigate to="/entrar" replace />;
  return children;
}
