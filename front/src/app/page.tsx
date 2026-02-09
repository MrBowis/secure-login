import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-gray-50 to-gray-100 p-4">
      <div className="w-full max-w-5xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900">
            Sistema de Autenticación Segura
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Plataforma de autenticación con verificación en dos pasos usando Microsoft Authenticator.
            Elige tu tipo de cuenta para comenzar.
          </p>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-1 gap-6 mt-12">
          {/* User Card */}
          <Card className="shadow-xl hover:shadow-2xl transition-shadow border-2 hover:border-blue-300">
            <CardHeader className="bg-linear-to-br from-blue-50 to-indigo-50 rounded-t-lg">
              <CardTitle className="text-2xl text-blue-900">Login Seguro</CardTitle>
              <CardDescription className="text-base">
                Acceso para usuarios del sistema
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900">Características:</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start">
                    <span className="text-blue-500 mr-2">✓</span>
                    <span>Acceso seguro con 2FA obligatorio</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-500 mr-2">✓</span>
                    <span>Panel de usuario personalizado</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-500 mr-2">✓</span>
                    <span>Protección avanzada de datos</span>
                  </li>
                </ul>
              </div>

              <div className="space-y-3">
                <Link href="/auth/login" className="block">
                  <Button className="w-full bg-blue-600 hover:bg-blue-700" size="lg">
                    Iniciar Sesión
                  </Button>
                </Link>
                <Link href="/auth/register" className="block">
                  <Button variant="outline" className="w-full" size="lg">
                    Crear Cuenta
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Security Info */}
        <Card className="mt-8 shadow-lg">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <div className="shrink-0">
                <svg className="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Máxima Seguridad</h3>
                <p className="text-sm text-gray-600">
                  Este sistema implementa autenticación de dos factores (2FA) obligatoria usando Microsoft Authenticator.
                  Todos los datos están protegidos con cifrado de extremo a extremo y las sesiones son monitoreadas
                  constantemente para garantizar tu seguridad.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

