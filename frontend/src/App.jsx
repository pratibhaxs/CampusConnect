import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { BookmarksProvider } from "./context/BookmarksContext";
import Sidebar from "./components/common/Sidebar";
import AppRoutes from "./routes/AppRoutes";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <BookmarksProvider>
          <div className="app-shell">
            <Sidebar />
            <main className="main-area">
              <AppRoutes />
            </main>
          </div>
        </BookmarksProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
