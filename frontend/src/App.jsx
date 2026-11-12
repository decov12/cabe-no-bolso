import { Route, Routes } from "react-router-dom";
import LayoutLogado from "./components/LayoutLogado";
import Inicio from "./pages/Inicio";
import Entrar from "./pages/Entrar";
import NovaSimulacao from "./pages/NovaSimulacao";
import Buscando from "./pages/Buscando";
import Resultado from "./pages/Resultado";
import Alternativas from "./pages/Alternativas";
import Historico from "./pages/Historico";

export default function App() {
  return (
    <Routes>
      {/* Telas públicas */}
      <Route path="/" element={<Inicio />} />
      <Route path="/entrar" element={<Entrar />} />

      {/* Telas que exigem login */}
      <Route element={<LayoutLogado />}>
        <Route path="/nova" element={<NovaSimulacao />} />
        <Route path="/buscando" element={<Buscando />} />
        <Route path="/resultado" element={<Resultado />} />
        <Route path="/alternativas" element={<Alternativas />} />
        <Route path="/historico" element={<Historico />} />
      </Route>
    </Routes>
  );
}
