import { Outlet } from "react-router-dom";
import BarraTopo from "./BarraTopo";
import RotaProtegida from "./RotaProtegida";

// Moldura das telas que exigem login: barra do topo + a tela atual.
export default function LayoutLogado() {
  return (
    <RotaProtegida>
      <BarraTopo />
      <main className="container py-5">
        <Outlet />
      </main>
    </RotaProtegida>
  );
}
