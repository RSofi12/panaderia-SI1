import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { SeccionReporteExistencias } from './components/SeccionReporteExistencias';

export default function ReporteExistenciasPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <Link
        to="/dashboard/reportes"
        className="inline-flex min-h-11 items-center gap-2 rounded-lg text-sm font-semibold text-amber-800 underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2"
      >
        <ArrowLeft aria-hidden="true" className="h-4 w-4" />
        Volver a Reportes
      </Link>
      <SeccionReporteExistencias />
    </div>
  );
}
